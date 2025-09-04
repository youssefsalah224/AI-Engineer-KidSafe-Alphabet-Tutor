KidSafe Alphabet Tutor 🧸✨

A kid-friendly, speech-first learning agent that helps children learn the English alphabet (A–Z) through an interactive voice interface.
This project is designed as part of an AI Engineer assessment, focusing on speech, phonics, and conversational AI with a fun and safe learning experience.

🚀 Features

🎙️ Speech-first interaction: Teaches letters and sounds in a conversational style.

🧩 Phonics support: Reinforces learning with multiple sound associations.

🎨 Simple UI: Minimal, kid-safe front end for engagement.

🔧 Flexible testing: Run as a web app or directly from the terminal.

🗂️ Project Structure
AI-Engineer-Assessment-KidSafe-Alphabet-Tutor/
│── app.py              # Entry point for terminal testing
│── frontend/           # Simple React UI
│── backend/            # FastAPI backend
│── llm_agent/          # Logic for the learning agent
│── requirements.txt    # Python dependencies
│── README.md           # Documentation (this file)

🖥️ Running the Project
1. Clone the Repository
git clone https://github.com/youssefsalah224/AI-Engineer-Assessment-KidSafe-Alphabet-Tutor.git
cd AI-Engineer-Assessment-KidSafe-Alphabet-Tutor

2. Install Dependencies
pip install -r requirements.txt

3. Run the Backend + Frontend
uvicorn server.main:app --reload


Then open your browser at:
👉 http://localhost:8000

🎤 Running app.py for Terminal Testing

If you’d like to test the tutor logic without using transcription models (helpful if API quota is exceeded):

python app.py
This runs a simplified command-line version of the Alphabet Tutor, so you can test interactions and logic directly from the terminal.

📌 Notes
This is an assessment project, so the code is structured for clarity and readability rather than production scalability.

The app is designed with safety and simplicity first, tailored for a young audience.

👨‍💻 Author

Youssef Salah
AI Developer • Trader • Founder of Monk Clothing
📍 Egypt
