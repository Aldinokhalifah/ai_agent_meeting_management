import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


def _models_with_fallback(primary: str, fallback: str) -> tuple[str, ...]:
    if fallback and fallback != primary:
        return (primary, fallback)
    return (primary,)


@dataclass(frozen=True)
class Settings:
    database_url: str | None
    openrouter_api_key: str | None
    openrouter_base_url: str
    primary_model: str
    fallback_model: str
    app_host: str
    app_port: int
    whatsapp_api_token: str | None      # ← tambah
    whatsapp_api_url: str    

    @property
    def openrouter_model(self) -> str:
        return self.primary_model

    @property
    def models_with_fallback(self) -> tuple[str, ...]:
        return _models_with_fallback(self.primary_model, self.fallback_model)


def _build_settings() -> Settings:
    primary = (
        os.getenv("PRIMARY_MODEL")
        or os.getenv("OPENROUTER_MODEL")
        or "openai/gpt-oss-120b:free"
    )
    fallback = os.getenv("FALLBACK_MODEL") or "meta-llama/llama-3.3-70b-instruct:free"

    return Settings(
        database_url=os.getenv("DATABASE_URL"),
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv(
            "OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"
        ),
        primary_model=primary,
        fallback_model=fallback,
        app_host=os.getenv("APP_HOST", "0.0.0.0"),
        app_port=int(os.getenv("APP_PORT", 8000)),
        whatsapp_api_token=os.getenv("WHATSAPP_API_TOKEN"),          # ← tambah
        whatsapp_api_url=os.getenv("WHATSAPP_API_URL", "https://api.fonnte.com/send"),  # ← tambah
    )


settings = _build_settings()

DATABASE_URL = settings.database_url
OPENROUTER_API_KEY = settings.openrouter_api_key
OPENROUTER_BASE_URL = settings.openrouter_base_url
OPENROUTER_MODEL = settings.primary_model
PRIMARY_MODEL = settings.primary_model
FALLBACK_MODEL = settings.fallback_model
MODELS_WITH_FALLBACK = settings.models_with_fallback
APP_HOST = settings.app_host
APP_PORT = settings.app_port
WHATSAPP_API_TOKEN = settings.whatsapp_api_token   # ← tambah
WHATSAPP_API_URL = settings.whatsapp_api_url 
