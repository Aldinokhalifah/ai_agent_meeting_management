from db.postgres import execute_query
from utils.find_user_meetings_by_title import find_user_meetings_by_title
from utils.check_room_available import check_room_available
from utils.meeting_title_match_summary import meeting_title_match_summary
from utils.check_schedule_conflict import check_schedule_conflict
from utils.parse_datetime import parse_datetime
from datetime import datetime
from services.waService import send_invitation_whatsapp

CONTINUATION_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_continuation_meeting",
            "description": "Membuat meeting lanjutan. Gunakan tool ini ketika user ingin membuat atau menjadwalkan meeting lanjutan dari meeting sebelumnya.",
            "parameters": {
                "type": "object",
                "properties": {
                    "source_meeting_id":{
                        "type": "string",
                        "description": "ID meeting dari meeting sebelumnya"
                    },
                    "title": {
                        "type": "string",
                        "description": "Judul meeting"
                    },
                    "source_meeting_title": {
                        "type": "string",
                        "description": "Judul meeting dari meeting sebelumnya, Dipakai jika source_meeting_id tidak tersedia."
                    },
                    "scheduled_at": {
                        "type": "string",
                        "description": "Waktu mulai meeting dalam format ISO 8601. Contoh: 2025-05-01T09:00:00"
                    },
                    "end_time": {
                        "type": "string",
                        "description": "Waktu selesai meeting dalam format ISO 8601, waktu selesai harus lebih dari waktu mulai meeting"
                    },
                    "location": {
                        "type": "string",
                        "description": "Lokasi meeting. Pilihan: 'Ruang Rapat Lounge', 'Ruang Rapat Turbo', 'Ruang Rapat Piston', 'Ruang Rapat Kaca', 'Ruang Rapat Sales',  'Online'"
                    },
                    "description": {
                        "type": "string",
                        "description": "Deskripsi atau agenda meeting"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user yang membuat meeting (diisi otomatis)"
                    },
                    "participant_ids": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "user_id": {
                                    "type": "string",
                                    "description": "ID user peserta"
                                },
                                "role": {
                                    "type": "string",
                                    "enum": ["participant", "secretary"],
                                    "description": "Role peserta"
                                },
                                "access_level": {
                                    "type": "string",
                                    "enum": ["full", "summary_only", "none"],
                                    "description": "Hak akses ke meeting sebelumnya"
                                }
                            },
                            "required": ["user_id"]
                        },
                        "description": "Daftar peserta continuation meeting"
                    }
                    
                },
                "required": ["source_meeting_id", "title", "scheduled_at", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_previous_meeting",
            "description": "Mengambil meeting sebelumnya dari meeting lanjutan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "continuation_meeting_id":{
                        "type": "string",
                        "description": "ID meeting dari meeting yang lanjutan"
                    },
                    "continuation_meeting_title": {
                        "type": "string",
                        "description": "Judul meeting dari meeting lanjutan, Dipakai jika continuation_meeting_id tidak tersedia."
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user yang membuat meeting (diisi otomatis)"
                    },
                },
                "required": ["continuation_meeting_id", "user_id"]
            }
        }
    }
]

async def execute_continuation_tool(tool_name: str, args: dict):
    user_id = args.get("user_id")
    
    if tool_name == "create_continuation_meeting":
        return await _create_continuation_meeting(args, user_id)
    elif tool_name == "get_previous_meeting":
        return await _get_previous_meeting(args, user_id)
    else:
        raise ValueError(f"Meeting tool '{tool_name}' tidak ditemukan")

