from db.postgres import execute_query
from datetime import datetime

MEETING_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "create_meeting",
            "description": "Membuat meeting baru. Gunakan tool ini ketika user ingin membuat atau menjadwalkan meeting baru.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Judul meeting"
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
                    }
                },
                "required": ["title", "scheduled_at", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_meetings",
            "description": "Mengambil daftar meeting yang diikuti user. Gunakan untuk melihat semua meeting atau meeting dengan status tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["scheduled", "ongoing", "done", "cancelled", "all"],
                        "description": "Filter status meeting. Gunakan 'all' untuk semua meeting."
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_meeting_detail",
            "description": "Mengambil detail lengkap sebuah meeting termasuk peserta dan notulen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting yang ingin dilihat detailnya"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_meetings",
            "description": "Mencari meeting berdasarkan kata kunci judul.",
            "parameters": {
                "type": "object",
                "properties": {
                    "keyword": {
                        "type": "string",
                        "description": "Kata kunci untuk mencari meeting"
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
            "name": "update_meeting_status",
            "description": "Mengubah status meeting. Gunakan untuk memulai (ongoing), mengakhiri (done), atau membatalkan (cancelled) meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["ongoing", "done", "cancelled"],
                        "description": "Status baru meeting"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "status", "user_id"]
            }
        }
    }
]


async def execute_meeting_tool(tool_name: str, args: dict):
    user_id = args.get("user_id")

    if tool_name == "create_meeting":
        return await _create_meeting(args, user_id)
    elif tool_name == "get_meetings":
        return await _get_meetings(args, user_id)
    elif tool_name == "get_meeting_detail":
        return await _get_meeting_detail(args, user_id)
    elif tool_name == "search_meetings":
        return await _search_meetings(args, user_id)
    elif tool_name == "update_meeting_status":
        return await _update_meeting_status(args, user_id)
    else:
        raise ValueError(f"Meeting tool '{tool_name}' tidak ditemukan")


async def _create_meeting(args: dict, user_id: str):
    # Buat meeting
    meeting = execute_query(
        """INSERT INTO meetings (title, description, scheduled_at, end_time, location, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, scheduled_at, end_time, location, status""",
        (
            args["title"],
            args.get("description"),
            args["scheduled_at"],
            args.get("end_time"),
            args.get("location"),
            user_id,
        ),
        fetch="one"
    )

    if not meeting:
        raise Exception("Gagal membuat meeting")

    # Tambahkan creator sebagai host
    execute_query(
        """INSERT INTO meeting_participants (meeting_id, user_id, role)
            VALUES (%s, %s, 'host')""",
        (meeting["id"], user_id),
        fetch="none"
    )

    return {
        "success": True,
        "meeting": meeting,
        "message": f"Meeting '{meeting['title']}' berhasil dibuat"
    }


async def _get_meetings(args: dict, user_id: str):
    status = args.get("status", "all")

    if status == "all":
        meetings = execute_query(
            """SELECT m.id, m.title, m.scheduled_at, m.end_time, m.location,
                m.status, mp.role as my_role
                FROM meetings m
                JOIN meeting_participants mp ON m.id = mp.meeting_id
                WHERE mp.user_id = %s
                ORDER BY m.scheduled_at DESC
                LIMIT 20""",
            (user_id,)
        )
    else:
        meetings = execute_query(
            """SELECT m.id, m.title, m.scheduled_at, m.end_time, m.location,
                m.status, mp.role as my_role
                FROM meetings m
                JOIN meeting_participants mp ON m.id = mp.meeting_id
                WHERE mp.user_id = %s AND m.status = %s
                ORDER BY m.scheduled_at DESC
                LIMIT 20""",
            (user_id, status)
        )

    return {
        "success": True,
        "meetings": meetings,
        "total": len(meetings)
    }


async def _get_meeting_detail(args: dict, user_id: str):
    meeting_id = args["meeting_id"]

    # Cek akses
    access = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not access:
        raise Exception("Kamu tidak memiliki akses ke meeting ini")

    # Ambil meeting
    meeting = execute_query(
        """SELECT id, title, description, scheduled_at, end_time,
            location, status, created_by
            FROM meetings WHERE id = %s""",
        (meeting_id,),
        fetch="one"
    )
    if not meeting:
        raise Exception("Meeting tidak ditemukan")

    # Ambil peserta
    participants = execute_query(
        """SELECT u.id, u.name, u.email, mp.role
            FROM meeting_participants mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = %s""",
        (meeting_id,)
    )

    return {
        "success": True,
        "meeting": {**meeting, "participants": participants}
    }


async def _search_meetings(args: dict, user_id: str):
    keyword = args["keyword"]

    meetings = execute_query(
        """SELECT m.id, m.title, m.scheduled_at, m.location, m.status, mp.role as my_role
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE mp.user_id = %s AND m.title ILIKE %s
            ORDER BY m.scheduled_at DESC
            LIMIT 20""",
        (user_id, f"%{keyword}%")
    )

    return {
        "success": True,
        "meetings": meetings,
        "total": len(meetings)
    }


async def _update_meeting_status(args: dict, user_id: str):
    meeting_id = args["meeting_id"]
    status = args["status"]

    # Cek hanya host yang bisa update
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat mengubah status meeting")

    execute_query(
        "UPDATE meetings SET status = %s WHERE id = %s",
        (status, meeting_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Status meeting berhasil diubah menjadi '{status}'"
    }