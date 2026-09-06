from typing import Any

from langchain_openai import ChatOpenAI
from openai import (
    APIConnectionError,
    APIError,
    APITimeoutError,
    AsyncOpenAI,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    OpenAI,
    PermissionDeniedError,
    RateLimitError,
)

from core.config import MODELS_WITH_FALLBACK, settings

_MODEL_ERRORS = (
    APIError,
    APIConnectionError,
    RateLimitError,
    APITimeoutError,
    AuthenticationError,
    BadRequestError,
    InternalServerError,
    NotFoundError,
    PermissionDeniedError,
    ValueError,
)

# Error ini milik API key, bukan model — langsung ganti key.
_KEY_LEVEL_STATUS = {401, 402, 403}

_STATUS_MESSAGES = {
    400: "Format pesan atau permintaanmu tidak dapat diproses oleh AI. Coba ubah atau sederhanakan kalimatmu.",
    401: "Layanan AI mengalami kendala autentikasi sistem. Silakan hubungi admin.",
    402: "Layanan AI sedang mencapai batas kuota penggunaan harian/bulanan. Silakan hubungi admin.",
    403: "Akses ke fitur AI sedang dibatasi untuk akun ini. Silakan coba lagi nanti.",
    404: "Model AI yang diminta sedang tidak tersedia. Silakan coba beberapa saat lagi.",
    408: "Waktu tunggu respon AI habis karena koneksi lambat. Silakan coba kirim ulang pesanmu.",
    429: "Layanan AI sedang sangat padat. Mohon tunggu sebentar lalu coba kirim pesanmu lagi.",
    500: "Terjadi gangguan internal pada server AI. Sistem telah mencoba opsi cadangan namun masih gagal. Coba lagi nanti.",
    502: "Koneksi ke server AI terputus di tengah jalan. Silakan coba lagi beberapa saat lagi.",
    503: "Layanan AI sedang dalam pemeliharaan atau tidak dapat dijangkau. Coba lagi dalam beberapa menit.",
    504: "AI membutuhkan waktu terlalu lama untuk merespon. Coba pecah pertanyaanmu menjadi lebih sederhana.",
    529: "Sistem AI sedang mengalami lonjakan pengguna yang sangat tinggi. Mohon coba lagi secara berkala.",
}


class LLMUnavailableError(Exception):
    """Dipakai untuk menegembalikan pesan error yang berdasarkan status code dan message

    Args:
        status_code: status kode untuk error yang diterima
        message: pesan error yang diterima
    """

    def __init__(
        self,
        status_code: int,
        message: str,
        *,
        attempts: list[dict[str, Any]] | None = None,
        original: Exception | None = None,
    ):
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.attempts = attempts or []
        self.original = original

    @property
    def http_detail(self) -> dict[str, Any]:
        return {
            "error": self.message,
            "status": self.status_code,
            "attempts": self.attempts,
        }


def _status_code(exc: Exception) -> int:
    code = getattr(exc, "status_code", None)
    if isinstance(code, int):
        return code
    if isinstance(exc, RateLimitError):
        return 429
    if isinstance(exc, AuthenticationError):
        return 401
    if isinstance(exc, PermissionDeniedError):
        return 403
    if isinstance(exc, NotFoundError):
        return 404
    if isinstance(exc, BadRequestError):
        return 400
    if isinstance(exc, InternalServerError):
        return 500
    if isinstance(exc, APITimeoutError):
        return 504
    if isinstance(exc, APIConnectionError):
        return 503
    return 500


def _user_message(status_code: int) -> str:
    return _STATUS_MESSAGES.get(
        status_code,
        f"Gagal memanggil model AI (HTTP {status_code}). Semua model dan API key sudah dicoba.",
    )


def _error_text(exc: Exception) -> str:
    return str(exc)[:400]


def _api_keys(client: Any) -> tuple[str, ...]:
    keys = settings.openrouter_api_keys
    if keys:
        return keys
    client_key = getattr(client, "api_key", None)
    if client_key:
        return (str(client_key),)
    return ()


