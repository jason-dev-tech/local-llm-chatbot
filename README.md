# 🤖 Local-First AI Chatbot with RAG, Citations, Tools, and Routing

A local-first **full-stack AI application** built with FastAPI and React, powered by a local LLM and extended with **multi-source Retrieval-Augmented Generation (RAG)**, deterministic attribution, and a lightweight agent foundation for tool-aware routing.

The current system supports **real-time streaming**, **multi-session chat**, **multi-source retrieval**, **inline citations**, **registry-based tools**, and **conservative routing** across chat, RAG, direct tools, and retrieval-summary flows.

> This repository is maintained as a local-first engineering system.
> It is **not an open-source project**. All rights are reserved.

---

# 🚀 System Overview

This system combines three core capabilities in one local-first runtime:

* **RAG** for knowledge-grounded responses over multi-source local documents
* **Tools** for direct text operations and structured query understanding
* **Routing** to decide between chat, retrieval, and explicit tool execution

The current implementation is positioned as an **extensible agent foundation**, not a full autonomous agent system. It emphasizes deterministic formatting, isolated execution paths, and evaluation-backed behavior.

---

# 🚀 Core Capabilities

## 💬 Chat Experience

* Real-time **token-level streaming responses**
* "Thinking..." state during generation
* Graceful error handling and fallback responses

## 🧠 AI Capabilities

* Local LLM integration (LM Studio / OpenAI-compatible API)
* Context-aware responses using chat history
* Automatic **AI-generated session titles**
* Rule-based and LLM-assisted routing across chat, RAG, and tools
* Structured query understanding that converts free-form input into downstream routing and retrieval signals

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

## 🛠 Tooling Layer

* Registry-based tool abstraction for name-based tool resolution
* `summarize_text` tool for direct text summarization
* `rewrite_text` tool for controlled rewriting that preserves meaning while improving clarity
* `extract_entities` tool for structured query analysis with JSON output
* Deterministic summarize behavior for explicit direct-input requests
* Controlled rewrite behavior with whitespace normalization, conservative prompting, and fallback to cleaned text
* Structured extraction output designed for downstream retrieval, routing, and system decisions
* Tools are isolated from the RAG response pipeline to avoid corrupting citation or attribution formatting

## 🧩 Structured Query Understanding

* `extract_entities` converts free-form user input into structured query signals
* Output is returned as JSON for system consumption rather than natural-language explanation
* The extracted structure emphasizes:
  * `query_type`
  * `topics`
  * `technologies`
  * `files`
  * `requested_operation`
* This tool is intended as a preprocessing capability for downstream retrieval and routing decisions

## 🧭 Routing Strategy

* Direct tool matching for explicit summarize and rewrite requests
* Direct tool matching for explicit entity-extraction requests
* Heuristic routing for clear RAG-oriented queries
* LLM routing fallback for ambiguous cases
* Explicit tool requests take priority over retrieval-summary fallback
* Retrieval-summary path remains available for summarize-over-knowledge requests
* Tool priority ordering prevents explicit tool intent from falling into RAG formatting flows

## 🧪 Evaluation Coverage

* Deterministic chatbot evals for routing, citations, source labels, and multi-source behavior
* Deterministic routing evals for heuristic, LLM, and effective route outcomes
* Behavioral tool evals for summarize / rewrite execution
* JSON-aware tool evals for structured extraction output
* Frontend validation completed for summarize, rewrite, normal chat, and RAG flows

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

The current milestone is a **production-style local AI system architecture** with multi-source RAG, deterministic attribution, registry-based tools, explicit tool priority, rule-based and LLM-assisted routing, and a narrow retrieval-summary composition path. The design is intentionally controlled and modular, with clear seams for extending the system without turning it into an uncontrolled agent loop.

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
   → Direct tool matching
   → Heuristic RAG router
   → LLM router fallback
   ↓
   → Tool path
   → RAG path
   → Chat path

Tool path
   → Tool registry lookup
   → summarize_text / rewrite_text / extract_entities

RAG path
   → Embedding → Vector Search (Chroma)
   → Retrieve Top-K Chunks
   → Context Injection
   → LLM Generation
   → Inline Citation + Attribution Post-processing

Chat path
   → Direct LLM response

Retrieval-summary path
   → Retrieve relevant chunks
   → Build text from retrieved context
   → Run summarize_text
   → Append attribution
```

## Separation of Concerns

* **Tool execution** is isolated behind a registry-based lookup layer
* **Retrieval** is responsible for chunk selection and source metadata propagation
* **Response formatting** is responsible for inline citations and deterministic attribution output
* **Routing** decides between explicit tools, RAG, retrieval-summary, and chat
* **Structured extraction** provides normalized query signals for downstream decisions

## Design Decisions

* Tools are isolated from the RAG pipeline to prevent formatting corruption
* Explicit tool intent takes priority over retrieval
* Attribution formatting is deterministic and normalized
* Evaluation is split between deterministic and behavioral checks
* Structured extraction is normalized to ensure stable downstream behavior
* Lightweight post-processing is used to stabilize category assignment such as technologies vs topics
* The routing layer is conservative by design and avoids claiming full autonomy

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
│   ├── extract_entities.py
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
* extract entities: Compare RAG in LangChain with Chroma and FastAPI using sample.txt and faq.txt

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

Current verified milestone:

* `tool evals`: **100%**
* `routing evals`: **100%**
* `chatbot evals`: **100%**

Verified coverage includes:

* Chatbot evaluation for RAG routing, inline citations, source labels, and multi-source behavior
* Routing evaluation for direct tool routing, heuristic routing, and LLM-assisted fallback
* Tool evaluation for summarize, rewrite, and structured extraction behavior
* JSON-aware validation for valid JSON, expected keys, and expected extracted content

## Frontend Behavior

Verified frontend flows:

* summarize tool requests
* rewrite tool requests
* normal chat queries
* RAG queries with source rendering

Frontend behavior includes streaming responses and sectioned source rendering for deterministic attribution blocks.

---

## 🔥 Highlights

- Local-first AI system architecture integrating local LLM usage, vector retrieval, deterministic attribution, and a React/FastAPI stack  

- End-to-end multi-source RAG pipeline:
  ingestion → embedding → retrieval → generation → attribution  

- Backend-controlled inline citations with stable numbering and dual-section attribution  

- Routing layers for chat, RAG, and tools, combining direct tool matching, heuristic decisions, and a minimal LLM router  

- Tool abstraction and registry with `summarize_text`, `rewrite_text`, and `extract_entities` as the current tool set  

- Narrow retrieval-summary loop that composes retrieval with tool execution without a full autonomous agent framework  

- Deterministic and behavior-based evaluation coverage for routing, citations, source labels, multi-source retrieval, and tool behavior  

- Verified frontend behavior for summarize, rewrite, chat, and RAG flows  

- System design emphasizes isolation, deterministic formatting, routing control, and extensibility  

---

# 📌 License

This project is **not open source**.
All rights reserved.
Unauthorized copying, modification, or distribution is not permitted.
