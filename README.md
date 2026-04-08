# 🤖 Local-First AI Chatbot with RAG, Citations, Tools, and Routing

A local-first **full-stack AI application** built with FastAPI and React, powered by a local LLM and extended with **multi-source Retrieval-Augmented Generation (RAG)**, deterministic attribution, structured query understanding, lightweight backend observability, and a lightweight agent foundation for tool-aware routing.

The current system supports **real-time streaming**, **multi-session chat**, **multi-source retrieval**, **inline citations**, **registry-based tools**, **metadata-aware file filtering**, **structured observability logging**, and **conservative routing** across chat, RAG, direct tools, and retrieval-summary flows.

> This repository is maintained as a local-first engineering system.
> It is **not an open-source project**. All rights are reserved.

---

# 🚀 System Overview

This system combines three core capabilities in one local-first runtime:

* **RAG** for knowledge-grounded responses over multi-source local documents
* **Tools** for direct text operations and structured query understanding
* **Routing** to decide between chat, retrieval, and explicit tool execution
* **Observability** for backend-side request logging and terminal-based metrics aggregation

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
* File-aware retrieval that uses explicit file references to apply metadata-based filtering and improve retrieval precision
* Structured backend observability logging for routing, retrieval, and response behavior

## 📚 Retrieval-Augmented Generation (RAG)

* Semantic search over local knowledge base (Chroma)
* Query embedding + similarity search (Top-K retrieval)
* Dynamic **context injection into prompts**
* Multi-source knowledge file support for retrieval and attribution
* Metadata-aware retrieval filtering when explicit file references are present in the query
* Backend-controlled **inline citations** for RAG answers
* Stable numbered citations aligned with the final attribution block
* Normalized source metadata and cleaner source labels for readability
* Dual-section attribution with **Sources used** and **Retrieved context**
* **Deterministic source attribution** and citation post-processing
* **Intent-aware routing** for knowledge-grounded requests
* If a query contains explicit file references, retrieval is restricted to those files for more precise and controlled answers

## 🛠 Tooling Layer

* Registry-based tool abstraction for name-based tool resolution
* `summarize_text` tool for direct text summarization
* `rewrite_text` tool for controlled rewriting that preserves meaning while improving clarity
* `extract_entities` tool for structured query analysis with JSON output
* Deterministic summarize behavior for explicit direct-input requests
* Controlled rewrite behavior with whitespace normalization, conservative prompting, and fallback to cleaned text
* Structured extraction output designed for downstream retrieval, routing, and system decisions
* `extract_entities` is also used internally for query analysis before retrieval when explicit file signals are present
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
* This tool is used both as an explicit system capability and as a preprocessing step for retrieval and routing decisions

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

## 📈 Observability / Monitoring

* Structured backend observability logs emitted during request handling
* Automatic file-based backend log generation for real application runs
* Terminal-based Metrics Aggregation Layer for request, outcome, session, query, and retrieval summaries
* Current monitoring workflow is backend-side only and is not exposed in the frontend

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

The current milestone is a **production-style local AI system architecture** with multi-source RAG, deterministic attribution, registry-based tools, explicit tool priority, rule-based and LLM-assisted routing, a narrow retrieval-summary composition path, and a lightweight observability and metrics foundation. The design is intentionally controlled and modular, with clear seams for extending the system without turning it into an uncontrolled agent loop.

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
Query Analysis
   → extract_entities for structured query signals when explicit file references are present
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

Observability path
   → Structured route / retrieval / response log events
   → Console output + local log file
   → Terminal metrics summary script
```

## Separation of Concerns

* **Tool execution** is isolated behind a registry-based lookup layer
* **Retrieval** is responsible for chunk selection and source metadata propagation
* **Response formatting** is responsible for inline citations and deterministic attribution output
* **Routing** decides between explicit tools, RAG, retrieval-summary, and chat
* **Structured extraction** provides normalized query signals for downstream decisions
* **Observability** records structured backend events without changing response behavior

## Design Decisions

* Tools are isolated from the RAG pipeline to prevent formatting corruption
* Explicit tool intent takes priority over retrieval
* Attribution formatting is deterministic and normalized
* Evaluation is split between deterministic and behavioral checks
* Structured extraction is normalized to ensure stable downstream behavior
* Lightweight post-processing is used to stabilize category assignment such as technologies vs topics
* Lightweight query analysis is applied before retrieval when explicit signals such as filenames are present
* Filtering is only applied when confident signals are detected to avoid degrading recall
* The routing layer is conservative by design and avoids claiming full autonomy
* Monitoring is currently implemented as backend logging plus terminal-based aggregation rather than a frontend dashboard

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
├── observability/
│   └── metrics_summary.py
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

## Backend Observability

The backend writes structured observability events during real application runs. These logs are intended for terminal-side debugging and local monitoring, and they are not currently surfaced in the frontend UI.

### What it captures

* request route decisions
* tool usage
* retrieval event details such as filenames and chunk counts
* response-stage latency
* cited sources used in final answers when available

### Where logs are written

Backend logs are written automatically to:

```bash
logs/backend.log
```

The backend also continues to print logs to the terminal during normal development runs.

### How to verify log generation

1. Start the backend:

```bash
python -m uvicorn main:app --reload
```

2. Start the frontend and send a few chat, RAG, or tool requests.
3. Confirm log output is being appended locally:

```bash
tail -f logs/backend.log
```

You should see structured JSON-style log lines for stages such as `route`, `retrieval`, `response`, and `error`.

## Metrics Aggregation Layer

The Metrics Aggregation Layer is a small backend-side CLI utility that reads structured backend observability logs and produces a readable monitoring summary for engineering review.

Use it when you want a quick local view of request volume, request outcomes, routing behavior, latency, session usage, query patterns, tool usage, or retrieval behavior from real chatbot runs.

### Run the metrics summary

From the project root:

```bash
python3 -m observability.metrics_summary logs/backend.log
```

You can also pass multiple log files or pipe log content into the command.

### Summary output includes

* overall request count
* overall success / failure counts and success rate
* overall average response-stage latency
* p50 and p95 response-stage latency
* average latency grouped by effective route
* successful response distribution by effective route
* per-route success / failure counts and success rate
* tool usage frequency
* active session count
* requests per session
* route usage per session
* top repeated user queries
* query counts grouped by effective route
* retrieval event count
* average retrieved chunk count
* zero-retrieval case count
* top zero-retrieval queries for RAG retrieval events
* most frequently retrieved filenames

This monitoring capability is currently terminal-based and backend-side only. It provides a lightweight operational view of the system without introducing dashboards or external monitoring infrastructure. The presentation layer may be extended later, but the current implementation is intentionally a local CLI workflow.

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

## Monitoring Verification

To verify the observability and metrics flow end to end:

1. Start the backend with `uvicorn`
2. Send messages from the frontend or CLI
3. Confirm `logs/backend.log` is being written
4. Run:

```bash
python3 -m observability.metrics_summary logs/backend.log
```

This should produce a readable request-level and retrieval-level metrics summary from actual backend log output.

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

- Backend observability with automatic file logging and a terminal-based metrics summary workflow  

- System design emphasizes isolation, deterministic formatting, routing control, and extensibility  

---

# 📌 License

This project is **not open source**.
All rights reserved.
Unauthorized copying, modification, or distribution is not permitted.
