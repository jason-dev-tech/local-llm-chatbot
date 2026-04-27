# Local-First AI Chatbot

A local-first AI chatbot with a FastAPI backend and a React + Vite frontend. The system supports multi-session chat, multi-source RAG over local documents, inline citations with source attribution, tool routing, and a LangGraph-orchestrated RAG workflow with validation and a controlled single retry.

## Project Purpose

This project is intended for technical demonstration purposes only.

The author does not use and does not intend to use this project for any commercial purposes.

It showcases AI engineering practices for building controlled, observable, and evaluation-driven LLM systems.

This repository is not intended for commercial use by the author.  
All rights are reserved.

## Architecture Overview

User requests flow through a backend routing layer that selects one of three paths:
- `chat`
- `rag`
- `tool`

The non-RAG paths remain procedural:
- Chat requests go through direct model interaction
- Tool requests go through a registry-based tool routing layer

The RAG path is orchestrated with LangGraph:
1. Retrieve relevant chunks from ChromaDB
2. Run an evidence check on retrieved results
3. Generate an answer using LangChain-based model integration
4. Validate the answer format and grounding behavior
5. Retry once if validation fails
6. Apply inline citations and source attribution formatting

## System Components

### Backend
- FastAPI API for sessions, chat, streaming, readiness, and session management
- Knowledge document upload endpoint for supported local RAG sources
- Procedural chat orchestration in the backend service layer
- Registry-based tool execution for summarization, rewriting, and entity extraction
- Runtime readiness and operational checks

### RAG
- Multi-source document loading from local knowledge files
- Document chunking and embedding generation
- ChromaDB-backed vector retrieval
- Metadata-aware filtering for explicit file references
- LangGraph workflow for retrieval, evidence check, generation, validation, and retry
- Inline citation insertion and structured source attribution

### Ingestion / Knowledge Pipeline
- Loads `.txt`, `.md`, `.json`, and `.pdf` documents from the local knowledge directory
- Supports uploading TXT, MD, JSON, and PDF documents from the sidebar UI
- Parses PDFs with PyPDF and expands structured JSON content into retrievable records
- Optionally loads JSON API sources from `knowledge/api_sources.json`
- Chunks content, generates embeddings, and stores vectors plus metadata in ChromaDB

### Frontend
- React UI for multi-session chat
- Sidebar knowledge upload UI for adding documents to the RAG knowledge base
- Streaming NDJSON response handling
- Markdown rendering for assistant responses
- Session create, rename, delete, and reload flows

### Observability / Monitoring
- Structured backend observability events are written to the terminal and `logs/backend.log`
- Events capture routing, retrieval, response mode, stage timing, total latency, and error details
- A metrics aggregation script summarizes route distribution, latency, retrieval behavior, and session activity

## Tech Stack

### Backend
- FastAPI
- Pydantic
- Uvicorn

### AI / RAG
- LangChain
- LangGraph
- OpenAI SDK
- ChromaDB
- PyPDF

### Frontend
- React
- TypeScript
- Vite
- React Markdown
- remark-gfm

### Storage
- SQLite
- ChromaDB

### Tooling
- Docker
- Docker Compose
- Nginx
- python-dotenv
- ESLint

## AI Engineering Highlights

- Multi-source RAG system over local documents and structured JSON content
- LangGraph-based workflow orchestration for the retrieval pipeline
- Deterministic validation and single controlled retry in the RAG path
- Tool routing architecture across chat, RAG, and direct tool execution
- Streaming responses across chat, RAG, and retrieval-based summarization for consistent real-time UX
- Client-side response time display for each assistant response
- Retrieval scope indicator for global knowledge versus session context
- Session-scoped document attachment for chat-specific retrieval context
- Local-first LLM integration through an OpenAI-compatible endpoint
- Script-based evaluation coverage for routing, retrieval behavior, citations, guardrails, and tools

This project does not bundle any models. Model usage is subject to the respective model licenses.

## Repository Layout

```text
.
├── main.py                  FastAPI application
├── chat_service.py          Chat, routing, and response orchestration
├── db.py                    SQLite persistence
├── llm.py                   Direct OpenAI SDK chat integration
├── llm_langchain.py         LangChain chat integration
├── routing/                 LLM-assisted routing helpers
├── rag/
│   ├── langgraph_workflow.py
│   ├── retrieval.py
│   ├── vector_store.py
│   ├── embedding.py
│   ├── loaders.py
│   ├── ingest.py
│   └── chunking.py
├── tools/                   Tool registry and tool implementations
├── evals/                   Script-based evaluation utilities
├── operational/             Runtime and readiness checks
├── knowledge/               Local source documents
└── frontend/                React + Vite frontend
```

