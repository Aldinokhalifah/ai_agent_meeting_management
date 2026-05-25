from datetime import datetime

def parse_datetime(value: str) -> datetime:
    """Konversi berbagai format datetime ke datetime object"""
    if not value:
        raise ValueError("datetime tidak boleh kosong")

    value = value.strip().replace("Z", "+00:00")

    # Coba ISO 8601 dulu
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        pass

    # Coba beberapa format umum tanpa timezone
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue

    raise ValueError(f"Format datetime tidak valid: {value}")