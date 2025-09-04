#KidSafe Alphabet Tutor 

A kid-friendly, speech-first learning agent that helps children learn the English alphabet (A–Z) through an interactive voice interface.
This project is designed as part of an AI Engineer assessment, focusing on speech, phonics, and conversational AI with a fun and safe learning experience.

🚀 Features

-Speech-first interaction: Teaches letters and sounds in a conversational style.
-Phonics support: Reinforces learning with multiple sound associations.
-Web & terminal modes: Run as a browser app or directly from the terminal.
-Response simulator: When transcription API quota is exceeded, a fallback simulator ensures the tutor still responds for testing.
-Integration-ready: Uses LiveKit (real-time voice & video), OpenAI, and ElevenLabs for speech & interaction.

-- Project Structure
AI-Engineer-Assessment-KidSafe-Alphabet-Tutor/
│── routes.py      # Entry point for terminal testing (with simulator mode)
│── backend/           # flask backend
│── index.html/        # Simple React UI
│── agent.py/          # Tutor logic & phonics rules
│── requirements.txt    # Python dependencies
│── README.md           # Documentation (this file)

--Running the Project
1. Clone the Repository
git clone https://github.com/youssefsalah224/AI-Engineer-Assessment-KidSafe-Alphabet-Tutor.git
cd AI-Engineer-Assessment-KidSafe-Alphabet-Tutor

2. Install Dependencies
pip install -r requirements.txt

3. Set Environment Variables

Create a .env file in the project root:

# LiveKit credentials
LIVEKIT_URL=your_livekit_url
LIVEKIT_API_KEY=your_api_key
LIVEKIT_API_SECRET=your_api_secret

# ElevenLabs API key
ELEVENLABS_API_KEY=your_api_key

# OpenAI API key
OPENAI_API_KEY=your_api_key

🎤 Running the Tutor
Web App (with flask + LiveKit)
uvicorn server.main:app --reload


Then open your browser at:
👉 http://localhost:8000

Terminal Testing (Simulator Mode)

If your transcription quota is exceeded, you can still test logic locally:

python app.py


This runs a command-line tutor that simulates transcription responses, ensuring the learning flow can be evaluated without external API calls.

📌 Notes

The LiveKit SDK handles real-time voice/video streaming.

ElevenLabs is used for high-quality TTS (Text-to-Speech).

A simulated response fallback ensures the project is testable even if external API limits are reached.

This project prioritizes clarity, readability, and educational value for assessment purposes.

👨‍💻 Author

Youssef Salah
AI Developer • Trader • Founder of Monk Clothing
📍 Egypt
