from livekit import rtc, agents, api
from livekit.api import AccessToken, VideoGrants
from livekit.plugins import openai
from livekit.agents import AgentSession, Agent
from flask import Flask, render_template, jsonify, request
from pydub import AudioSegment
from app import Assistant
import numpy as np
import httpx
from livekit.api import AccessToken, VideoGrants
import io


class SessionManager:
  """Manages voice agent sessions with proper room management"""
  def __init__(self):
      self.room = None
      self.assistant = None
      self.active = False
      self.room_name = "phonics-room"
      self.current_token = None
      self.event_loop = None
      self.session_task = None
      self.recent_messages = []  # Store recent agent messages for UI display

  def _create_room_token(self, identity: str) -> str:
      """Create a token for joining the LiveKit room using the new API"""
      try:
          token = (
              AccessToken(
                  api_key=os.environ["LIVEKIT_API_KEY"],
                  api_secret=os.environ["LIVEKIT_API_SECRET"]
              )
              .with_identity(identity)
              .with_grants(
                  VideoGrants(
                      room_join=True,
                      room=self.room_name,
                      can_publish=True,
                      can_subscribe=True,
                      can_publish_data=True
                  )
              )
          )
          return token.to_jwt()
      except Exception as e:
          print(f"Error creating room token: {str(e)}")
          raise

  async def _setup_llm(self):
      """Set up the LLM component"""
      try:
          # Set up Azure OpenAI LLM
          self.llm_model = openai.LLM.with_azure(
              azure_deployment=os.environ.get("AZURE_DEPLOYMENT"),
              azure_endpoint=os.environ.get("AZURE_OPENAI_ENDPOINT"),
              api_key=os.environ.get("AZURE_OPENAI_API_KEY"),
              temperature=0.7,
          )

          print("LLM set up successfully")

      except Exception as e:
          print(f"Error setting up LLM: {str(e)}")
          # Continue without LLM for basic functionality
          self.llm_model = None

  async def _setup_audio_track(self):
      """Set up the audio source and track for publishing"""
      try:
          self.audio_source = rtc.AudioSource(sample_rate=16000, num_channels=1)
          self.audio_track = rtc.LocalAudioTrack.create_audio_track("agent_voice", self.audio_source)
          await self.room.local_participant.publish_track(self.audio_track)
          print("Audio track set up and published successfully")
      except Exception as e:
          print(f"Error setting up audio track: {str(e)}")
          raise

  async def _text_to_speech_azure(self, text: str) -> bytes:
      """Convert text to speech using Azure Cognitive Services (fallback)"""
      try:
          # This is a placeholder - you'd need to implement Azure Speech SDK
          print("Azure TTS not implemented yet, using console output")
          return None
      except Exception as e:
          print(f"Error with Azure TTS: {str(e)}")
          return None

  async def _text_to_speech_elevenlabs(self, text: str) -> bytes:
      """Convert text to speech using ElevenLabs API (returns PCM)"""
      try:
          api_key = os.environ.get("ELEVEN_API_KEY")
          if not api_key:
              print("ElevenLabs API key not found, skipping...")
              return None

          voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
          url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}/stream"

          headers = {
              "Accept": "audio/wav",   # 👈 ask for WAV instead of MP3
              "Content-Type": "application/json",
              "xi-api-key": api_key
          }

          data = {
              "text": text,
              "model_id": "eleven_monolingual_v1",
              "voice_settings": {
                  "stability": 0.5,
                  "similarity_boost": 0.5
              }
          }

          async with httpx.AsyncClient() as client:
              response = await client.post(url, json=data, headers=headers)

              if response.status_code == 200:
                  return response.content  # WAV bytes
              else:
                  print(f"ElevenLabs API error: {response.status_code} - {response.text}")
                  return None

      except Exception as e:
          print(f"Error with ElevenLabs TTS: {str(e)}")
          return None


  async def _publish_audio_data(self, audio_data: bytes):
      """Publish audio data (MP3 or WAV) to the room"""
      try:
          if not self.audio_source or not audio_data:
              print("Audio source or audio data is missing")
              return

          # Decode audio (MP3 or WAV) to PCM16 to be able to sent it to the back end
          audio = AudioSegment.from_file(io.BytesIO(audio_data), format="mp3")
          audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)

          raw_pcm = audio.raw_data
          audio_array = np.frombuffer(raw_pcm, dtype=np.int16).astype(np.float32) / 32768.0

          frame = rtc.AudioFrame(
              data=audio_array.tobytes(),
              sample_rate=16000,
              num_channels=1,
              samples_per_channel=len(audio_array),
          )

          await self.audio_source.capture_frame(frame)
          print(f"✅ Published {len(audio_array)} samples at 16kHz")

      except Exception as e:
          print(f"Error publishing audio data: {str(e)}")

  # this is for testing i did it  because i excededd the quto of my transscription model 
  async def _say_text(self, text: str):
      """Convert text to speech and publish it"""
      print(f" Agent saying: {text}")

      self.recent_messages.append({
          'text': text,
          'timestamp': datetime.now().isoformat()
      })
      # Keep only last 10 messages
      if len(self.recent_messages) > 10:
          self.recent_messages = self.recent_messages[-10:]

      audio_data = None

      # Try ElevenLabs first
      if os.environ.get("ELEVEN_API_KEY"):
          audio_data = await self._text_to_speech_elevenlabs(text)

      # Fallback to Azure if ElevenLabs fails
      if not audio_data and os.environ.get("AZURE_SPEECH_KEY"):
          print("Attempting Azure TTS...")
          audio_data = await self._text_to_speech_azure(text)

      if audio_data:
          print("✅ Audio generated and will be played")
          await self._publish_audio_data(audio_data)
      else:
          print("⚠️ No cloud TTS available - message stored for display in UI")


  async def _send_greeting(self, child_name: str):
      """Send initial greeting"""
      greeting = f"Hello {child_name}! I'm Youssef, your phonics tutor. Are you ready to practice some letters today?"
      await self._say_text(greeting)

  async def start_session(self, child_data):
      """Start a voice tutoring session with proper room connection"""
      try:
          print(f"Starting voice session for: {child_data['name']}")
          identity = f"tutor-{random.randint(1000, 9999)}"
          self.participant_identity = identity
          # Initialize the Assistant
          self.assistant = Assistant(child_data)
          self.current_token = self._create_room_token(identity)
          self.room = rtc.Room()

          # Set up event handlers
          self._setup_room_handlers()
          await self.room.connect(
              url=os.environ.get("LIVEKIT_URL", "ws://localhost:7880"),
              token=self.current_token
          )

          print(f"Connected to room: {self.room_name}")

          await self._setup_audio_track()
          await self._setup_llm()
          self.active = True
          await asyncio.sleep(1)
          await self._send_greeting(child_data['name'])

          print(f"Voice session started successfully for {child_data['name']}")
          return True

      except Exception as e:
          print(f"Error starting session: {str(e)}")
          import traceback
          traceback.print_exc()
          self.active = False
          return False

  def _setup_room_handlers(self):
      """Set up room event handlers"""
      @self.room.on("participant_connected")
      def on_participant_connected(participant: rtc.RemoteParticipant):
          print(f"Participant connected: {participant.identity}")

      @self.room.on("participant_disconnected")
      def on_participant_disconnected(participant: rtc.RemoteParticipant):
          print(f"Participant disconnected: {participant.identity}")

      @self.room.on("track_published")
      def on_track_published(publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
          print(f"Track published: {publication.sid} by {participant.identity}")

          if publication.kind == rtc.TrackKind.KIND_AUDIO:

              
              print("Student audio track detected")
              asyncio.create_task(self._handle_student_audio(publication))

      @self.room.on("track_subscribed")
      def on_track_subscribed(track: rtc.Track, publication: rtc.RemoteTrackPublication, participant: rtc.RemoteParticipant):
          print(f"Track subscribed: {publication.sid}")

  async def _handle_student_audio(self, publication: rtc.RemoteTrackPublication):
      """Handle incoming student audio"""
      try:
          print("Student started speaking - simulating speech recognition...")

          # Simulate speech recognition with different responses
          simulated_responses = [
              "Hello",
              "A", 
              "B",
              "What's that?",
              "Can you help me?",
              "I want to learn"
          ]

          # Wait a bit to simulate processing
          await asyncio.sleep(2)

          # Pick a random response to simulate speech recognition
          import random
          detected_text = random.choice(simulated_responses)
          print(f"Simulated detected speech: '{detected_text}'")

          if self.assistant:
              # Process through assistant
              await self.assistant.on_message(detected_text)

              # Generate a contextual response
              if detected_text.upper() in ['A', 'B', 'C', 'D', 'E']:
                  response = f"Excellent! You said the letter {detected_text.upper()}! That letter makes the sound /{detected_text.lower()}/. Can you say the sound /{detected_text.lower()}/ with me?"
              elif "hello" in detected_text.lower():
                  response = "Hello there! I'm so happy to hear your voice! Should we practice some letters together? Let's start with the letter A!"
              elif "help" in detected_text.lower():
                  response = "Of course I can help! Let's practice letters and sounds. Can you say the letter A for me?"
              elif "learn" in detected_text.lower():
                  response = "Wonderful! I love helping children learn! Let's practice the alphabet. Can you say the letter B?"
              else:
                  response = "I heard you! That's great speaking! Let's practice a letter. Can you say the letter A?"

              await self._say_text(response)

      except Exception as e:
          print(f"Error handling student audio: {str(e)}")

  async def stop_session(self):
      """Stop the current session"""
      try:
          if self.session_task and not self.session_task.done():
              self.session_task.cancel()

          if self.room:
              await self.room.disconnect()
              print("Disconnected from room")

          self.room = None
          self.assistant = None
          self.active = False
          self.current_token = None
          self.participant_identity = None
          self.llm_model = None
          self.audio_source = None
          self.audio_track = None
          self.session_task = None

          print("Session stopped successfully")
          return True

      except Exception as e:
          print(f"Error stopping session: {str(e)}")
          return False
  def get_status(self):
      """Get current session status"""
      return {
          'active': self.active,
          'room_name': self.room_name if self.active else None,
          'memory_status': self.assistant.get_memory_status() if self.assistant else None
      }


app = Flask(__name__)
session_manager = SessionManager()
SAMPLE_CHILD_DATA = {
  'name': 'Emma',
  'age': 6,
  'level': 'beginner'
}

# Add these imports at the top with other imports


def run_async(coro):
  """Helper to run async functions in Flask"""
  try:
      # Get or create the event loop for the session manager
      if hasattr(session_manager, 'event_loop') and session_manager.event_loop and not session_manager.event_loop.is_closed():
          loop = session_manager.event_loop
      else:
          loop = asyncio.new_event_loop()
          session_manager.event_loop = loop
          asyncio.set_event_loop(loop)

      return loop.run_until_complete(coro)
  except Exception as e:
      print(f"Error in run_async: {str(e)}")
      return None

# Fixed token creation function - add this before the Flask routes
def create_room_token(identity: str, room_name: str) -> str:
  """Create a token for joining the LiveKit room using the new API"""
  token = (
      AccessToken(
          api_key=os.environ["LIVEKIT_API_KEY"],
          api_secret=os.environ["LIVEKIT_API_SECRET"]
      )
      .with_identity(identity)
      .with_name(identity)
      .with_grants(
          VideoGrants(
              room_join=True,
              room=room_name,
              can_publish=True,
              can_subscribe=True,
              can_publish_data=True
          )
      )
  )
  return token.to_jwt()

@app.route('/')
def index():
  """Main page with control buttons"""
  return render_template('index.html', 
                         session_active=session_manager.active,
                         child_name=SAMPLE_CHILD_DATA['name'])

@app.route('/start_session', methods=['POST'])
def start_session():
  """Start the voice tutoring session"""
  try:
      success = run_async(session_manager.start_session(SAMPLE_CHILD_DATA))
      if success:
          return jsonify({'status': 'success', 'message': f'Session started for {SAMPLE_CHILD_DATA["name"]}'})
      else:
          return jsonify({'status': 'error', 'message': 'Failed to start session'}), 500
  except Exception as e:
      print(f"Error in start_session route: {str(e)}")
      return jsonify({'status': 'error', 'message': f'Error starting session: {str(e)}'}), 500

@app.route('/stop_session', methods=['POST'])
def stop_session():
  """Stop the voice tutoring session"""
  try:
      success = run_async(session_manager.stop_session())
      if success:
          return jsonify({'status': 'success', 'message': 'Session stopped successfully'})
      else:
          return jsonify({'status': 'error', 'message': 'Failed to stop session'}), 500
  except Exception as e:
      print(f"Error in stop_session route: {str(e)}")
      return jsonify({'status': 'error', 'message': f'Error stopping session: {str(e)}'}), 500

@app.route('/status')
def status():
  """Get current session status"""
  return jsonify({
      'active': session_manager.active, 
      'room_name': session_manager.room_name,
      'recent_messages': session_manager.recent_messages[-5:] if session_manager.recent_messages else []
  })

@app.route('/messages')
def get_messages():
  """Get recent agent messages"""
  return jsonify({
      'messages': session_manager.recent_messages[-10:] if session_manager.recent_messages else []
  })

if __name__ == '__main__':
  print("Starting LiveKit Session Control Server...")
  app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)