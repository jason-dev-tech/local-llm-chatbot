# 🤖 Local-First AI Chatbot with RAG, Tools, and Routing

A local-first **full-stack AI chatbot** built with FastAPI and React, powered by a local LLM and extended with **multi-source Retrieval-Augmented Generation (RAG)**, backend-controlled citations, and a lightweight tool-and-routing foundation.

The current system supports **real-time streaming**, **multi-session chat**, **multi-source retrieval**, **deterministic attribution**, and **conservative agent-style routing** across chat, RAG, and tools.

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
* Rule-based and LLM-assisted routing across chat, RAG, and tools

## 📚 Retrieval-Augmented Generation (RAG)

* Semantic search over local knowledge base (Chroma)
* Query embedding + similarity search (Top-K retrieval)
* Dynamic **context injection into prompts**
* Multi-source knowledge file support for retrieval and attribution
* Backend-controlled **inline citations** for RAG answers
* Stable numbered citations aligned with the final attribution block
* Normalized source metadata and cleaner source labels for readability
* Dual-section attribution with **Sources used** and **Retrieved context**
* **Deterministic source attribution** and citation post-processing
* **Intent-aware routing** for knowledge-grounded requests

## 🛠 Tooling Foundation

* Minimal tool abstraction with a registry-based lookup layer
* `summarize_text` tool for direct text summarization
* `rewrite_text` tool for direct text rewriting / cleanup
* Rule-based routing for explicit tool commands
* LLM-based router for ambiguous chat / RAG / tool selection
* Minimal retrieval-summary loop:
  summarize intent → retrieve knowledge → summarize retrieved text

## 🧪 Evaluation Coverage

* Deterministic evals for RAG routing behavior
* Citation and Sources section checks
* Source label and multi-source retrieval checks
* Separate routing evals for heuristic, LLM, and effective route outcomes
* Tool evals for summarize / rewrite routing and execution

## 🗂 Session Management

* Multi-session chat system
* Rename / delete sessions
* Persistent chat history (SQLite)
* Sessions sorted by latest activity

## 🎨 UI / UX

* Clean, responsive interface
* Markdown rendering (tables, lists, code blocks)
* Code block **copy button**
* Streaming + final state synchronization for backend-built attribution blocks

## Current Status

The project currently represents a solid **agent foundation milestone**: local chat, multi-source RAG, deterministic attribution, a small tool registry, rule-based and LLM-assisted routing, and a narrow multi-step retrieval-summary path. The architecture is intentionally simple, but it is structured to extend cleanly into broader agent-style workflows.

---

# 🏗 Tech Stack

## Backend

* FastAPI
* Python
* SQLite (chat persistence)
* Chroma (vector database)
* LangChain
* StreamingResponse (LLM streaming)

## Frontend

* React (TypeScript)
* Vite
* Fetch API (stream handling)
* React Markdown + remark-gfm

## AI / LLM

* Local LLM (LM Studio)
* OpenAI-compatible API
* LangChain for model orchestration and streaming
* Embedding model for semantic search

---

# 🧠 System Architecture

```
User Query
   ↓
Routing Layer
   → Rule-based tool router
   → Heuristic RAG router
   → LLM router fallback
   ↓
(1) Chat path
   → Direct LLM response

(2) RAG path
   → Embedding → Vector Search (Chroma)
   → Retrieve Top-K Chunks
   → Context Injection
   → LLM Generation
   → Inline Citation + Attribution Post-processing

(3) Tool path
   → Tool registry lookup
   → summarize_text / rewrite_text

(4) Retrieval-summary path
   → Retrieve relevant chunks
   → Build text from retrieved context
   → Run summarize_text
   → Append attribution
```

## Core Workflow Notes

* RAG answers use backend-controlled inline citations such as `[1]` and `[2]`
* Final attribution is split into **Sources used** and **Retrieved context**
* Source numbering remains stable across inline citations and the final attribution block
* Source metadata is normalized during ingestion / retrieval to improve attribution quality
* Explicit tool commands are handled conservatively before ambiguous LLM-routed cases

---

# 📂 Project Structure

```
local-llm-chatbot/
├── routing/
│   └── llm_router.py
├── rag/
│   ├── loaders.py
│   ├── chunking.py
│   ├── embedding.py
│   ├── vector_store.py
│   ├── retrieval.py
│   └── router.py
├── tools/
│   ├── base.py
│   ├── registry.py
│   ├── summarize.py
│   ├── rewrite.py
│   └── router.py
├── evals/
│   ├── run_evals.py
│   ├── run_routing_evals.py
│   └── run_tool_evals.py
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
python -m uvicorn main:app --reload
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

## Tool Queries

* summarize: Retrieval-Augmented Generation improves grounded answers.
* rewrite: This   sentence   should be cleaner.

## Retrieval-Summary Queries

* Summarize what the knowledge base says about RAG
* Summarize the docs about retrieval and citations

---

# ✅ Evaluation

Run the deterministic evaluation scripts from the project root:

```bash
python3 evals/run_evals.py
python3 evals/run_routing_evals.py
python3 evals/run_tool_evals.py
```

These scripts validate routing, multi-source retrieval behavior, citation formatting, source labeling, and direct tool execution without relying on model-graded evaluation.

---

## 🔥 Highlights

- Built a **local-first AI chatbot system** integrating local LLM usage, vector retrieval, deterministic attribution, and a React/FastAPI stack  

- Implemented an **end-to-end multi-source RAG pipeline**:
  ingestion → embedding → retrieval → generation → attribution  

- Added **backend-controlled inline citations** with stable numbering and dual-section attribution for transparency  

- Designed **routing layers for chat, RAG, and tools**, combining heuristic decisions, explicit command handling, and a minimal LLM router  

- Introduced a **tool abstraction and registry** with summarize and rewrite tools as the first agent-oriented capabilities  

- Added a narrow **retrieval-summary loop**, showing how tool execution can be composed with retrieval without a full autonomous agent framework  

- Built **deterministic evaluation coverage** for routing, citations, source labels, multi-source retrieval, and tool behavior  

- Built **real-time streaming chat** with persistent multi-session history in SQLite  

- Focused on **system design, evaluation discipline, and extensibility**, not just isolated prompt calls  

---

# 📌 License

This project is **not open source**.
All rights reserved.
Unauthorized copying, modification, or distribution is not permitted.
