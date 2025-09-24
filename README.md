# Ai Voice Assistant

This project is an **experimental Apple Voice Assistant clone** with a **Python backend** (AI agent, memory, and database) and a **React/Vite frontend** (voice UI with LiveKit integration).  

⚠️ **Disclaimer:** This application is intended **only for testing purposes**. It is **not suitable for production deployment**.  

---

## ⚡ Features

### Backend
- **AI Agent Core (`agent.py`)** – Runs the backend assistant.
- **Prompts (`prompts.py`)** – Stores assistant/system prompts.
- **SQLite DB (`service_db.sqlite`)** – Handles service ticket storage.
- **Tools (`tools.py`)** – Includes weather, datetime, and ticket management utilities.
- **Environment Config (`.env`)** – Stores API keys and secrets (ignored in Git).
- **Extendable Modules** – Additional logic can be added inside `chatai/` and `KMS/`.

### Frontend
- **React + Vite** for a lightweight and fast UI.
- **LiveKit Integration** for real-time voice/video streaming.
- **Environment Config (`.env`)** stores LiveKit URL.
- **Token Handling** in `model.jsx` requires a LiveKit Room Token.

---

## 🔧 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/apple-voice-assistant.git
cd apple-voice-assistant

2. Backend Setup

cd backend
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows PowerShell

pip install -r requirements.txt

Create a .env file inside backend/:

GEMINI_API_KEY=your_api_key
LIVEKIT_API_KEY=your_livekit_key
LIVEKIT_API_SECRET=your_livekit_secret
LIVEKIT_URL=your_livekit_url

Run the backend agent:

python agent.py

3. Frontend Setup

cd frontend
npm install
npm run dev

Create a .env file inside frontend/:

VITE_LIVEKIT_URL=your_livekit_url

⚠️ In src/model.jsx, replace the token placeholder with a LiveKit Room Token:

const token = "YOUR_LIVE_KIT_TOKEN";

You can generate a LiveKit token from your LiveKit dashboard for testing.
🛠 Development Notes

    Update backend/tools.py to add new utilities.

    Modify backend/prompts.py to customize assistant behavior.

    Use backend/service_db.sqlite for persistent ticket storage.

    Extend backend logic inside chatai/ or KMS/.

    Frontend requires both a LiveKit URL (.env) and a LiveKit token (model.jsx).
