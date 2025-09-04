import os
import random
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv
from prompt import PROMPT
from livekit import agents
from livekit.agents import AgentSession, Agent
from livekit.plugins.turn_detector import EOUPlugin
from livekit.plugins import openai
from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import asyncio
import threading
import logging
from typing import Optional


load_dotenv()
plugin = EOUPlugin()
plugin.download_files()

class MemoryManager:
    """Manages short-term memory for the last 3 user/assistant exchanges"""
    
    def __init__(self, max_exchanges=3):
        self.max_exchanges = max_exchanges
        self.exchanges: List[Dict[str, Any]] = []
        self.derived_settings = {
            'child_name': '',
            'focus_letter': '',
            'difficulty': 'easy',
            'phonics_progress': []
        }
    
    def add_exchange(self, user_input: str, assistant_response: str = ""):
        """Add a new user/assistant exchange"""
        exchange = {
            'timestamp': datetime.now().isoformat(),
            'user': user_input.strip(),
            'assistant': assistant_response.strip()
        }
        
        self.exchanges.append(exchange)
        
        # Keep only the last N exchanges
        if len(self.exchanges) > self.max_exchanges:
            self.exchanges = self.exchanges[-self.max_exchanges:]
        
        # Update derived settings based on conversation
        self._update_derived_settings()
    
    def _update_derived_settings(self):
        """Extract personalized settings from conversation history"""
        recent_text = " ".join([
            f"{ex['user']} {ex['assistant']}" for ex in self.exchanges[-3:]
        ]).lower()
        
        # Extract child's name (simple pattern matching)
        import re
        name_patterns = [
            r"my name is (\w+)",
            r"i am (\w+)",
            r"i'm (\w+)",
            r"call me (\w+)"
        ]
        
        for pattern in name_patterns:
            match = re.search(pattern, recent_text)
            if match:
                self.derived_settings['child_name'] = match.group(1).title()
                break
        
        # Detect focus letter
        letter_mentions = re.findall(r'\bletter ([a-z])\b', recent_text)
        if letter_mentions:
            self.derived_settings['focus_letter'] = letter_mentions[-1].upper()
        
        # Assess difficulty based on responses
        if any(word in recent_text for word in ['hard', 'difficult', 'tough']):
            self.derived_settings['difficulty'] = 'easy'
        elif any(word in recent_text for word in ['easy', 'simple', 'more']):
            self.derived_settings['difficulty'] = 'medium'
    
    def get_context_prompt(self) -> str:
        """Generate context prompt based on memory"""
        if not self.exchanges:
            return ""
        
        context = "\n=== RECENT CONVERSATION MEMORY ===\n"
        for i, exchange in enumerate(self.exchanges[-3:], 1):
            context += f"Exchange {i}:\n"
            context += f"Child: {exchange['user']}\n"
            if exchange['assistant']:
                context += f"You: {exchange['assistant']}\n"
            context += "\n"
        
        # Add derived settings
        settings = self.derived_settings
        context += "=== PERSONALIZATION SETTINGS ===\n"
        if settings['child_name']:
            context += f"Child's name: {settings['child_name']}\n"
        if settings['focus_letter']:
            context += f"Current focus letter: {settings['focus_letter']}\n"
        context += f"Difficulty level: {settings['difficulty']}\n"
        context += "====================================\n\n"
        
        return context

