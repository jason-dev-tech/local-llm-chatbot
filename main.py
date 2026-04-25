import json
import logging
import re
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from config import KNOWLEDGE_DIR
from db import init_db, get_all_sessions_with_titles, session_exists, get_session_messages, save_message
from operational.runtime_checks import run_backend_smoke_checks, validate_runtime_config
from rag.ingest import ingest_documents, run_ingestion
from rag.loaders import SUPPORTED_EXTENSIONS, load_file_documents
from chat_service import (
    create_new_session,
    rename_session,
    remove_session,
    send_message,
    send_message_and_stream,
)

LOG_DIR = Path("logs")
LOG_DIR.mkdir(exist_ok=True)
BACKEND_LOG_PATH = LOG_DIR / "backend.log"
STARTUP_LOGGER = logging.getLogger("chatbot.startup")
SAFE_FILENAME_PATTERN = re.compile(r"[^A-Za-z0-9._ -]+")
SESSION_UPLOAD_DIR = Path("data/session_uploads")

logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    force=True,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(BACKEND_LOG_PATH, encoding="utf-8"),
    ],
)

app = FastAPI(title="Local AI Chatbot API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class CreateSessionResponse(BaseModel):
    session_id: str
    title: str | None


class ChatRequest(BaseModel):
    session_id: str
    message: str


class ChatResponse(BaseModel):
    session_id: str
    reply: str


class ChatStreamRequest(BaseModel):
    session_id: str
    message: str


class RenameSessionRequest(BaseModel):
    title: str


def _extract_multipart_boundary(content_type: str) -> str | None:
    for part in content_type.split(";"):
        key, separator, value = part.strip().partition("=")
        if separator and key.lower() == "boundary":
            return value.strip().strip('"')
    return None


def _extract_disposition_filename(content_disposition: str) -> str | None:
    match = re.search(r'filename="([^"]*)"', content_disposition)
    if match:
        return match.group(1)

    match = re.search(r"filename=([^;]+)", content_disposition)
    if match:
        return match.group(1).strip().strip('"')

    return None


def _sanitize_upload_filename(filename: str) -> str:
    basename = Path(filename.replace("\\", "/")).name.strip()
    sanitized = SAFE_FILENAME_PATTERN.sub("_", basename).strip(" .")
    return sanitized


def _sanitize_path_segment(value: str) -> str:
    sanitized = SAFE_FILENAME_PATTERN.sub("_", value.strip()).strip(" .")
    return sanitized


def _extract_single_uploaded_file(body: bytes, boundary: str) -> tuple[str, bytes] | None:
    boundary_marker = f"--{boundary}".encode("utf-8")

    for raw_part in body.split(boundary_marker):
        part = raw_part.strip(b"\r\n")
        if not part or part == b"--":
            continue

        if part.endswith(b"--"):
            part = part[:-2].rstrip(b"\r\n")

        header_blob, separator, content = part.partition(b"\r\n\r\n")
        if not separator:
            continue

        headers = header_blob.decode("latin-1").split("\r\n")
        content_disposition = ""
        for header in headers:
            name, header_separator, value = header.partition(":")
            if header_separator and name.lower() == "content-disposition":
                content_disposition = value.strip()
                break

        filename = _extract_disposition_filename(content_disposition)
        if filename:
            return filename, content.rstrip(b"\r\n")

    return None


def _validate_supported_upload_filename(filename: str) -> None:
    suffix = Path(filename).suffix.lower()
    if suffix not in SUPPORTED_EXTENSIONS:
        supported = ", ".join(sorted(SUPPORTED_EXTENSIONS))
        raise HTTPException(status_code=400, detail=f"Unsupported file type. Supported types: {supported}")


@app.on_event("startup")
def startup_event():
    config_errors = validate_runtime_config()
    if config_errors:
        STARTUP_LOGGER.error(
            json.dumps(
                {
                    "stage": "startup_validation",
                    "status": "failed",
                    "errors": config_errors,
                },
                ensure_ascii=True,
                sort_keys=True,
            )
        )
        raise RuntimeError("Backend startup validation failed.")

    init_db()
    STARTUP_LOGGER.info(
        json.dumps(
            {
                "stage": "startup_validation",
                "status": "ok",
            },
            ensure_ascii=True,
            sort_keys=True,
        )
    )


@app.get("/")
def root():
    return {"message": "Local AI Chatbot API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/ready")
def ready():
    result = run_backend_smoke_checks()
    is_ready = result["ok"]
    payload = {
        "status": "ready" if is_ready else "not_ready",
        "checks": result["checks"],
        "config_errors": result["config_errors"],
        "check_details": {
            name: detail
            for name, detail in result.get("check_details", {}).items()
            if detail
        },
    }
    if is_ready:
        return payload

    return JSONResponse(status_code=503, content=payload)


@app.get("/sessions")
def list_sessions():
    sessions = get_all_sessions_with_titles()
    return [
        {
            "session_id": session_id,
            "title": title,
        }
        for session_id, title in sessions
    ]


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session_api():
    session_id = create_new_session()
    sessions = get_all_sessions_with_titles()

    matched_title = None
    for sid, title in sessions:
        if sid == session_id:
            matched_title = title
            break

    return {
        "session_id": session_id,
        "title": matched_title,
    }


@app.get("/sessions/{session_id}")
def get_session_detail_api(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    messages = get_session_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
    }


@app.get("/sessions/{session_id}/messages")
def get_session_messages_api(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    return get_session_messages(session_id)


@app.post("/chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    if not session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    if not request.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    reply = send_message(request.session_id, request.message)

    return {
        "session_id": request.session_id,
        "reply": reply,
    }


@app.post("/chat/stream")
def chat_stream_api(request: ChatStreamRequest):
    if not session_exists(request.session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    def event_stream():
        response_metadata = {}

        def update_response_metadata(metadata):
            response_metadata.update(
                {
                    key: value
                    for key, value in metadata.items()
                    if value is not None
                }
            )

        try:
            for token in send_message_and_stream(
                request.session_id,
                message,
                metadata_callback=update_response_metadata,
            ):
                yield json.dumps({
                    "type": "token",
                    "content": token,
                }) + "\n"

            yield json.dumps({"type": "done", **response_metadata}) + "\n"

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e),
            }) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )


