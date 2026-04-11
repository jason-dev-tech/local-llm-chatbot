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

# 🧱 Architecture Overview

The implemented system is a small full-stack AI application with a clear split between UI, API orchestration, local persistence, retrieval infrastructure, and runtime validation.

* **React frontend** provides the chat UI, streaming response rendering, session management, and browser-side API calls.
* **FastAPI backend** handles routing, chat orchestration, RAG execution, tool execution, citation formatting, and observability events.
* **SQLite** stores sessions and message history for the current multi-session chat experience.
* **Chroma** stores embedded document chunks for retrieval over the local knowledge base.
* **Local or OpenAI-compatible model endpoint** supplies both chat generation and embeddings through the configured API base URL.
* **Evaluation and operational checks** provide deterministic eval scripts, backend self-checks, and readiness validation for runtime dependencies.

The architecture is intentionally modular rather than agentic-by-default: retrieval, tools, routing, response formatting, and operational validation are separated into distinct backend layers.

---

# 🔄 Request Flow

## Normal chat

* The frontend sends a chat request to the FastAPI backend.
* The backend checks for explicit tool intent and retrieval-oriented routing.
* If the request is treated as normal chat, the backend sends the prompt to the configured chat model endpoint and returns the final response.

## RAG requests

* The backend routes knowledge-oriented queries into the retrieval path.
* The query is embedded, matched against Chroma, reranked, and converted into prompt context.
* The backend generates the answer from retrieved context, then applies inline citations and source attribution.
* If retrieval evidence is too weak, the backend returns the existing insufficient-evidence response instead of a confident unsupported answer.

## Tool-routed requests

* Explicit summarize, rewrite, or extraction requests are routed into the tool layer first.
* Tools run in isolated backend code paths so they do not interfere with RAG citation formatting.
* For supported cases, deterministic summarize-then-rewrite chaining remains available as a lightweight controlled composition path.

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

## 🛡 Grounding & Safety

* Evidence-aware backend guardrails are applied to retrieval-backed answers
* When retrieval does not provide sufficient support, the system returns a concise insufficient-evidence fallback instead of a confident unsupported RAG answer
* Guardrails rely on lightweight retrieval signals such as rerank score and meaningful query-term overlap rather than a separate scoring service
* Successful RAG flows keep the existing citation and attribution behavior unchanged

## 🛠 Tooling Layer

* Registry-based tool abstraction for name-based tool resolution
* `summarize_text` tool for direct text summarization
* `rewrite_text` tool for controlled rewriting that preserves meaning while improving clarity
* `extract_entities` tool for structured query analysis with JSON output
* Deterministic multi-step tool chaining for a lightweight agent-style summarize-then-rewrite flow
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
* Behavioral tool evals for summarize / rewrite execution, including deterministic summarize-then-rewrite chaining
* JSON-aware tool evals for structured extraction output
* Frontend validation completed for summarize, rewrite, normal chat, and RAG flows

## 📈 Observability / Monitoring

* Structured backend observability logs emitted during request handling
* Automatic file-based backend log generation for real application runs
* Terminal-based Metrics Aggregation Layer for request, outcome, session, query, and retrieval summaries
* Current monitoring workflow is backend-side only and is not exposed in the frontend

## 🧾 Response Modes

The backend classifies response events into a small set of explicit modes for observability:

* `chat`
* `tool`
* `rag_response`
* `insufficient_evidence`

These modes are used in backend logs to distinguish normal chat responses, direct tool execution, retrieval-backed responses, and guarded fallback behavior.

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
│   ├── run_tool_evals.py
│   ├── run_guardrail_evals.py
│   └── run_answer_quality_evals.py
├── observability/
│   └── metrics_summary.py
├── operational/
│   ├── runtime_checks.py
│   └── self_check.py
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

## Deployment / Runtime Model

The current system supports two practical runtime modes:

* **Local development**: run FastAPI and the Vite frontend directly, with the backend calling a locally running OpenAI-compatible model endpoint.
* **Docker deployment**: run backend and frontend containers locally with mounted `data/`, `logs/`, and `knowledge/` directories.

In both modes, the application still depends on an external chat + embedding provider. That provider may be LM Studio on the same machine, or another OpenAI-compatible hosted endpoint.

Operationally, the runtime model distinguishes:

* **Liveness** via `GET /health`: the backend process is up.
* **Readiness** via `GET /ready`: the backend is usable, including database, storage, chat endpoint, and embedding endpoint availability.

For Docker, the frontend API base URL is runtime-configurable through `runtime-config.js`, so the browser-facing backend URL can be changed at container startup without rebuilding the frontend image.

## Docker Deployment

For local Docker deployment, the local model server must already be running on the host machine, such as LM Studio or another OpenAI-compatible endpoint.

Required environment variables for the backend container:

* `OPENAI_API_KEY`
* `MODEL_NAME`
* `EMBEDDING_MODEL`
* `DB_PATH`
* `KNOWLEDGE_DIR`
* `CHROMA_PERSIST_DIR`

Optional tuning parameters for chunking behavior:

* `CHUNK_SIZE`
* `CHUNK_OVERLAP`

The Docker-safe backend model endpoint is:

```text
OPENAI_BASE_URL=http://host.docker.internal:1234/v1
```

The backend container still listens on port `8000` internally, but the included Compose setup maps it to host port `8001` to avoid conflicts with an already-running local backend.

Start the Docker deployment from the project root:

```bash
docker compose up --build
```

Example local access URLs:

* Frontend: `http://localhost:3000`
* Backend API: `http://127.0.0.1:8001`
* Backend health check: `http://127.0.0.1:8001/health`