async def _create_continuation_meeting(args: dict, user_id: str):
    source_meeting_id = args.get("source_meeting_id")
    source_meeting_title = (args.get("source_meeting_title") or "").strip()
    participant_ids = args.get("participant_ids", [])

    try:
        scheduled_at = parse_datetime(args["scheduled_at"])
        end_time = parse_datetime(args["end_time"]) if args.get("end_time") else None
    except ValueError as e:
        raise Exception(f"Format waktu tidak valid: {str(e)}")

    if end_time and end_time <= scheduled_at:
        raise Exception("END_TIME_BEFORE_START_TIME")

    if scheduled_at < datetime.now(scheduled_at.tzinfo):
        raise Exception("SCHEDULE_IN_THE_PAST")

    # Ambil source meeting
    if source_meeting_id:
        source_meeting = execute_query(
            """SELECT id, title, description, scheduled_at, end_time, location, status, created_by
                FROM meetings WHERE id = %s""",
            (source_meeting_id,),
            fetch="one"
        )

        if not source_meeting:
            raise Exception("Meeting tidak ditemukan")

        role_check = execute_query(
            """
            SELECT role FROM meeting_participants
            WHERE meeting_id = %s AND user_id = %s
            """,
            (source_meeting_id, user_id),
            fetch="one"
        )

        if not role_check or role_check["role"] != "host":
            raise Exception("Hanya host yang dapat membuat continuation")

    elif source_meeting_title:
        source_meetings = find_user_meetings_by_title(user_id, source_meeting_title)

        if not source_meetings:
            raise Exception("Meeting tidak ditemukan")

        if len(source_meetings) > 1:
            return {
                "success": False,
                "message": "Ditemukan beberapa meeting dengan judul yang sama",
                "matches": meeting_title_match_summary(source_meetings),
            }

        source_meeting = source_meetings[0]

        role_check = execute_query(
            """
            SELECT role FROM meeting_participants
            WHERE meeting_id = %s AND user_id = %s
            """,
            (source_meeting["id"], user_id),
            fetch="one"
        )

        if not role_check or role_check["role"] != "host":
            raise Exception("Hanya host yang dapat membuat continuation")
    else:
        raise ValueError("source_meeting_id atau source_meeting_title wajib diisi")

    if args.get("location") and end_time:
        room_check = check_room_available(args["location"], scheduled_at, end_time)
        if room_check:
            raise Exception("SCHEDULE_CONFLICT_ROOM")

    if end_time:
        all_conflicts = []
        all_user_ids = [user_id] + [p["user_id"] for p in participant_ids]

        for pid in all_user_ids:
            conflicts = check_schedule_conflict(pid, scheduled_at, end_time)
            all_conflicts.extend(conflicts)

        unique_conflicts = list(set(all_conflicts))
        if unique_conflicts:
            raise Exception(f"SCHEDULE_CONFLICT_USERS_[{', '.join(unique_conflicts)}]")

    meeting = execute_query(
        """
        INSERT INTO meetings (
            title, description, scheduled_at, end_time, location, created_by, previous_meeting_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING id, title, description, scheduled_at, end_time, location, status
        """,
        (
            args["title"],
            args.get("description"),
            scheduled_at,
            end_time,
            args.get("location"),
            user_id,
            source_meeting["id"],
        ),
        fetch="one"
    )

    if not meeting:
        raise Exception("FAILED_CREATE_MEETING")

    execute_query(
        """
        INSERT INTO meeting_participants (meeting_id, user_id, role)
        VALUES (%s, %s, 'host')
        """,
        (meeting["id"], user_id),
        fetch="none"
    )

    valid_access_levels = ["full", "summary_only", "none"]
    
    host = execute_query(
        "SELECT name FROM users WHERE id = %s",
        (user_id,),
        fetch="one"
    )

    for p in participant_ids:

        access_level = p.get("access_level")

        if access_level and access_level not in valid_access_levels:
            raise Exception("INVALID_ACCESS_LEVEL")

        participant_user_id = p["user_id"]

        if participant_user_id == user_id:
            continue

        execute_query(
            """
            INSERT INTO meeting_participants (
                meeting_id,
                user_id,
                role
            )
            VALUES (%s, %s, %s)
            """,
            (
                meeting["id"],
                participant_user_id,
                p.get("role", "participant")
            ),
            fetch="none"
        )

        was_participant = execute_query(
            """
            SELECT 1 FROM meeting_participants
            WHERE meeting_id = %s AND user_id = %s
            """,
            (source_meeting_id, participant_user_id),
            fetch="one"
        )

        access_level = (
            "full"
            if was_participant
            else p.get("access_level", "none")
        )

        execute_query(
            """
            INSERT INTO meeting_continuation_access 
            (
                continuation_meeting_id,
                source_meeting_id,
                user_id,
                access_level
            )
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (
                continuation_meeting_id,
                source_meeting_id,
                user_id
            )
            DO UPDATE SET access_level = EXCLUDED.access_level
            """,
            (
                meeting["id"],
                source_meeting_id,
                participant_user_id,
                access_level
            ),
            fetch="none"
        )

        target_user = execute_query(
            "SELECT id, name, whatsapp_phone FROM users WHERE id = %s",
            (participant_user_id,),
            fetch="one"
        )

        if target_user and target_user.get("whatsapp_phone"):
            try:
                await send_invitation_whatsapp(
                    recipient_phone=target_user["whatsapp_phone"],
                    recipient_name=target_user["name"],
                    meeting=meeting,
                    host_name=host["name"] if host else "Host",
                )
            except Exception as e:
                print(f"[WA Error] Invitation to {target_user.get('whatsapp_phone')}: {e}")

    open_action_items = execute_query(
        """
        SELECT id, description, assigned_to, due_date
        FROM action_items
        WHERE meeting_id = %s AND status = 'open'
        """,
        (source_meeting["id"],),
        fetch="all"
    )

    carried_items = []
    for item in open_action_items:
        execute_query(
            "UPDATE action_items SET status = %s WHERE id = %s",
            ("carried_over", item["id"]),
            fetch="none"
        )

        new_item = execute_query(
            """
            INSERT INTO action_items (
                meeting_id, description, assigned_to, due_date, carried_from_id
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                meeting["id"],
                item["description"],
                item["assigned_to"],
                item["due_date"],
                item["id"],
            ),
            fetch="one"
        )
        carried_items.append(new_item)

    participants = execute_query(
        """
        SELECT mp.user_id, mp.role, u.name, u.email
        FROM meeting_participants mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.meeting_id = %s
        """,
        (meeting["id"],),
        fetch="all"
    )

    return {
        "success": True,
        "meeting": {
            **meeting,
            "participants": participants
        },
        "carried_action_items": carried_items,
        "message": f"Meeting '{source_meeting['title']}' berhasil dilanjutkan"
    }

async def _get_previous_meeting(args: dict, user_id: str):
    continuation_meeting_id = args.get("continuation_meeting_id")
    continuation_meeting_title = (args.get("continuation_meeting_title") or "").strip()

    if continuation_meeting_id:
        continuation_meeting = execute_query(
            """SELECT id, title, description, scheduled_at, end_time, location, status, previous_meeting_id, created_by
               FROM meetings WHERE id = %s""",
            (continuation_meeting_id,),
            fetch="one"
        )

        if not continuation_meeting:
            raise Exception("Meeting tidak ditemukan")

        role_check = execute_query(
            """
            SELECT role FROM meeting_participants
            WHERE meeting_id = %s AND user_id = %s
            """,
            (continuation_meeting_id, user_id),
            fetch="one"
        )

        if not role_check:
            raise Exception("Kamu tidak memiliki akses ke meeting ini!")

        if not continuation_meeting["previous_meeting_id"]:
            raise Exception("Meeting ini tidak memiliki meeting sebelumnya")

        source_meeting_id = continuation_meeting["previous_meeting_id"]

    elif continuation_meeting_title:
        continuation_meetings = find_user_meetings_by_title(user_id, continuation_meeting_title)

        if not continuation_meetings:
            raise Exception("Meeting tidak ditemukan")

        if len(continuation_meetings) > 1:
            return {
                "success": False,
                "message": "Ditemukan beberapa meeting dengan judul yang sama",
                "matches": meeting_title_match_summary(continuation_meetings),
            }

        continuation_meeting = continuation_meetings[0]

        if not continuation_meeting["previous_meeting_id"]:
            raise Exception("Meeting ini tidak memiliki meeting sebelumnya")

        source_meeting_id = continuation_meeting["previous_meeting_id"]

    else:
        raise ValueError("continuation_meeting_id atau continuation_meeting_title wajib diisi")

    was_participant = execute_query(
        """
        SELECT 1 FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        """,
        (source_meeting_id, user_id),
        fetch="one"
    )

    if was_participant:
        meeting = execute_query(
            """SELECT id, title, description, scheduled_at, end_time, location, status, previous_meeting_id, created_by
               FROM meetings WHERE id = %s""",
            (source_meeting_id,),
            fetch="one"
        )

        participants = execute_query(
            """
            SELECT mp.user_id, mp.role, u.name, u.email
            FROM meeting_participants mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = %s
            """,
            (meeting["id"],),
            fetch="all"
        )

        return {
            "access_level": "full",
            "meeting": {
                **meeting,
                "participants": participants
            }
        }

    access_level = execute_query(
        """
        SELECT access_level FROM meeting_continuation_access
        WHERE continuation_meeting_id = %s
        AND source_meeting_id = %s
        AND user_id = %s
        """,
        (continuation_meeting["id"], source_meeting_id, user_id),
        fetch="one"
    )

    if not access_level or access_level["access_level"] == "none":
        raise Exception("Kamu tidak memiliki akses ke meeting sebelumnya")

    source_meeting = execute_query(
        """SELECT id, title, description, scheduled_at, end_time, location, status, previous_meeting_id, created_by
           FROM meetings WHERE id = %s""",
        (source_meeting_id,),
        fetch="one"
    )

    if access_level["access_level"] == "summary_only":
        return {
            "access_level": "summary_only",
            "meeting": {
                "id": source_meeting["id"],
                "title": source_meeting["title"],
                "scheduled_at": source_meeting["scheduled_at"],
                "status": source_meeting["status"],
                "description": source_meeting["description"],
            }
        }

    participants = execute_query(
        """
        SELECT mp.user_id, mp.role, u.name, u.email
        FROM meeting_participants mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.meeting_id = %s
        """,
        (source_meeting_id,),
        fetch="all"
    )

    return {
        "access_level": "full",
        "meeting": {
            **source_meeting,
            "participants": participants
        }
    }