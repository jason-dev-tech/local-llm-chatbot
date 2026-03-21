from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from chat_service import create_new_chat_session, send_user_message
from db import (
    init_db,
    list_sessions,
    get_session,
    get_session_messages,
    update_session_title,
    delete_session,
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
    session_id: int
    title: str


class ChatRequest(BaseModel):
    session_id: int
    message: str


class ChatResponse(BaseModel):
    session_id: int
    reply: str


class RenameSessionRequest(BaseModel):
    title: str


@app.on_event("startup")
def startup_event():
    init_db()


@app.get("/")
def root():
    return {"message": "Local AI Chatbot API is running"}


@app.get("/sessions")
def get_sessions():
    return {"sessions": list_sessions()}


@app.post("/sessions", response_model=CreateSessionResponse)
def create_session_api():
    session_id = create_new_chat_session()
    session = get_session(session_id)
    return {
        "session_id": session["id"],
        "title": session["title"],
    }


@app.get("/sessions/{session_id}")
def get_session_api(session_id: int):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    messages = get_session_messages(session_id)
    return {
        "session": session,
        "messages": messages,
    }


@app.post("/chat", response_model=ChatResponse)
def chat_api(request: ChatRequest):
    session = get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    reply = send_user_message(request.session_id, request.message)
    return {
        "session_id": request.session_id,
        "reply": reply,
    }


@app.patch("/sessions/{session_id}")
def rename_session_api(session_id: int, request: RenameSessionRequest):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    update_session_title(session_id, request.title.strip())
    updated_session = get_session(session_id)
    return {"session": updated_session}


@app.delete("/sessions/{session_id}")
def delete_session_api(session_id: int):
    session = get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    delete_session(session_id)
    return {"message": "Session deleted"}