## Development

### Backend

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Docker Compose

Start a local OpenAI-compatible model server before launching Docker Compose. Model files are not bundled with this project.

Configure the model endpoint with `.env` or environment variables, especially `OPENAI_BASE_URL`, `MODEL_NAME`, and `EMBEDDING_MODEL`.

```bash
docker compose up --build
```

Check backend readiness:

```bash
curl http://127.0.0.1:8001/ready
```

Backend in Docker Compose:

```text
http://127.0.0.1:8001
```

Frontend in Docker Compose:

```text
http://127.0.0.1:3000
```

Backend in local development:

```text
http://127.0.0.1:8000
```

## Configuration

Environment variables are loaded with `python-dotenv`. See [.env.example](./.env.example).

Key settings:
- `OPENAI_BASE_URL`
- `OPENAI_API_KEY`
- `MODEL_NAME`
- `EMBEDDING_MODEL`
- `DB_PATH`
- `KNOWLEDGE_DIR`
- `CHROMA_PERSIST_DIR`
- `RAG_COLLECTION_NAME`
- `CHUNK_SIZE`
- `CHUNK_OVERLAP`

## Ingestion / Knowledge Pipeline

The knowledge pipeline prepares local content for retrieval:
- Reads documents from [`knowledge/`](./knowledge/)
- Supports `.txt`, `.md`, `.json`, and `.pdf`
- Builds chunks and embeddings
- Stores vectors and metadata in ChromaDB

Documents can also be uploaded from the frontend sidebar. Uploaded TXT, MD, JSON, and PDF files are saved into the configured knowledge directory, indexed into ChromaDB, and become available for future RAG retrieval. This is knowledge ingestion for the shared knowledge base, not a one-time chat attachment.

Run ingestion:

```bash
python -m rag.ingest
```

Why it matters:
- Retrieval quality depends on the indexed knowledge base
- Metadata captured during ingestion supports source attribution and file-aware filtering

## Runtime Verification

The backend exposes runtime verification endpoints and local checks:
- `GET /health` confirms the API process is running
- `GET /ready` runs runtime checks for configuration, imports, database, Chroma directory, chat endpoint, and embedding endpoint
- `python -m operational.self_check` runs the same smoke checks from the command line

Run the self-check:

```bash
python -m operational.self_check
```

Verify document upload and retrieval:
1. Upload a supported document from the sidebar.
2. Ask a question related to the uploaded content.
3. Confirm the answer cites the uploaded source.

Why it matters:
- Confirms the model endpoint, embeddings, storage, and runtime dependencies are available before interactive use

## Observability / Monitoring

The backend emits structured observability events during request handling.
- Logs are written to [`logs/backend.log`](./logs/backend.log) when the backend runs
- Events include route selection, retrieved filenames, response mode, latency, and errors

Why it matters:
- Makes routing and retrieval behavior inspectable during development
- Helps diagnose slow requests, failed probes, and low-evidence RAG responses

## Metrics Aggregation Layer

The metrics aggregation layer summarizes observability logs into a readable report.

Run it against the backend log:

```bash
python -m observability.metrics_summary logs/backend.log
```

Why it matters:
- Aggregates latency, route distribution, response modes, tool usage, retrieval counts, and session/query patterns
- Includes route decision, retrieval, LLM generation, and total request latency summaries when available
- Provides a lightweight operations view without adding external monitoring infrastructure

## Evaluation

This repository uses script-based evaluation rather than a formal test framework.

Examples:

```bash
python evals/run_evals.py
python evals/run_routing_evals.py
python evals/run_retrieval_evals.py
python evals/run_rag_response_evals.py
python evals/run_tool_evals.py
python evals/run_guardrail_evals.py
python evals/run_answer_quality_evals.py
```

## Limitations

- No formal testing framework is implemented; `pytest`, `jest`, and similar frameworks are not present
- Evaluation is script-based and is not CI-integrated yet
- The system is local-first and not set up for cloud deployment
- Document ingestion is limited to the formats implemented in the repository, including PDF support via PyPDF

## License / Usage

This project is not open source.

All rights are reserved. No permission is granted to anyone to use, copy, modify, distribute, or use this project for commercial purposes.
