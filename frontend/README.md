# Frontend

React + TypeScript frontend for the local-first AI chatbot. It provides the chat interface, session management, streaming response rendering, and Markdown display for responses returned by the FastAPI backend.

## Project Purpose

This project is intended for technical demonstration purposes only.

The author does not use and does not intend to use this project for any commercial purposes.

It showcases AI engineering practices for building controlled, observable, and evaluation-driven LLM systems.

This repository is not intended for commercial use by the author.  
All rights are reserved.

## Architecture Overview

The frontend is responsible for:
- Fetching sessions and message history from the backend
- Sending chat requests to the backend
- Handling NDJSON streaming responses
- Uploading selected knowledge documents from the sidebar
- Rendering assistant output with Markdown support

Routing, retrieval, validation, retry behavior, citations, and source attribution all remain backend responsibilities.

## Tech Stack

### Frontend
- React
- TypeScript
- Vite
- React Markdown
- remark-gfm

### Tooling
- ESLint
- Docker
- Nginx

## AI Engineering Highlights

- Streaming chat UI for backend-generated responses
- UI support for source attribution sections returned by the backend
- Sidebar knowledge upload UI with selected-file, uploading, success, and error states
- Session-based chat workflow with persistent backend storage
- Frontend remains thin while AI orchestration stays in backend services

## Development

Install dependencies:

```bash
npm install
```

Run the development server:

```bash
npm run dev
```

Default local URL:

```text
http://localhost:5173
```

## Backend Dependency

The frontend depends on the backend API.

Local development backend default:

```text
http://127.0.0.1:8000
```

Docker Compose frontend target:

```text
http://127.0.0.1:8001
```

This can be overridden with `VITE_API_BASE_URL` or runtime config exposed through [`public/runtime-config.js`](./public/runtime-config.js).

## Knowledge Upload

The sidebar includes a minimal knowledge document upload control. The frontend sends the selected file to `POST /knowledge/upload` as multipart form data using the existing backend API.

Upload state is limited to the selected filename plus concise uploading, success, and error messages. Chat streaming behavior is unchanged.

## Docker

The production image builds the Vite app and serves the static output with Nginx.

## Runtime Verification

The frontend does not implement its own health system, but it depends on the backend readiness flow.
- The UI calls the backend `/ready` endpoint before sending requests
- Readiness failures are surfaced as user-facing error states

Why it matters:
- Prevents chat attempts when the backend or model endpoint is unavailable

## Observability / Monitoring

Observability is backend-driven.
- The frontend renders streaming output and source attribution returned by the API
- Monitoring, structured logs, and metrics aggregation remain backend concerns

Why it matters:
- Keeps frontend logic thin while preserving visibility into routing, retrieval, and response behavior through backend logs

## Limitations

- No frontend test framework is implemented
- The frontend does not perform AI orchestration directly; it depends on backend routing and RAG behavior
- Deployment is local/container-oriented rather than cloud-oriented

## License / Usage

This project is not open source.

All rights are reserved. No permission is granted to anyone to use, copy, modify, distribute, or use this project for commercial purposes.
