from langchain_openai import ChatOpenAI

from app.core.config import settings


def build_chat_model() -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )
