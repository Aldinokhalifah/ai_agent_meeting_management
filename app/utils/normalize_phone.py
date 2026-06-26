import re

_ALLOWED_CHARS_RE = re.compile(r"^[\d+\-\s()]+$")
_NON_DIGIT_RE = re.compile(r"\D")


def normalize_indonesia_whatsapp(value) -> str | None:
    """Normalisasi nomor WhatsApp Indonesia ke format 62xxxx."""
    if value is None:
        return None

    raw = str(value).strip()
    if raw == "":
        return None

    if not _ALLOWED_CHARS_RE.match(raw):
        return None

    digits = _NON_DIGIT_RE.sub("", raw)

    if len(digits) < 9 or len(digits) > 15:
        return None

    if digits.startswith("62"):
        return digits
    if digits.startswith("0"):
        return f"62{digits[1:]}"
    if digits.startswith("8"):
        return f"62{digits}"

    return None