from langchain_openai import ChatOpenAI
from openai import APIConnectionError, APIError, APITimeoutError, AsyncOpenAI, RateLimitError

from core.config import MODELS_WITH_FALLBACK, settings

_MODEL_ERRORS = (APIError, APIConnectionError, RateLimitError, APITimeoutError)


def build_chat_model(model: str | None = None) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    return ChatOpenAI(
        model=model or settings.primary_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )


async def chat_completions_with_fallback(client: AsyncOpenAI, **kwargs):
    models = MODELS_WITH_FALLBACK
    last_error: Exception | None = None

    for index, model in enumerate(models):
        try:
            return await client.chat.completions.create(model=model, **kwargs)
        except _MODEL_ERRORS as exc:
            last_error = exc
            if index < len(models) - 1:
                print(
                    f"[LLM] Model {model} tidak tersedia ({exc}), "
                    f"mencoba fallback: {models[index + 1]}"
                )
                continue
            raise

    if last_error:
        raise last_error
    raise RuntimeError("No models configured for fallback")
