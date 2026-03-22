from pydantic import BaseModel
from typing import Optional


class SessionItem(BaseModel):
    session_id: str
    title: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CreateSessionRequest(BaseModel):
    session_id: str
    title: Optional[str] = None


class RenameSessionRequest(BaseModel):
    title: str


class MessageItem(BaseModel):
    id: int
    role: str
    content: str
    created_at: Optional[str] = None


class ChatStreamRequest(BaseModel):
    session_id: str
    message: str