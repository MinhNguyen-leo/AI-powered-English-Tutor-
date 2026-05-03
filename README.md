# 🎓 AI-Powered English Tutor

> Personalized IELTS English tutor with real-time chat correction, writing feedback, and AI memory that learns from your mistakes.

[![Python](https://img.shields.io/badge/Python-3.10+-blue)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.111-green)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18-61dafb)](https://react.dev)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-orange)](https://openai.com)

---

## ✨ Features

| Feature | Description |
|---------|-------------|
| 💬 **Chat Correction** | Send any English text and get instant grammar/vocabulary corrections |
| ✍️ **Writing Coach** | Paste an IELTS essay and receive band scores + detailed feedback |
| 🧠 **Memory System** | Your past mistakes are stored and retrieved via FAISS vector search |
| 🎯 **Personalization** | The AI references your previous errors to give tailored advice |
| 📊 **IELTS Scoring** | Sub-scores for Grammar, Vocabulary, Task Achievement, Coherence |

---

## 🏗️ Architecture

```
User Input
    │
    ▼
React Frontend (Vite)
    │  POST /chat  or  POST /writing
    ▼
FastAPI Backend
    ├── RAG Service (FAISS + sentence-transformers)
    │       └── retrieve top-3 past mistakes → context string
    ├── AI Service (OpenAI GPT-4o-mini)
    │       └── system prompt → structured JSON response
    └── Memory Service (JSON persistence)
            └── store new errors → update FAISS index
```

---

## 🚀 Quick Start

### Prerequisites
- Python >= 3.10
- Node.js >= 18
- An [OpenAI API key](https://platform.openai.com/api-keys)

---

### 1. Clone & Setup

```bash
git clone https://github.com/YOUR_USERNAME/AI-powered-English-Tutor-.git
cd AI-powered-English-Tutor-
```

### 2. Backend Setup

```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Configure Environment

```bash
# Copy example env file
copy .env.example .env       # Windows
cp .env.example .env         # Mac/Linux

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=sk-your-key-here
```

### 4. Run the Backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

> API docs available at: http://localhost:8000/docs

### 5. Frontend Setup (new terminal)

```bash
cd frontend
npm install
npm run dev
```

> App available at: http://localhost:5173

---

## 📁 Project Structure

```
AI-powered-English-Tutor-/
├── backend/
│   ├── main.py                 # FastAPI app entry point
│   ├── requirements.txt
│   ├── routers/
│   │   ├── chat.py             # POST /chat
│   │   ├── writing.py          # POST /writing
│   │   └── memory_router.py    # GET /memory/{user_id}/stats
│   ├── services/
│   │   ├── ai_service.py       # OpenAI API + prompt engineering
│   │   ├── memory.py           # Error storage (JSON persistence)
│   │   └── rag.py              # FAISS vector index + retrieval
│   ├── models/
│   │   └── schemas.py          # Pydantic request/response models
│   ├── utils/
│   │   └── logger.py           # Dual console+JSONL logging
│   └── data/                   # Auto-created: memory.json, logs.jsonl
├── frontend/
│   └── src/
│       ├── App.jsx             # App shell + sidebar navigation
│       ├── index.css           # Full design system
│       ├── components/
│       │   ├── ChatPage.jsx    # Chat UI with correction display
│       │   ├── WritingPage.jsx # IELTS essay analyzer
│       │   ├── HistoryPanel.jsx# Past mistakes + stats
│       │   └── ScoreRing.jsx   # Animated SVG score ring
│       └── services/
│           └── api.js          # Axios API client
├── .env.example
├── .gitignore
└── README.md
```

---

## 🧪 Testing the API

```bash
# Test chat endpoint
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "message": "I goes to school yesterday"}'

# Test writing endpoint
curl -X POST http://localhost:8000/writing \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test", "text": "Technology have many benefit for society...", "task_type": "Task 2"}'

# Get memory stats
curl http://localhost:8000/memory/test/stats
```

---

## 🌐 Deployment

### Backend → Render

1. Push to GitHub
2. Create new **Web Service** on [render.com](https://render.com)
3. Set environment variables: `OPENAI_API_KEY`, `OPENAI_MODEL`
4. Build command: `pip install -r backend/requirements.txt`
5. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

### Frontend → Vercel

1. Import GitHub repo on [vercel.com](https://vercel.com)
2. Set **Root Directory** to `frontend`
3. Add env variable: `VITE_API_URL=https://your-render-url.onrender.com`
4. Deploy

---

## 📄 License

MIT — built for learning and portfolio purposes.
