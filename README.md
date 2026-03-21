# 🧠 Local AI Chatbot (CLI + FastAPI)

A local-first AI chatbot built with Python, LM Studio, SQLite, and FastAPI.

---

## 📌 Project Status

🚧 Actively evolving into a full AI application.

Current capabilities:

- Local LLM integration via LM Studio
- CLI chatbot interface
- FastAPI backend API
- Multi-session chat management
- Persistent chat history
- Streaming-ready architecture

---

## 📖 Overview

This project is a **local AI chatbot system** that runs entirely on your machine and communicates with a locally hosted language model via an OpenAI-compatible API.

It started as a CLI chatbot and has been refactored into a **layered backend architecture** with FastAPI support, making it ready for web-based interfaces and future AI extensions such as RAG.

---

## ✨ Features

- Local LLM inference (LM Studio)
- OpenAI-compatible API integration
- CLI chatbot interface
- FastAPI backend (REST API)
- Multi-session conversation support
- Persistent chat history (SQLite)
- Automatic session title generation
- Clean layered architecture

---

## 🏗️ Architecture

```
            ┌───────────────┐
            │   CLI / API   │
            │  (app / main) │
            └──────┬────────┘
                   ↓
            ┌───────────────┐
            │ Chat Service  │
            │ (business logic)
            └──────┬────────┘
                   ↓
        ┌───────────────┐     ┌───────────────┐
        │     SQLite     │     │   LM Studio   │
        │ (chat history) │     │ (local LLM)   │
        └───────────────┘     └───────────────┘
```

---

## 📁 Project Structure

```
.
├── app.py
├── main.py
├── chat_service.py
├── llm.py
├── db.py
├── config.py
├── data/
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## ⚙️ Configuration

Environment variables are managed via `.env`.

Example:

```
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=meta-llama-3.1-8b-instruct
DB_PATH=data/chat_store.db
```

---

## 🚀 Getting Started

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

---

## 🤖 Run CLI

```bash
python app.py
```

---

## 🌐 Run API

```bash
uvicorn main:app --reload
```

Docs:

http://127.0.0.1:8000/docs

---

## 🔌 API Endpoints

- GET /sessions
- POST /sessions
- GET /sessions/{session_id}
- POST /chat
- PATCH /sessions/{session_id}
- DELETE /sessions/{session_id}

---

## 💾 Data Storage

Local SQLite database:

```
data/chat_store.db
```

---

## 🔐 Privacy

- Fully local execution
- No external API calls
- No data leaves your machine

---

## 🧩 Tech Stack

- Python
- FastAPI
- OpenAI SDK
- LM Studio
- SQLite

---

## 🚀 Roadmap

- Streaming API
- Web UI
- RAG support

---

## 📝 Goal

Building toward becoming an AI Application Engineer with real-world backend and LLM integration experience.
