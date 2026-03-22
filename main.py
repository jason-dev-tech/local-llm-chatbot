import json

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from db import init_db, get_all_sessions_with_titles, session_exists, get_session_messages
from chat_service import (
    create_new_session,
    rename_session,
    remove_session,
    send_message,
    send_message_and_stream,
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


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "Local AI Chatbot API is running"}


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
        try:
            for token in send_message_and_stream(request.session_id, message):
                yield json.dumps({
                    "type": "token",
                    "content": token,
                }) + "\n"

            yield json.dumps({
                "type": "done",
            }) + "\n"

        except Exception as e:
            yield json.dumps({
                "type": "error",
                "message": str(e),
            }) + "\n"

    return StreamingResponse(
        event_stream(),
        media_type="application/x-ndjson",
    )


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