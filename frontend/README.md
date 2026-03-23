# Frontend (React + TypeScript)

This folder contains the frontend implementation of the **Local AI Chatbot with RAG**.

It provides a modern UI for interacting with the chatbot, supporting real-time streaming responses, session management, and Markdown rendering.

---

# 🚀 Features

* Real-time **streaming chat UI**
* Multi-session chat interface
* Markdown rendering (tables, lists, code blocks)
* Code block **copy button**
* Automatic scroll to latest message
* Loading states and error handling

---

# 🏗 Tech Stack

* React (TypeScript)
* Vite
* Fetch API (streaming support)
* React Markdown + remark-gfm

---

# ⚙️ Development

## Install dependencies

```bash
npm install
```

## Start development server

```bash
npm run dev
```

The app will be available at:

```text
http://localhost:5173
```

---

# 🔗 Backend Dependency

This frontend requires the backend server to be running.

Make sure to start the backend first:

```bash
uvicorn main:app --reload
```

---

# 📌 Notes

* Streaming responses are handled via a custom NDJSON-based API
* Final responses are synchronized after streaming completes (for source attribution)
* RAG-related logic is handled entirely on the backend

---

# 📖 More Information

For full system architecture and AI details, refer to the root README:

```text
../README.md
```
