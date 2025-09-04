# 🎓 KidSafe Alphabet Tutor

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-18+-blue.svg)](https://reactjs.org/)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An innovative AI-powered speech-first learning agent designed to teach children the English alphabet through interactive voice conversations. Built as part of an AI Engineer assessment, this project demonstrates expertise in conversational AI, speech processing, and child-safe educational technology.

## 🌟 Key Features

- **🎙️ Speech-First Learning**: Natural voice interactions for immersive alphabet learning
- **🔤 Phonics Integration**: Advanced phonetic support with multiple sound associations
- **👶 Kid-Safe Design**: Child-friendly interface and content filtering
- **🌐 Dual Mode Operation**: Web application and terminal-based testing
- **🔄 Fallback System**: Intelligent response simulator for API quota management
- **⚡ Real-Time Processing**: LiveKit integration for seamless voice/video streaming
- **🎯 Educational Focus**: Structured learning progression through A-Z

## 🏗️ Architecture

```
AI-Engineer-Assessment-KidSafe-Alphabet-Tutor/
├── agent.py                    # Standalone terminal agent for testing
├── server.py                   # Web application entry point
├── backend/                    # FastAPI backend services
├── frontend/                   # React.js user interface
├── llm_agent/                  # Core tutor logic & phonics engine
├── requirements.txt            # Python dependencies
├── .env.example               # Environment configuration template
└── README.md                  # Project documentation
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- Node.js 16+ (for frontend development)
- API keys for required services (see [API Requirements](#-api-requirements))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/youssefsalah224/AI-Engineer-Assessment-KidSafe-Alphabet-Tutor.git
   cd AI-Engineer-Assessment-KidSafe-Alphabet-Tutor
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys (see API Requirements section)
   ```

## 🔑 API Requirements

This project requires the following API services:

### Required APIs
- **OpenAI API** - For conversational AI and natural language processing
- **ElevenLabs API** - For high-quality text-to-speech synthesis
- **LiveKit** - For real-time voice and video streaming

### Environment Configuration

Create a `.env` file in the project root with the following variables:

```env
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# ElevenLabs Configuration  
ELEVENLABS_API_KEY=your_elevenlabs_api_key_here

# LiveKit Configuration
LIVEKIT_URL=your_livekit_server_url
LIVEKIT_API_KEY=your_livekit_api_key
LIVEKIT_API_SECRET=your_livekit_api_secret
```

### API Key Setup Guide

1. **OpenAI API**: Visit [OpenAI Platform](https://platform.openai.com/api-keys) to generate your API key
2. **ElevenLabs API**: Sign up at [ElevenLabs](https://elevenlabs.io/) and obtain your API key
3. **LiveKit**: Create an account at [LiveKit Cloud](https://livekit.io/) for real-time communication services

## 🎮 Usage

### Web Application Mode

Start the full web application with voice interface:

```bash
uvicorn server:app --reload
```

Navigate to `http://localhost:8000` in your browser to access the interactive learning interface.

### Terminal Testing Mode

For development and testing purposes, especially when transcription API quotas are exceeded:

```bash
python agent.py
```

**Features of Terminal Mode:**
- ✅ Standalone operation without web interface
- ✅ Simulated speech input for testing learning logic
- ✅ Complete alphabet tutoring functionality
- ✅ No external API dependency for basic testing
- ✅ Ideal for development and assessment review

This mode allows evaluators and developers to test the core educational logic even when API limits are reached.

## 🧪 Testing

The project includes comprehensive testing capabilities:

- **Unit Tests**: Core tutoring logic validation
- **Integration Tests**: API service connectivity
- **Simulator Mode**: Fallback testing without external dependencies

Run tests with:
```bash
python -m pytest tests/
```

## 🛠️ Technical Stack

- **Backend**: FastAPI, Python 3.8+
- **Frontend**: React.js, HTML5, CSS3
- **AI/ML**: OpenAI GPT models, custom phonics engine
- **Speech**: ElevenLabs TTS, LiveKit real-time audio
- **Deployment**: Uvicorn ASGI server

## 📋 Assessment Context

This project was developed as part of an AI Engineer role assessment, demonstrating:

- ✅ **Conversational AI Development**
- ✅ **Speech Processing Integration** 
- ✅ **Child-Safe Content Design**
- ✅ **API Integration & Management**
- ✅ **Fallback System Implementation**
- ✅ **Full-Stack Development Skills**
- ✅ **Educational Technology Expertise**

## 🔧 Development Notes

- The terminal agent (`agent.py`) serves as a quota-independent testing environment
- Response simulation ensures consistent functionality during API limitations
- Modular architecture supports easy extension and maintenance
- Child safety measures are integrated throughout the application

## 📞 Support

For questions about this assessment project or technical implementation details, please contact:

**Youssef Salah**  
AI Developer | Full-Stack Engineer  
📧 [Contact Information]  
🌍 Cairo, Egypt

---

*This project demonstrates practical AI application development with focus on educational technology, speech processing, and child-safe interaction design.*
