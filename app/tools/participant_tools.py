from db.postgres import execute_query

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
        """SELECT id, name, email
            FROM users
            WHERE name ILIKE %s OR email ILIKE %s
            LIMIT 10""",
        (f"%{keyword}%", f"%{keyword}%")
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

    # Cek hanya host yang bisa tambah peserta
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat menambahkan peserta")

    # Cek sudah jadi peserta belum
    existing = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="one"
    )
    if existing:
        raise Exception("User sudah menjadi peserta meeting ini")

    # Cek user ada
    target_user = execute_query(
        "SELECT id, name, email FROM users WHERE id = %s",
        (target_user_id,),
        fetch="one"
    )
    if not target_user:
        raise Exception("User tidak ditemukan")

    # Tambahkan peserta
    execute_query(
        """INSERT INTO meeting_participants (meeting_id, user_id, role)
            VALUES (%s, %s, 'participant')""",
        (meeting_id, target_user_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"{target_user['name']} berhasil ditambahkan sebagai peserta"
    }

async def _remove_participant(args: dict):
    meeting_id = args["meeting_id"]
    target_user_id = args["target_user_id"]
    user_id = args["user_id"]

    # Cek hanya host yang bisa hapus peserta
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat menghapus peserta")

    if target_user_id == user_id:
        raise Exception("Host tidak bisa menghapus diri sendiri")

    # Cek target memang peserta meeting
    existing = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="one"
    )
    if not existing:
        raise Exception("User bukan peserta meeting ini")

    # Cek user ada
    target_user = execute_query(
        "SELECT id, name, email FROM users WHERE id = %s",
        (target_user_id,),
        fetch="one"
    )
    if not target_user:
        raise Exception("User tidak ditemukan")

    execute_query(
        "DELETE FROM meeting_participants WHERE meeting_id = %s AND user_id = %s ",
        (meeting_id, target_user_id),
        fetch='none'
    )

    return {
        "success": True,
        "message": f"{target_user['name']} berhasil dihapus sebagai peserta"
    }

async def _update_role_participant(args: dict):
    meeting_id = args["meeting_id"]
    target_user_id = args["target_user_id"]
    user_id = args["user_id"]
    role_target = args["role"]
    validRoles = ["secretary", "participant"]

    if role_target not in validRoles:
        raise Exception("Role tidak valid")

    # Cek hanya host yang bisa update role peserta
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat memperbarui role peserta")

    if target_user_id == user_id:
        raise Exception("Host tidak bisa memperbarui role diri sendiri")

    # Cek target memang peserta meeting
    existing = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, target_user_id),
        fetch="one"
    )
    if not existing:
        raise Exception("User bukan peserta meeting ini")

    # Cek user ada
    target_user = execute_query(
        "SELECT id, name, email FROM users WHERE id = %s",
        (target_user_id,),
        fetch="one"
    )
    if not target_user:
        raise Exception("User tidak ditemukan")
    
    execute_query(
        "UPDATE meeting_participants SET role = %s WHERE meeting_id = %s AND user_id = %s",
        (role_target, meeting_id, target_user_id),
        fetch='none'
    )

    return {
        "success": True,
        "message": f"{target_user['name']} role berhasil diperbarui"
    }