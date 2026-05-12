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
    },
    {
        "type": "function",
        "function": {
            "name": "remove_meeting",
            "description": "Menghapus meeting. Gunakan tool ini jika user ingin menghapus meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
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
            "name": "get_meeting_participants",
            "description": "Mengambil daftar peserta dari sebuah meeting tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
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
            "name": "get_upcoming_meetings",
            "description": "Mengambil daftar meeting yang akan datang dalam beberapa hari ke depan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "days": {
                        "type": "integer",
                        "description": "Jumlah hari ke depan (default 7)"
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
            "name": "get_meeting_notes",
            "description": "Mengambil notulen dari sebuah meeting tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
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
            "name": "get_ai_summary",
            "description": "Mengambil AI summary dari sebuah meeting yang sudah selesai.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
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
    elif tool_name == "remove_meeting":
        return await _remove_meeting(args, user_id)
    elif tool_name == "get_meeting_participants":
        return await _get_meeting_participants(args, user_id)
    elif tool_name == "get_upcoming_meetings":
        return await _get_upcoming_meetings(args, user_id)
    elif tool_name == "get_meeting_notes":
        return await _get_meeting_notes(args, user_id)
    elif tool_name == "get_ai_summary":
        return await _get_ai_summary(args, user_id)
    else:
        raise ValueError(f"Meeting tool '{tool_name}' tidak ditemukan")

def parse_datetime(value: str) -> str:
    """Konversi berbagai format datetime ke ISO 8601"""
    if not value:
        raise ValueError("scheduled_at tidak boleh kosong")

    # Coba beberapa format umum
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).isoformat()
        except ValueError:
            continue

    raise ValueError(f"Format datetime tidak valid: {value}")

async def _create_meeting(args: dict, user_id: str):
    try:
        scheduled_at = parse_datetime(args["scheduled_at"])
        end_time = parse_datetime(args["end_time"]) if args.get("end_time") else None
    except ValueError as e:
        raise Exception(f"Format waktu tidak valid: {str(e)}")

    meeting = execute_query(
        """INSERT INTO meetings (title, description, scheduled_at, end_time, location, created_by)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id, title, scheduled_at, end_time, location, status""",
        (
            args["title"],
            args.get("description"),
            scheduled_at,
            end_time,
            args.get("location"),
            user_id,
        ),
        fetch="one"
    )

    if not meeting:
        raise Exception("Gagal membuat meeting")

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

async def _remove_meeting(args: dict, user_id: str):
    meeting_id = args["meeting_id"]

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

    # Cek hanya host yang bisa update
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] != "host":
        raise Exception("Hanya host yang dapat menghapus meeting")

    # Hapus dependensi terlebih dahulu untuk menghindari FK constraint (jika ada)
    execute_query(
        "DELETE FROM action_items WHERE meeting_id = %s",
        (meeting_id,),
        fetch="none"
    )
    execute_query(
        "DELETE FROM meeting_participants WHERE meeting_id = %s",
        (meeting_id,),
        fetch="none"
    )

    execute_query(
        "DELETE FROM meetings WHERE id = %s",
        (meeting_id,),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Meeting dengan judul: {meeting['title']} berhasil dihapus"
    }

async def _get_meeting_participants(args: dict, user_id: str):
    meeting_id = args["meeting_id"]

    # Cek akses
    access = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not access:
        raise Exception("Kamu tidak memiliki akses ke meeting ini")

    participants = execute_query(
        """SELECT u.id, u.name, u.email, mp.role
            FROM meeting_participants mp
            JOIN users u ON mp.user_id = u.id
            WHERE mp.meeting_id = %s
            ORDER BY mp.role ASC""",
        (meeting_id,)
    )

    return {
        "success": True,
        "participants": participants,
        "total": len(participants)
    }


async def _get_upcoming_meetings(args: dict, user_id: str):
    days = args.get("days", 7)
    
    meetings = execute_query(
        """SELECT m.id, m.title, m.scheduled_at, m.end_time,
            m.location, m.status, mp.role as my_role
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE mp.user_id = %s
            AND m.status = 'scheduled'
            AND m.scheduled_at BETWEEN NOW() AND NOW() + INTERVAL '%s days'
            ORDER BY m.scheduled_at ASC""",
        (user_id, days)
    )

    return {
        "success": True,
        "meetings": meetings,
        "total": len(meetings),
        "days": days
    }


async def _get_meeting_notes(args: dict, user_id: str):
    meeting_id = args["meeting_id"]

    # Cek akses
    access = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not access:
        raise Exception("Kamu tidak memiliki akses ke meeting ini")

    note = execute_query(
        """SELECT n.content, n.updated_at, u.name as created_by_name
            FROM notes n
            JOIN users u ON n.created_by = u.id
            WHERE n.meeting_id = %s""",
        (meeting_id,),
        fetch="one"
    )

    if not note:
        return {
            "success": True,
            "note": None,
            "message": "Belum ada notulen untuk meeting ini"
        }

    # Konversi Tiptap JSON ke plain text
    content = note.get("content", {})
    plain_text = _tiptap_to_text(content)

    return {
        "success": True,
        "note": {
            "content": plain_text,
            "updated_at": str(note["updated_at"]),
            "created_by": note["created_by_name"]
        }
    }


async def _get_ai_summary(args: dict, user_id: str):
    meeting_id = args["meeting_id"]

    # Cek akses
    access = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not access:
        raise Exception("Kamu tidak memiliki akses ke meeting ini")

    meeting = execute_query(
        "SELECT title, status, ai_summary FROM meetings WHERE id = %s",
        (meeting_id,),
        fetch="one"
    )

    if not meeting:
        raise Exception("Meeting tidak ditemukan")

    if meeting["status"] != "done":
        return {
            "success": False,
            "message": "AI summary hanya tersedia setelah meeting selesai"
        }

    if not meeting["ai_summary"]:
        return {
            "success": False,
            "message": "AI summary belum dibuat untuk meeting ini"
        }

    return {
        "success": True,
        "meeting_title": meeting["title"],
        "ai_summary": meeting["ai_summary"]
    }


def _tiptap_to_text(content) -> str:
    """Konversi Tiptap JSON ke plain text"""
    if not content:
        return ""

    def parse_node(node):
        if not node:
            return ""
        node_type = node.get("type", "")
        children = node.get("content", [])

        if node_type == "text":
            return node.get("text", "")
        elif node_type == "paragraph":
            return "".join(parse_node(c) for c in children) + "\n"
        elif node_type == "heading":
            return "".join(parse_node(c) for c in children) + "\n"
        elif node_type in ("bulletList", "orderedList"):
            return "".join(parse_node(c) for c in children)
        elif node_type == "listItem":
            return "• " + "".join(parse_node(c) for c in children)
        elif node_type == "hardBreak":
            return "\n"
        elif node_type == "doc":
            return "".join(parse_node(c) for c in children)
        else:
            return "".join(parse_node(c) for c in children)

    return parse_node(content).strip()