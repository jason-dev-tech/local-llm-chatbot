# 🤖 Local AI Chatbot (FastAPI + React + Streaming)

A full-stack AI chatbot application running with a **local LLM**, featuring real-time streaming responses, multi-session chat management, and a modern React UI.

> ⚠️ This project is for portfolio and demonstration purposes only.  
> It is **not an open-source project**. All rights are reserved.

---

## 🚀 Features

### 💬 Chat Experience
- Real-time **streaming responses** (token-by-token)
- "Thinking..." state during generation
- Error handling and fallback messages

### 🧠 AI Capabilities
- Local LLM integration (via LM Studio / OpenAI-compatible API)
- Automatic **session title generation** using AI
- Context-aware responses (recent message history)

### 🗂 Session Management
- Create multiple chat sessions
- Rename / delete sessions
- Persistent chat history (SQLite)
- Sessions sorted by latest activity

### 🎨 UI / UX
- Clean, responsive layout
- Markdown rendering (headings, lists, tables, code blocks)
- Code block **copy button**
- Loading states for sessions and messages

---

## 🏗 Tech Stack

### Backend
- FastAPI
- SQLite
- Python
- StreamingResponse (token streaming)

### Frontend
- React (TypeScript)
- Vite
- Fetch API (stream handling)
- React Markdown + remark-gfm

### AI / LLM
- Local LLM (LM Studio)
- OpenAI-compatible API

---

## 📂 Project Structure

```
local-llm-chatbot/
├── backend/
├── frontend/
└── README.md
```

---

## ⚙️ Getting Started

### 1. Start Backend

```
cd backend
uvicorn main:app --reload
```

### 2. Start Frontend

```
cd frontend
npm install
npm run dev
```

---

## 🧪 Example Prompts

- Explain how the internet works
- Give me a Python example to read a file
- Compare Python and JavaScript in a table
- Give me a step-by-step plan to learn React

---

## 🔥 Highlights

- Built a **full-stack AI application**
- Implemented **real-time streaming LLM responses**
- Designed **session-based chat architecture**
- Applied **modern React component structure**
- Focused on **product-level UX**

---

## 📌 License

This project is **not open source**.  
All rights reserved.  
Unauthorized copying, modification, or distribution is not permitted.
