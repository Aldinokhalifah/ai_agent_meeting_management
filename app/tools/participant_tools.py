from db.postgres import execute_query
from utils.check_schedule_conflict import check_schedule_conflict
from services.waService import send_invitation_whatsapp

PARTICIPANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_user",
            "description": "Mencari user berdasarkan nama atau email untuk ditambahkan ke meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Nama atau email user yang dicari"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["keyword", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "add_participant",
            "description": "Menambahkan user sebagai peserta ke sebuah meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "target_user_id": {
                        "type": "string",
                        "description": "ID user yang akan ditambahkan"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user yang melakukan aksi (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "target_user_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "remove_participant",
            "description": "Menghapus user dari peserta sebuah meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "target_user_id": {
                        "type": "string",
                        "description": "ID user yang akan dihapus"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user yang melakukan aksi (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "target_user_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_role_participant",
            "description": "Memperbarui role user dari peserta sebuah meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "target_user_id": {
                        "type": "string",
                        "description": "ID user yang rolenya akan diubah"
                    },
                    "role": {
                        "type": "string",
                        "description": "Role baru: secretary atau participant"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user yang melakukan aksi (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "target_user_id", "user_id", "role"]
            }
        }
    }
]


async def execute_participant_tool(tool_name: str, args: dict):
    if tool_name == "search_user":
        return await _search_user(args)
    elif tool_name == "add_participant":
        return await _add_participant(args)
    elif tool_name == "remove_participant":
        return await _remove_participant(args)
    elif tool_name == "update_role_participant":
        return await _update_role_participant(args)
    else:
        raise ValueError(f"Participant tool '{tool_name}' tidak ditemukan")


async def _search_user(args: dict):
    keyword = args["keyword"]

    users = execute_query(
        """
        SELECT id, name, email
        FROM users
        WHERE name ILIKE %s OR email ILIKE %s
        LIMIT 10
        """,
        (f"%{keyword}%", f"%{keyword}%"),
        fetch="all"
    )

    return {
        "success": True,
        "users": users,
        "total": len(users)
    }


async def _add_participant(args: dict):
    meeting_id = args["meeting_id"]
    target_user_id = args["target_user_id"]
    user_id = args["user_id"]

    meeting = execute_query(
        """
        SELECT id, title, scheduled_at, end_time, location, status
        FROM meetings
        WHERE id = %s
        """,
        (meeting_id,),
        fetch="one"
    )

    if not meeting:
        raise Exception("Meeting tidak ditemukan.")

    role = execute_query(
        """
        SELECT role
        FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        """,
        (meeting_id, user_id),
        fetch="one"
    )

    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat menambahkan peserta.")

    target_user = execute_query(
        """
        SELECT id, name, email, whatsapp_phone
        FROM users
        WHERE id = %s
        """,
        (target_user_id,),
        fetch="one"
    )

    if not target_user:
        raise Exception("Peserta tidak ditemukan.")

    existing = execute_query(
        """
        SELECT 1
        FROM meeting_participants
        WHERE meeting_id = %s AND user_id = %s
        """,
        (meeting_id, target_user_id),
        fetch="one"
    )

    if existing:
        raise Exception(f"Peserta {target_user['name']} sudah menjadi peserta")

    if meeting["end_time"]:
        conflict_users = check_schedule_conflict(
            target_user_id,
            meeting["scheduled_at"],
            meeting["end_time"]
        )

        if conflict_users:
            raise Exception(
                f"SCHEDULE_CONFLICT_USERS_{','.join(conflict_users)}"
            )

    execute_query(
        """
        INSERT INTO meeting_participants (
            meeting_id,
            user_id,
            role
        )
        VALUES (%s, %s, 'participant')
        """,
        (meeting_id, target_user_id),
        fetch="none"
    )
    
    if target_user.get("whatsapp_phone"):
        host = execute_query(
            "SELECT name FROM users WHERE id = %s",
            (user_id,),
            fetch="one"
        )
        try:
            await send_invitation_whatsapp(
                recipient_phone=target_user["whatsapp_phone"],
                recipient_name=target_user["name"],
                meeting=meeting,
                host_name=host["name"] if host else "Host",
            )
        except Exception as e:
            print(f"[WA Error] Invitation to {target_user['whatsapp_phone']}: {e}")
    else:
        print(f"[WA Skipped] {target_user.get('name')} tidak punya whatsapp_phone (user_id={target_user_id})")

    return {
        "success": True,
        "message": f"{target_user['name']} berhasil ditambahkan sebagai peserta"
    }


async def _remove_participant(args: dict):
    meeting_id = args["meeting_id"]
    target_user_id = args["target_user_id"]
    user_id = args["user_id"]

    meeting = execute_query(
        """
        SELECT id, title
        FROM meetings
        WHERE id = %s
        """,
        (meeting_id,),
        fetch="one"
    )

    if not meeting:
        raise Exception("Meeting tidak ditemukan")

    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )

    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat menghapus peserta")

    if target_user_id == user_id:
        raise Exception("Host tidak bisa menghapus diri sendiri")

    existing = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="one"
    )

    if not existing:
        raise Exception("User bukan peserta meeting ini")

    target_user = execute_query(
        "SELECT id, name, email FROM users WHERE id = %s",
        (target_user_id,),
        fetch="one"
    )

    if not target_user:
        raise Exception("User tidak ditemukan")

    execute_query(
        "DELETE FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"{target_user['name']} berhasil dihapus sebagai peserta"
    }


async def _update_role_participant(args: dict):
    meeting_id = args["meeting_id"]
    target_user_id = args["target_user_id"]
    user_id = args["user_id"]
    new_role = args["role"]

    valid_roles = ["secretary", "participant"]
    if new_role not in valid_roles:
        raise Exception("Role tidak valid")

    meeting = execute_query(
        """
        SELECT id, title
        FROM meetings
        WHERE id = %s
        """,
        (meeting_id,),
        fetch="one"
    )

    if not meeting:
        raise Exception("Meeting tidak ditemukan")

    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )

    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat memperbarui role peserta")

    if target_user_id == user_id:
        raise Exception("Host tidak bisa memperbarui role diri sendiri")

    existing = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="one"
    )

    if not existing:
        raise Exception("User bukan peserta meeting ini")

    target_user = execute_query(
        "SELECT id, name, email FROM users WHERE id = %s",
        (target_user_id,),
        fetch="one"
    )

    if not target_user:
        raise Exception("User tidak ditemukan")

    execute_query(
        "UPDATE meeting_participants SET role = %s WHERE meeting_id = %s AND user_id = %s",
        (new_role, meeting_id, target_user_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"{target_user['name']} role berhasil diperbarui"
    }