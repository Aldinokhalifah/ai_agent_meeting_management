def meeting_title_match_summary(meetings: list) -> list:
    return [
        {
            "id": m["id"],
            "title": m["title"],
            "scheduled_at": str(m["scheduled_at"]),
            "status": m["status"],
        }
        for m in meetings
    ]