# 🤖 Local AI Chatbot with RAG (FastAPI + React + Streaming)

A full-stack AI chatbot application powered by a **local LLM**, enhanced with **Retrieval-Augmented Generation (RAG)** for knowledge-aware responses.
The system supports real-time streaming, multi-session chat, and intelligent routing between general conversation and knowledge-based answering.

> ⚠️ This project is for portfolio and demonstration purposes only.
> It is **not an open-source project**. All rights are reserved.

---

# 🚀 Features

## 💬 Chat Experience

* Real-time **streaming responses** (token-by-token)
* "Thinking..." state during generation
* Graceful error handling and fallback responses

## 🧠 AI Capabilities

* Local LLM integration (via LM Studio / OpenAI-compatible API)
* **RAG (Retrieval-Augmented Generation)** support
* Context-aware responses using recent chat history
* Automatic **AI-generated session titles**

## 📚 Knowledge-Aware Responses (RAG)

* Semantic search over local knowledge base
* Automatic **context injection** into LLM prompts
* **Source attribution** in responses
* Deterministic **post-processing for clean source formatting**
* **Intent-aware routing** (only trigger RAG when needed)

## 🗂 Session Management

* Multiple chat sessions
* Rename / delete sessions
* Persistent chat history (SQLite)
* Sessions sorted by latest activity

## 🎨 UI / UX

* Clean, responsive interface
* Markdown rendering (headings, tables, lists, code blocks)
* Code block **copy button**
* Loading states for sessions and messages

---

# 🏗 Tech Stack

## Backend

* FastAPI
* Python
* SQLite (chat persistence)
* Chroma (vector database for RAG)
* StreamingResponse (token streaming)

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

# 🧠 RAG Architecture Overview

```
User Query
   ↓
Intent Router (heuristic)
   ↓
(If needed)
   → Embedding → Vector Search (Chroma)
   → Retrieve Top-K Chunks
   ↓
Context Injection
   ↓
LLM Generation
   ↓
Post-processing (Source Formatting)
   ↓
Final Answer
```

---

# 📂 Project Structure

```
local-llm-chatbot/
├── backend/
│   ├── rag/
│   │   ├── loaders.py
│   │   ├── chunking.py
│   │   ├── embedding.py
│   │   ├── vector_store.py
│   │   ├── retrieval.py
│   │   └── router.py
│   ├── chat_service.py
│   ├── llm.py
│   └── ...
├── frontend/
└── README.md
```

---

# ⚙️ Getting Started

## 1. Start Backend

```
cd backend
uvicorn main:app --reload
```

## 2. Start Frontend

```
cd frontend
npm install
npm run dev
```

---

# 🧪 Example Prompts

## General Chat

* Hello
* Tell me a joke
* What can you do?

## Knowledge-Based (RAG)

* What is Retrieval-Augmented Generation?
* How does RAG improve chatbot quality?
* Explain how semantic search works

---

# 🔥 Highlights (For Recruiters)

* Built a **full-stack AI application with RAG architecture**
* Implemented **semantic search with vector database (Chroma)**
* Designed **end-to-end RAG pipeline**:

  * ingestion → embedding → retrieval → generation
* Developed **intent-aware routing** for conditional RAG usage
* Implemented **deterministic source attribution (post-processing)**
* Built **real-time streaming LLM responses**
* Designed **multi-session chat system with persistence**
* Focused on **production-like system design and UX**

---

# 📌 License

This project is **not open source**.
All rights reserved.
Unauthorized copying, modification, or distribution is not permitted.