@app.post("/knowledge/upload")
async def upload_knowledge_file_api(request: Request):
    content_type = request.headers.get("content-type", "")
    boundary = _extract_multipart_boundary(content_type)
    if not boundary:
        raise HTTPException(status_code=400, detail="Expected multipart file upload")

    uploaded_file = _extract_single_uploaded_file(await request.body(), boundary)
    if uploaded_file is None:
        raise HTTPException(status_code=400, detail="No file was uploaded")

    original_filename, file_content = uploaded_file
    filename = _sanitize_upload_filename(original_filename)
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    _validate_supported_upload_filename(filename)

    knowledge_path = Path(KNOWLEDGE_DIR).resolve()
    destination = (knowledge_path / filename).resolve()
    if knowledge_path not in destination.parents:
        raise HTTPException(status_code=400, detail="Invalid filename")

    knowledge_path.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(file_content)
    run_ingestion()

    return {
        "filename": filename,
        "status": "uploaded_and_indexed",
    }


@app.post("/sessions/{session_id}/attachments")
async def upload_session_attachment_api(session_id: str, request: Request):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    content_type = request.headers.get("content-type", "")
    boundary = _extract_multipart_boundary(content_type)
    if not boundary:
        raise HTTPException(status_code=400, detail="Expected multipart file upload")

    uploaded_file = _extract_single_uploaded_file(await request.body(), boundary)
    if uploaded_file is None:
        raise HTTPException(status_code=400, detail="No file was uploaded")

    original_filename, file_content = uploaded_file
    filename = _sanitize_upload_filename(original_filename)
    safe_session_id = _sanitize_path_segment(session_id)
    if not filename or not safe_session_id:
        raise HTTPException(status_code=400, detail="Invalid upload target")

    _validate_supported_upload_filename(filename)

    upload_root = SESSION_UPLOAD_DIR.resolve()
    session_path = (upload_root / safe_session_id).resolve()
    destination = (session_path / filename).resolve()
    if upload_root not in destination.parents or session_path not in destination.parents:
        raise HTTPException(status_code=400, detail="Invalid filename")

    session_path.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(file_content)

    documents = load_file_documents(destination)
    stored_chunk_count = ingest_documents(
        documents,
        extra_metadata={
            "session_id": session_id,
            "scope": "session",
        },
    )
    if not stored_chunk_count:
        raise HTTPException(status_code=400, detail="No indexable content found in uploaded file")

    save_message(session_id, "attachment", filename)

    return {
        "filename": filename,
        "session_id": session_id,
        "status": "uploaded_and_indexed",
    }


@app.patch("/sessions/{session_id}")
def rename_session_api(session_id: str, request: RenameSessionRequest):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    new_title = request.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Title cannot be empty")

    rename_session(session_id, new_title)

    return {
        "message": "Session renamed successfully",
        "session_id": session_id,
        "title": new_title,
    }


@app.delete("/sessions/{session_id}")
def delete_session_api(session_id: str):
    if not session_exists(session_id):
        raise HTTPException(status_code=404, detail="Session not found")

    deleted = remove_session(session_id)
    if not deleted:
        raise HTTPException(status_code=500, detail="Failed to delete session")

    return {
        "message": "Session deleted successfully",
        "session_id": session_id,
    }