class PhonicsHelper:
    """Helper class for phonics-focused feedback and assessment"""
    
    LETTER_SOUNDS = {
        'A': ['ay', 'ah', 'aa'], 
        'B': ['buh'], 
        'C': ['kuh', 'suh', 'ch'], 
        'D': ['duh'], 
        'E': ['ee', 'eh', 'uh'], 
        'F': ['fuh'], 
        'G': ['guh', 'juh'], 
        'H': ['huh'], 
        'I': ['eye', 'ih'], 
        'J': ['juh'], 
        'K': ['kuh'], 
        'L': ['luh'], 
        'M': ['muh'], 
        'N': ['nuh'], 
        'O': ['oh', 'aw', 'ah'], 
        'P': ['puh'], 
        'Q': ['kwuh'], 
        'R': ['ruh'], 
        'S': ['suh', 'zuh'], 
        'T': ['tuh'], 
        'U': ['yoo', 'uh', 'oo'], 
        'V': ['vuh'], 
        'W': ['wuh'], 
        'X': ['ks', 'zuh'], 
        'Y': ['yuh', 'eye', 'ee'], 
        'Z': ['zuh', 'zee']
    }

    PHONICS_WORDS = {
        'A': ['apple', 'ant', 'alligator', 'airplane', 'ax', 'arrow'],
        'B': ['ball', 'bat', 'banana', 'bear', 'bird', 'book'],
        'C': ['cat', 'car', 'cake', 'cup', 'cow', 'corn'],
        'D': ['dog', 'duck', 'door', 'doll', 'drum', 'desk'],
        'E': ['elephant', 'egg', 'envelope', 'engine', 'ear', 'elf'],
        'F': ['fish', 'frog', 'fan', 'fox', 'feather', 'flag'],
        'G': ['goat', 'grape', 'gift', 'girl', 'game', 'guitar'],
        'H': ['hat', 'house', 'horse', 'hand', 'hammer', 'hen'],
        'I': ['igloo', 'insect', 'ink', 'ice', 'iron', 'iguanodon'],
        'J': ['jam', 'jelly', 'jug', 'juice', 'jeep', 'jacket'],
        'K': ['kite', 'kangaroo', 'king', 'key', 'kitten', 'kettle'],
        'L': ['lion', 'leaf', 'lamp', 'ladder', 'log', 'lemon'],
        'M': ['monkey', 'moon', 'milk', 'map', 'mouse', 'muffin'],
        'N': ['nest', 'net', 'nurse', 'nose', 'nail', 'nut'],
        'O': ['octopus', 'orange', 'ostrich', 'owl', 'ox', 'ocean'],
        'P': ['pig', 'pen', 'pan', 'pot', 'pizza', 'pumpkin'],
        'Q': ['queen', 'quilt', 'quail', 'question', 'quarter', 'quack'],
        'R': ['rabbit', 'rain', 'ring', 'robot', 'rocket', 'rose'],
        'S': ['sun', 'sock', 'sand', 'snake', 'star', 'spoon'],
        'T': ['tiger', 'tree', 'toy', 'table', 'train', 'tent'],
        'U': ['umbrella', 'uncle', 'under', 'uniform', 'unicorn', 'up'],
        'V': ['van', 'vase', 'vest', 'violin', 'vulture', 'village'],
        'W': ['whale', 'watch', 'wagon', 'wolf', 'window', 'watermelon'],
        'X': ['xylophone', 'x-ray', 'xenops', 'xenon'],  # tricky letter
        'Y': ['yarn', 'yak', 'yacht', 'yellow', 'yo-yo', 'yard'],
        'Z': ['zebra', 'zip', 'zoo', 'zero', 'zigzag', 'zucchini']
    }

    
    @classmethod
    def get_letter_feedback(cls, letter: str, user_pronunciation: str) -> str:
        """Provide feedback on letter pronunciation"""
        letter = letter.upper()
        user_pronunciation = user_pronunciation.lower().strip()
        if letter in cls.LETTER_SOUNDS:
            correct_sounds = cls.LETTER_SOUNDS[letter]
            # Simple pronunciation check
            is_correct = any(sound in user_pronunciation for sound in correct_sounds)

            if is_correct:
                return f"Great job! You said the letter {letter} perfectly!"
            else:
                primary_sound = correct_sounds[0]
                return f"Good try! The letter {letter} makes the sound '{primary_sound}'. Can you try again?"
        
        return f"Let's practice the letter {letter} together!"
    
    @classmethod
    def get_phonics_activity(cls, letter: str, difficulty: str = 'easy') -> str:
        """Generate phonics activity based on letter and difficulty"""
        letter = letter.upper()
        
        if difficulty == 'easy':
            return f"Let's practice the letter {letter}! Can you say the letter name first? Then we'll practice its sound!"
        elif difficulty == 'medium':
            words = cls.PHONICS_WORDS.get(letter, [f"{letter.lower()}word"])
            word = random.choice(words[:2])
            return f"Great! Now let's try a word that starts with {letter}. Can you say '{word}'?"
        else:  # hard
            words = cls.PHONICS_WORDS.get(letter, [])
            if len(words) >= 2:
                word1, word2 = random.sample(words, 2)
                return f"Excellent! Can you tell me which word starts with {letter}: '{word1}' or 'zebra'?"
        
        return f"Let's work on the letter {letter}!"

