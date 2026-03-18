# 🧠 Local AI CLI Chatbot (LM Studio + Python + SQLite)

## 📌 Project Status

🚧 This project is currently under active development.

The goal is to build a **local AI application** with:

* Local LLM inference (LM Studio)
* Persistent chat history (SQLite)
* Clean and extensible architecture

---

## 📖 Overview

This is a **local AI chatbot** that runs entirely on your machine.

Key characteristics:

* No external API dependency
* Uses a locally hosted LLM via LM Studio
* Stores chat history in SQLite
* Designed as a foundation for future AI features (e.g., RAG)

---

## 🏗️ Current Architecture

```text
User Input
   ↓
Python CLI (app.py)
   ↓
LM Studio (local API server)
   ↓
Local LLM response
   ↓
SQLite (chat history)
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
└── .gitignore
```

---

## ⚙️ Configuration

Environment variables are managed via `.env`:

```env
OPENAI_BASE_URL=http://localhost:1234/v1
OPENAI_API_KEY=lm-studio
MODEL_NAME=your-local-model-name
DB_PATH=data/chat_store.db
SESSION_ID=default
```

---

## 🧩 Tech Stack

* Python
* OpenAI Python SDK (OpenAI-compatible API)
* LM Studio (local LLM)
* SQLite

---

## 💾 Data Handling

* Chat history is stored locally in:

  ```
  data/chat_store.db
  ```

* The `data/` directory is excluded from version control.

---

## 🔐 Privacy

* All processing is done locally
* No external API calls
* No data leaves the machine

---

## 🎯 Next Steps

* [ ] Connect to LM Studio and verify local inference
* [ ] Improve error handling
* [ ] Support multi-session chat
* [ ] Add streaming responses
* [ ] Prepare for RAG (embeddings + retrieval)

---

## 📝 Notes

This project is part of a learning path toward becoming an **AI Application Engineer**, focusing on:

* Real-world architecture
* Local-first AI systems
* Clean code and project structure
