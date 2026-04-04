# 🤖 Local AI Chatbot with RAG (FastAPI + React + Streaming)

A production-style **full-stack AI chatbot** powered by a local LLM, enhanced with **Retrieval-Augmented Generation (RAG)** for knowledge-aware responses.

The system supports **real-time streaming**, **multi-session chat**, and **intent-aware routing**, enabling dynamic switching between general conversation and knowledge-based answering.

> ⚠️ This project is for portfolio and demonstration purposes only.
> It is **not an open-source project**. All rights are reserved.

---

# 🚀 Key Features

## 💬 Chat Experience

* Real-time **token-level streaming responses**
* "Thinking..." state during generation
* Graceful error handling and fallback responses

## 🧠 AI Capabilities

* Local LLM integration (LM Studio / OpenAI-compatible API)
* Context-aware responses using chat history
* Automatic **AI-generated session titles**

## 📚 Retrieval-Augmented Generation (RAG)

* Semantic search over local knowledge base (Chroma)
* Query embedding + similarity search (Top-K retrieval)
* Dynamic **context injection into prompts**
* **Deterministic source attribution** (post-processing)
* **Intent-aware routing** (only trigger RAG when needed)

## 🗂 Session Management

* Multi-session chat system
* Rename / delete sessions
* Persistent chat history (SQLite)
* Sessions sorted by latest activity

## 🎨 UI / UX

* Clean, responsive interface
* Markdown rendering (tables, lists, code blocks)
* Code block **copy button**
* Streaming + final state synchronization (Sources appear after completion)

---

# 🏗 Tech Stack

## Backend

* FastAPI
* Python
* SQLite (chat persistence)
* Chroma (vector database)
* StreamingResponse (LLM streaming)

## Frontend

* React (TypeScript)
* Vite
* Fetch API (stream handling)
* React Markdown + remark-gfm

## AI / LLM

* Local LLM (LM Studio)
* OpenAI-compatible API
* Embedding model for semantic search

---

# 🧠 RAG Architecture

```
User Query
   ↓
Intent Router (heuristic)
   ↓
(If knowledge is needed)
   → Embedding → Vector Search (Chroma)
   → Retrieve Top-K Chunks
   ↓
Context Injection (Prompt Augmentation)
   ↓
LLM Generation (Streaming)
   ↓
Post-processing (Source Formatting)
   ↓
Frontend Sync (Final Message Update)
```

---

# 📂 Project Structure

```
local-llm-chatbot/
├── rag/
│   ├── loaders.py
│   ├── chunking.py
│   ├── embedding.py
│   ├── vector_store.py
│   ├── retrieval.py
│   └── router.py
├── chat_service.py
├── llm.py
├── frontend/
└── README.md
```

---

# ⚙️ Getting Started

## 1. Start Backend

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

## 2. Start Frontend

```bash
cd frontend
npm install
npm run dev
```

Run the frontend from the `frontend` directory.

## Common Issues

If you see `ModuleNotFoundError` (for example `uvicorn` or `chromadb`), install the backend dependencies with:

```bash
pip install -r requirements.txt
```

---

# 🧪 Example Prompts

## General Chat (No RAG)

* Hello
* Tell me a joke
* What can you do?

## Knowledge-Based Queries (RAG)

* What is Retrieval-Augmented Generation?
* How does RAG improve chatbot quality?
* Explain semantic search

---

## 🔥 Highlights

- Built a **production-style RAG-based AI application** integrating LLM, vector search, and full-stack architecture  

- Designed an **end-to-end RAG pipeline**:
  ingestion → embedding → retrieval → generation, enabling knowledge-grounded responses  

- Implemented **semantic search using Chroma vector database** to retrieve relevant context efficiently  

- Developed **intent-aware query routing**, dynamically switching between general LLM responses and retrieval-based answering  

- Implemented **deterministic post-processing for source attribution**, improving transparency and trustworthiness of responses  

- Built **real-time streaming LLM responses with frontend synchronization**, enhancing user experience  

- Designed a **multi-session chat architecture with persistent storage (SQLite)** for scalable conversation management  

- Focused on **system design, user experience, and practical AI integration**, rather than isolated model usage  

---

# 📌 License

This project is **not open source**.
All rights reserved.
Unauthorized copying, modification, or distribution is not permitted.
