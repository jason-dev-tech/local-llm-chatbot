# 🧠 Local AI CLI Chatbot

A local-first AI chatbot built with Python, LM Studio, and SQLite.

---

## 📌 Project Status

🚧 This project is under active development.

Current focus:

- Local LLM integration via LM Studio
- Streaming chat experience
- Persistent chat history
- Clean and extensible architecture

---

## 📖 Overview

This project is a **local AI chatbot** that runs entirely on your machine and communicates with a locally hosted language model through an OpenAI-compatible API.

### Key Characteristics

- Runs fully locally (no cloud dependency)
- Uses LM Studio as the LLM runtime
- Stores chat history in SQLite
- Supports real-time streaming responses
- Designed for future RAG and AI system extensions

---

## ✨ Features

- Local LLM inference via LM Studio
- OpenAI-compatible API integration
- Interactive CLI chatbot
- Streaming responses (real-time output)
- Persistent chat history (SQLite)
- Session-based conversation handling (single session)

---

## 🏗️ Architecture

```text
User Input
   ↓
Python CLI (app.py)
   ↓
LM Studio (local API server)
   ↓
Streaming LLM response
   ↓
SQLite (chat history persistence)
```

---

## 📁 Project Structure

```text
.
├── app.py
├── config.py
├── db.py
├── data/                # runtime data (not tracked)
├── requirements.txt
├── README.md
├── .env.example
└── .gitignore
```

---

## ⚙️ Configuration

Environment variables are managed via `.env`.

Example:

```env
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=meta-llama-3.1-8b-instruct
DB_PATH=data/chat_store.db
SESSION_ID=default
```

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone <your-repo-url>
cd ai-cli-chatbot
```

### 2. Create virtual environment

```bash
python3 -m venv .venv
```

### 3. Activate environment

```bash
source .venv/bin/activate
```

### 4. Install dependencies

```bash
pip install -r requirements.txt
```

### 5. Setup environment variables

```bash
cp .env.example .env
```

Update `.env`:

```env
MODEL_NAME=meta-llama-3.1-8b-instruct
```

### 6. Start LM Studio

- Load your model
- Start local server (`http://localhost:1234`)

### 7. Run the chatbot

```bash
python app.py
```

---

## 💬 Usage

```text
You: Hello
AI: Hello! How can I assist you today?
```

### Commands

- `exit` → Quit chatbot
- `/history` → Show recent chat history

---

## 💾 Data Storage

- Chat history is stored in:

```text
data/chat_store.db
```

- Data is local-only and not tracked by Git.

---

## 🔐 Privacy

- All inference runs locally
- No external API calls
- No data leaves your machine

---

## 🧩 Tech Stack

- Python
- OpenAI Python SDK
- LM Studio
- SQLite
- python-dotenv

---

## 🚀 Development Roadmap

### ✅ Completed

- [x] Local LLM integration (LM Studio)
- [x] CLI chatbot
- [x] SQLite chat persistence
- [x] Streaming responses

### 🔜 Planned

- [ ] Multi-session support
- [ ] Embeddings + Retrieval (RAG)
- [ ] Web UI (FastAPI + frontend)
- [ ] Prompt optimization
- [ ] Chat export / logging

---

## 💡 Why This Project

This project demonstrates how to build a **local-first AI application** without relying on external APIs.

It focuses on:

- privacy-first AI architecture
- cost-free LLM usage
- real-time user experience
- scalable design for future AI systems

---

## 📝 Learning Goal

Part of a learning path toward becoming an **AI Application Engineer**, focusing on:

- LLM integration
- real-world AI system design
- maintainable Python architecture
- production-ready patterns
