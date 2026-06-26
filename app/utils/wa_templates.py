from datetime import datetime

MAX_NOTE_CHARS = 3500

_DAY_NAMES = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu", "Minggu"]
_MONTH_NAMES = [
    "Januari", "Februari", "Maret", "April", "Mei", "Juni",
    "Juli", "Agustus", "September", "Oktober", "November", "Desember",
]


def _as_datetime(value) -> datetime:
    """Terima datetime object (dari psycopg2) atau ISO string."""
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value))


def format_date(value) -> str:
    d = _as_datetime(value)
    return f"{_DAY_NAMES[d.weekday()]}, {d.day} {_MONTH_NAMES[d.month - 1]} {d.year}"


def format_time(value) -> str:
    d = _as_datetime(value)
    return f"{d.hour:02d}:{d.minute:02d}"


def invitation_message(recipient_name, meeting_title, scheduled_at, end_time, location, host_name) -> str:
    time_range = (
        f"{format_time(scheduled_at)} – {format_time(end_time)}"
        if end_time
        else format_time(scheduled_at)
    )
    lines = [
        f"Halo {recipient_name},",
        "",
        f"Anda diundang ke pertemuan: *{meeting_title}*",
        f"📅 {format_date(scheduled_at)}",
        f"⏰ {time_range}",
    ]
    if location:
        lines.append(f"📍 {location}")
    lines.append(f"👤 Host: {host_name}")
    lines += ["", "Sampai jumpa di meeting."]
    return "\n".join(lines)


def meeting_summary_message(recipient_name, meeting_title, scheduled_at, location, ai_summary, note_text, my_action_items) -> str:
    lines = [
        f"Halo {recipient_name},",
        "",
        f"Pertemuan *{meeting_title}* telah selesai.",
        f"📅 {format_date(scheduled_at)}",
    ]
    if location:
        lines.append(f"📍 {location}")
    lines.append("")

    if ai_summary:
        lines.append("*Ringkasan AI:*")
        lines.append(ai_summary.strip())
        lines.append("")

    if note_text:
        trimmed = note_text.strip()
        if len(trimmed) > MAX_NOTE_CHARS:
            body = trimmed[:MAX_NOTE_CHARS] + "…\n_(notulen dipotong; lihat lengkap di aplikasi)_"
        else:
            body = trimmed
        lines.append("*Notulen:*")
        lines.append(body)
        lines.append("")

    if my_action_items:
        lines.append("*Action items untuk Anda:*")
        for i, item in enumerate(my_action_items):
            lines.append(f"{i + 1}. {item['description']}")
    else:
        lines.append("Tidak ada action item terbuka yang ditugaskan kepada Anda.")

    lines += ["", "— Meeting Management"]
    return "\n".join(lines)