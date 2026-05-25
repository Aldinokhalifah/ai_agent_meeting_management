from db.postgres import execute_query

def check_room_available(location, scheduled_at, end_time, exclude_meeting_id=None):
    query = """
        SELECT id, title
        FROM meetings
        WHERE location = %s
        AND status NOT IN ('done', 'cancelled')
        AND scheduled_at < %s
        AND end_time > %s
    """

    params = [location, end_time, scheduled_at]

    if exclude_meeting_id:
        query += " AND id <> %s"
        params.append(exclude_meeting_id)

    result = execute_query(query, tuple(params), fetch="all") or []
    return len(result) > 0