def _exhausted(last_error: Exception | None, attempts: list[dict[str, Any]]) -> LLMUnavailableError:
    if last_error is None:
        return LLMUnavailableError(
            503,
            "Tidak ada API key atau model OpenRouter yang dikonfigurasi.",
            attempts=attempts,
        )
    status = _status_code(last_error)
    return LLMUnavailableError(
        status,
        _user_message(status),
        attempts=attempts,
        original=last_error,
    )


def _log_fallback(key_index: int, model: str, exc: Exception, nxt: str | None) -> None:
    suffix = f" mencoba fallback: {nxt}" if nxt else " tidak ada fallback tersisa"
    print(
        f"[LLM] Gagal key#{key_index + 1} model={model} "
        f"(HTTP {_status_code(exc)}: {_error_text(exc)}).{suffix}"
    )


def _next_fallback_label(
    key_index: int,
    model_index: int,
    keys: tuple[str, ...],
    models: tuple[str, ...],
    skip_rest_models: bool,
) -> str | None:
    if not skip_rest_models and model_index + 1 < len(models):
        return f"key#{key_index + 1} model={models[model_index + 1]}"
    if key_index + 1 < len(keys):
        return f"key#{key_index + 2} model={models[0]}"
    return None


def _record_failure(
    attempts: list[dict[str, Any]],
    key_index: int,
    model: str,
    exc: Exception,
    nxt: str | None,
) -> None:
    attempts.append(
        {
            "api_key": key_index + 1,
            "model": model,
            "status": _status_code(exc),
            "error": _error_text(exc),
        }
    )
    _log_fallback(key_index, model, exc, nxt)


def build_chat_model(model: str | None = None) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise ValueError("OPENROUTER_API_KEY is not set")

    return ChatOpenAI(
        model=model or settings.primary_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0.2,
    )


def _run_fallback_sync(client: OpenAI, **kwargs):
    keys = _api_keys(client)
    models = MODELS_WITH_FALLBACK
    if not keys or not models:
        raise _exhausted(None, [])

    last_error: Exception | None = None
    attempts: list[dict[str, Any]] = []

    for key_index, api_key in enumerate(keys):
        keyed = client.with_options(api_key=api_key)
        for model_index, model in enumerate(models):
            try:
                res = keyed.chat.completions.create(model=model, **kwargs)
                # Validasi struktur respons sebelum dikembalikan
                if not res or getattr(res, "choices", None) is None or len(res.choices) == 0:
                    raise ValueError(f"Respon model {model} tidak valid (choices is None/empty).")
                return res
            except _MODEL_ERRORS as exc:
                last_error = exc
                skip_rest = _status_code(exc) in _KEY_LEVEL_STATUS
                nxt = _next_fallback_label(key_index, model_index, keys, models, skip_rest)
                _record_failure(attempts, key_index, model, exc, nxt)
                if skip_rest:
                    break

    raise _exhausted(last_error, attempts)


async def chat_completions_with_fallback(client: AsyncOpenAI, **kwargs):
    keys = _api_keys(client)
    models = MODELS_WITH_FALLBACK
    if not keys or not models:
        raise _exhausted(None, [])

    last_error: Exception | None = None
    attempts: list[dict[str, Any]] = []

    for key_index, api_key in enumerate(keys):
        keyed = client.with_options(api_key=api_key)
        for model_index, model in enumerate(models):
            try:
                res = await keyed.chat.completions.create(model=model, **kwargs)
                # Validasi struktur respons sebelum dikembalikan
                if not res or getattr(res, "choices", None) is None or len(res.choices) == 0:
                    raise ValueError(f"Respon model {model} tidak valid (choices is None/empty).")
                return res
            except _MODEL_ERRORS as exc:
                last_error = exc
                skip_rest = _status_code(exc) in _KEY_LEVEL_STATUS
                nxt = _next_fallback_label(key_index, model_index, keys, models, skip_rest)
                _record_failure(attempts, key_index, model, exc, nxt)
                if skip_rest:
                    break

    raise _exhausted(last_error, attempts)


def chat_completions_with_fallback_sync(client: OpenAI, **kwargs):
    return _run_fallback_sync(client, **kwargs)