class Assistant(Agent):
    def __init__(self, child: Dict[str, Any]):
        self.child_name = child.get('name', 'friend')
        self.memory = MemoryManager()
        self.phonics_helper = PhonicsHelper()
        self.current_activity = None
        self.awaiting_pronunciation = False
        
        # Enhanced phonics-focused prompt
        intro = f"""
You are Youssef, a friendly and encouraging phonics tutor for young children. 
You're working with {self.child_name} today to help them learn letters, sounds, and words.

PHONICS TEACHING GUIDELINES:
1. Always emphasize both letter NAMES and letter SOUNDS
2. Provide gentle pronunciation feedback and correction
3. Use simple, age-appropriate language
4. Be encouraging and celebrate small wins
5. Ask the child to repeat sounds and words
6. Connect letters to familiar words and objects
7. Adapt difficulty based on the child's responses

INTERACTION STYLE:
- Speak warmly and enthusiastically
- Use the child's name when you know it
- Give specific praise for good attempts
- Offer gentle corrections with encouragement
- Keep sessions engaging with variety

Remember: You have access to recent conversation memory to personalize your teaching.
"""
        
        full_prompt = intro + "\n\n" + PROMPT
        super().__init__(instructions=full_prompt)

    def _generate_personalized_prompt(self) -> str:
        """Generate a personalized prompt with memory context"""
        base_prompt = self.instructions
        memory_context = self.memory.get_context_prompt()

        if self.current_activity:
            activity_context = f"\nCURRENT ACTIVITY: {self.current_activity}\n"
            return base_prompt + memory_context + activity_context
        return base_prompt + memory_context

    async def _analyze_phonics_response(self, user_input: str) -> Optional[str]:
        """Analyze user input for phonics-specific feedback"""
        user_input_lower = user_input.lower().strip()
        import re
        single_letter = re.match(r'^([a-z])$', user_input_lower)
        if single_letter:
            letter = single_letter.group(1)
            return self.phonics_helper.get_letter_feedback(letter, user_input_lower)
        
        # Pattern for letter sounds (phonetic attempts)
        sound_patterns = [
            (r'([a-z])uh', 'consonant_sound'),
            (r'([aeiou])([aeiou])?', 'vowel_sound')
        ]
        
        for pattern, sound_type in sound_patterns:
            match = re.search(pattern, user_input_lower)
            if match and self.awaiting_pronunciation:
                letter = match.group(1).upper()
                return self.phonics_helper.get_letter_feedback(letter, user_input_lower)
        
        return None

    async def on_message(self, message: str):
        """Enhanced message handling with phonics focus and memory"""
        print(f"Processing message: '{message}'")
        
        try:
            # Check for phonics-specific responses first
            phonics_feedback = await self._analyze_phonics_response(message)
            
            if phonics_feedback:
                print(f"Providing phonics feedback: {phonics_feedback}")
                # Add to memory and continue with normal flow
                self.memory.add_exchange(message, phonics_feedback)
                return phonics_feedback
            
            # Update memory with the user input (response will be added later)
            self.memory.add_exchange(message, "")
            
            # Generate activity suggestions based on memory
            settings = self.memory.derived_settings
            if settings['focus_letter'] and not self.current_activity:
                self.current_activity = self.phonics_helper.get_phonics_activity(
                    settings['focus_letter'], 
                    settings['difficulty']
                )
            
            print(f"Current memory context: {settings}")
            
        except Exception as e:
            print(f"Error in message processing: {e}")

    async def on_user_speech(self, user_speech, participant):
        """Handle speech recognition with phonics analysis"""
        try:
            text = user_speech.text.strip()
            print(f"User speech detected: '{text}'")
            
            # Process through the enhanced message handler
            await self.on_message(text)
            
        except Exception as e:
            print(f"Error in on_user_speech: {e}")
            await super().on_user_speech(user_speech, participant)

    def get_memory_status(self) -> Dict[str, Any]:
        """Get current memory status for UI display"""
        return {
            'exchanges': self.memory.exchanges[-3:],  # Last 3 exchanges
            'settings': self.memory.derived_settings,
            'current_activity': self.current_activity,
            'total_exchanges': len(self.memory.exchanges)
        }

async def run_session(child):
    print(f"Running phonics session for: {child['name']}")
    assistant = Assistant(child)
    session = AgentSession(
        llm=openai.realtime.RealtimeModel.with_azure(
            azure_deployment=os.environ["AZURE_DEPLOYMENT"],
            azure_endpoint=os.environ["AZURE_OPENAI_ENDPOINT"],
            api_key=os.environ["AZURE_OPENAI_API_KEY"],
            temperature="0.7",
            voice="ash"
        )
    )

    session.agent = assistant
    await session.start(
        agent=assistant,
    )

    memory_status = assistant.get_memory_status()
    print(f"Session memory status: {json.dumps(memory_status, indent=2)}")
    await session.generate_reply()
########## this part is for local testing and running agent in the terminal you can un coment it to test ###########
# async def entrypoint(ctx: agents.JobContext):
#     await ctx.connect()
#     child = {'name': 'Student'}  # Default or get from context
#     await run_session(child)

# if __name__ == '__main__':
#         agents.cli.run_app(agents.WorkerOptions(entrypoint_fnc=entrypoint))



