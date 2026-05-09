from fastapi import APIRouter, HTTPException

from schemas.chat import ChatRequest, ChatResponse
from services.llm import build_chat_model

router = APIRouter()


@router.get("/health")
def health_check() -> dict[str, str]:
    return {
            "status": "ok",
            "message": "Server AI Agent sedang berjalan"
        }


@router.post("/chat", response_model=ChatResponse)
def chat(payload: ChatRequest) -> ChatResponse:
    try:
        model = build_chat_model()
        response = model.invoke(payload.message)
        return ChatResponse(answer=response.content)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
