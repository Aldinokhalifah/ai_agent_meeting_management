from db.postgres import execute_query

def check_schedule_conflict(user_id, scheduled_at, end_time):
    conflict = execute_query(
        """
        SELECT DISTINCT u.name
        FROM meetings m
        JOIN meeting_participants mp
            ON m.id = mp.meeting_id
        JOIN users u
            ON mp.user_id = u.id
        WHERE mp.user_id = %s
        AND m.status NOT IN ('done', 'cancelled')
        AND (
            m.scheduled_at < %s
            AND m.end_time > %s
        )
        """,
        (
            user_id,
            end_time,
            scheduled_at
        ),
        fetch="all"
    )

    return [row["name"] for row in conflict]