The frontend API base URL is now runtime-configurable. In Docker, the frontend container writes a small `runtime-config.js` file at startup from `API_BASE_URL`, so you can change the browser-facing backend URL without rebuilding the frontend image.

### Health and readiness

* `GET /health` is a lightweight liveness-style endpoint that reports whether the backend process is up.
* `GET /ready` is a stricter readiness endpoint that now includes database, local storage, chat endpoint readiness, and embedding endpoint readiness.
* The backend depends on an external OpenAI-compatible provider for both chat generation and embeddings, so a running API process alone is not enough to consider the system ready.
* If the configured chat model or embedding model is unreachable or unusable, `/ready` returns `503` even when `/health` still returns `200`.
* In Docker Compose, the backend container healthcheck now uses `GET /ready`, so the container can be running but still report as unhealthy when the external model provider is unavailable.

The Compose setup mounts these local directories into the backend container for persistence and retrieval data access:

* `data/`
* `logs/`
* `knowledge/`

## Backend Self-Check

For a lightweight backend smoke check covering runtime configuration, key imports, database access, and local directory readiness, run:

```bash
python -m operational.self_check
```

This is intended for local and container verification and exits with a non-zero status if the backend runtime is not ready.

The self-check now includes lightweight live probes against the configured chat model and embedding model, so it can fail when the backend configuration is valid but the external provider is not actually usable.

## Document Ingestion and Verification

The local knowledge pipeline currently supports these file types under `knowledge/`:

* `.txt`
* `.md`
* `.pdf`
* `.json`

To ingest local knowledge files into the vector store, run:

```bash
python -m rag.ingest
```

## Ingestion Observability

The ingestion pipeline now outputs source-level summaries during ingestion. Each supported source type such as `txt`, `pdf`, `json`, and `json_api` reports the number of documents loaded and the number of chunks generated. This provides deterministic verification of ingestion, easier debugging of data pipelines, and better visibility into multi-source RAG systems.

Example output:

```text
[ingest] source=test_api.json source_type=json_api documents=2
[ingest] source=test_api.json source_type=json_api chunks=2
```

### Structured JSON ingestion

The ingestion pipeline also supports lightweight structured data ingestion without changing the retrieval architecture.

JSON files:

* Place `.json` files under `knowledge/`
* Root arrays are treated as multiple records
* Root objects use top-level `records`, `items`, or `results` arrays when present; otherwise the object is treated as a single record
* Records are normalized into deterministic line-oriented text before chunking and embedding

JSON API ingestion:

* Add sources to the JSON API manifest at `knowledge/api_sources.json`
* Run the same ingestion command: `python -m rag.ingest`
* Each listed endpoint is fetched, normalized into record text, and ingested through the existing chunking and embedding flow

Example manifest:

```json
[
  {
    "name": "sample_api",
    "url": "http://localhost:9000/data.json",
    "record_type": "sample_record"
  }
]
```

### Verification flow

1. Add or update files in `knowledge/`
2. Run `python -m rag.ingest`
3. Ask knowledge-based queries and verify citations and source attribution in the response

### Example verification queries

PDF-oriented query:

```text
What does the AI knowledge guide say about chunking?
```

Multi-document query:

```text
What do the knowledge files say about RAG, citations, and metadata?
```

### Expected verification signals

* retrieval-backed answers should include inline citations when supported by retrieved knowledge
* the final response should show source attribution for the retrieved documents
* multi-document queries may show more than one source in the attribution block when relevant

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

This command reads backend log output only. It is a terminal-based monitoring utility and is not currently exposed through the frontend.

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
* Summarize this text and then rewrite it more clearly: Retrieval-Augmented Generation combines retrieval with generation to improve grounding and answer quality.
* extract entities: Compare RAG in LangChain with Chroma and FastAPI using sample.txt and faq.txt

## Retrieval-Summary Queries

* Summarize what the knowledge base says about RAG
* Summarize the docs about retrieval and citations

---

# ✅ Evaluation

The AI system includes deterministic, dataset-driven evaluation for routing, tools, RAG response validation, insufficient-evidence guardrails, and basic answer quality checks over real backend responses.

Current evaluation coverage includes:

* routing evaluation
* tool evaluation
* retrieval evaluation
* RAG response validation for citations and sources
* guardrail evaluation for `insufficient_evidence` cases
* answer quality evaluation for groundedness, hallucination avoidance, and `response_mode`

These evaluations validate:

* routing correctness
* response_mode classification
* guardrail triggering behavior
* citation and source formatting behavior
* groundedness and unsupported-claim avoidance using simple `must_contain` / `must_not_contain` checks
* deterministic summarize-then-rewrite tool chaining behavior

Run the evaluation commands from the project root:

```bash
python -m evals.run_evals
python -m evals.run_retrieval_evals
python -m evals.run_routing_evals
python -m evals.run_tool_evals
python -m evals.run_guardrail_evals
python -m evals.run_answer_quality_evals
```

Current verified milestone:

* `tool evals`: **100%**
* `routing evals`: **100%**
* `chatbot evals`: **100%**

Verified coverage includes:

* Chatbot evaluation for RAG routing, inline citations, source labels, and multi-source behavior
* Routing evaluation for direct tool routing, heuristic routing, and LLM-assisted fallback
* Tool evaluation for summarize, rewrite, and structured extraction behavior
* Guardrail evaluation for `insufficient_evidence` versus normal RAG responses
* Answer quality evaluation for real backend outputs across `rag_response`, `insufficient_evidence`, and `chat`
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
