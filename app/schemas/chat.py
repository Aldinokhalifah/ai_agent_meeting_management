from pydantic import BaseModel
from typing import Optional, List

class Message(BaseModel):
    role: str  # "user" | "assistant" | "tool"
    content: str

class ChatRequest(BaseModel):
    message: str
    user_id: str
    conversation_history: Optional[List[Message]] = []

class ChatResponse(BaseModel):
    response: str
    actions_taken: Optional[List[str]] = []