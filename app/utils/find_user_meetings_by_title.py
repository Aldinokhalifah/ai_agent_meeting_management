from db.postgres import execute_query

def find_user_meetings_by_title(user_id: str, title: str) -> list:
    return execute_query(
        """
        SELECT m.id, m.title, m.description, m.scheduled_at, m.end_time,
            m.location, m.status, m.created_by
        FROM meetings m
        JOIN meeting_participants mp ON m.id = mp.meeting_id
        WHERE mp.user_id = %s AND LOWER(m.title) = LOWER(%s)
        ORDER BY m.scheduled_at DESC
        """,
        (user_id, title),
    )