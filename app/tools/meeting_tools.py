from db.postgres import execute_query
from datetime import datetime
from openai import OpenAI
import os
from utils.prompt import build_meeting_summary_prompt
from utils.check_schedule_conflict import check_schedule_conflict
from utils.check_room_available import check_room_available
from utils.parse_datetime import parse_datetime
from utils.meeting_title_match_summary import meeting_title_match_summary
from utils.find_user_meetings_by_title import find_user_meetings_by_title
from utils.tiptap_to_text import tiptap_to_text
from services.waService import send_meeting_summary_whatsapps

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
                    },
                    "participant_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Daftar ID user peserta meeting"
                    },
                    "previous_meeting_id": {
                        "type": "string",
                        "description": "ID meeting sebelumnya jika ini meeting lanjutan"
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
            "name": "get_meeting_detail_by_title",
            "description": "Mengambil detail lengkap sebuah meeting berdasarkan title meeting termasuk peserta dan notulen.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "title meeting yang ingin dilihat detailnya"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["title", "user_id"]
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
                    "title": {
                        "type": "string",
                        "description": "Judul meeting, dipakai kalau meeting_id tidak tersedia"
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
    elif tool_name == "get_meeting_detail_by_title":
        return await _get_meeting_detail_by_title(args, user_id)
    else:
        raise ValueError(f"Meeting tool '{tool_name}' tidak ditemukan")

openrouter = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY")
)

async def generate_meeting_summary(meeting_id: str, user_id: str):
    # Ambil meeting
    meeting = execute_query(
        """
        SELECT id, title, scheduled_at, location,
        description, status
        FROM meetings
        WHERE id = %s
        """,
        (meeting_id,),
        fetch="one"
    )

    if not meeting:
        raise Exception("MEETING_NOT_FOUND")

    # Cek participant
    access = execute_query(
        """
        SELECT 1
        FROM meeting_participants
        WHERE meeting_id = %s
        AND user_id = %s
        """,
        (meeting_id, user_id),
        fetch="one"
    )

    if not access:
        raise Exception("ACCESS_FORBIDDEN")

    # Meeting harus done
    if meeting["status"] != "done":
        raise Exception("MEETING_NOT_DONE")

    # Ambil note
    note = execute_query(
        """
        SELECT content
        FROM notes
        WHERE meeting_id = %s
        """,
        (meeting_id,),
        fetch="one"
    )

    note_content = note["content"] if note else None

    note_text = tiptap_to_text(note_content) if note_content else None

    if not note_text:
        raise Exception("NOTE_EMPTY")

    # Ambil participants
    participants = execute_query(
        """
        SELECT u.name, mp.role
        FROM meeting_participants mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.meeting_id = %s
        """,
        (meeting_id,),
        fetch="all"
    )

    participant_names = ", ".join(
        [f"{p['name']} ({p['role']})" for p in participants]
    )

    # Ambil action items
    action_items = execute_query(
        """
        SELECT
            ai.description,
            ai.status,
            ai.due_date,
            u.name AS assigned_to_name
        FROM action_items ai
        LEFT JOIN users u
            ON ai.assigned_to = u.id
        WHERE ai.meeting_id = %s
        """,
        (meeting_id,),
        fetch="all"
    )

    pending_items = [
        item for item in action_items
        if item["status"] != "done"
    ]

    if pending_items:
        action_item_text = "\n".join([
            f"{idx + 1}. {item['description']} "
            f"(Ditugaskan ke: {item['assigned_to_name'] or 'Belum ditugaskan'}, "
            f"Deadline: {item['due_date'] or 'Tidak ada deadline'})"
            for idx, item in enumerate(pending_items)
        ])
    else:
        action_item_text = "Tidak ada action items"

    # Prompt
    prompt = build_meeting_summary_prompt(
        meeting["title"],
        meeting["scheduled_at"],
        meeting["location"],
        meeting["description"],
        note_text,
        participant_names,
        action_item_text
    )

    # Request OpenRouter
    response = openrouter.chat.completions.create(
        model=os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b:free"),
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        max_tokens=1000,
        temperature=0.3
    )

    summary = response.choices[0].message.content

    if not summary:
        raise Exception("AI_RESPONSE_EMPTY")

    # Simpan summary
    execute_query(
        """
        UPDATE meetings
        SET ai_summary = %s
        WHERE id = %s
        """,
        (summary, meeting_id),
        fetch="none"
    )

    return summary

async def _create_meeting(args: dict, user_id: str):
    title = args.get("title")
    description = args.get("description")
    location = args.get("location")
    participant_ids = args.get("participant_ids", [])
    previous_meeting_id = args.get("previous_meeting_id")

    if not title or not args.get("scheduled_at"):
        raise Exception("TITLE_AND_SCHEDULE_REQUIRED")

    # Parse datetime
    try:
        scheduled_at = parse_datetime(args["scheduled_at"])
        end_time = (
            parse_datetime(args["end_time"])
            if args.get("end_time")
            else None
        )
    except ValueError as e:
        raise Exception(f"Format waktu tidak valid: {str(e)}")

    # Validasi end_time > scheduled_at
    if end_time and end_time <= scheduled_at:
        raise Exception("END_TIME_BEFORE_START_TIME")

    # Validasi scheduled_at tidak di masa lalu
    if scheduled_at < datetime.now(scheduled_at.tzinfo):
        raise Exception("SCHEDULE_IN_THE_PAST")

    # Validasi room bentrok
    if location and end_time:
        room_conflict = check_room_available(
            location,
            scheduled_at,
            end_time
        )

        if room_conflict:
            raise Exception("SCHEDULE_CONFLICT_ROOM")

    # Validasi participant bentrok
    if end_time:

        all_conflicts = []

        for pid in [user_id, *participant_ids]:

            conflicts = check_schedule_conflict(
                pid,
                scheduled_at,
                end_time
            )

            all_conflicts.extend(conflicts)

        unique_conflicts = list(set(all_conflicts))

        if unique_conflicts:
            raise Exception(
                f"SCHEDULE_CONFLICT_USERS_[{', '.join(unique_conflicts)}]"
            )

    # Create meeting
    meeting = execute_query(
        """
        INSERT INTO meetings (
            title,
            description,
            scheduled_at,
            end_time,
            location,
            created_by,
            previous_meeting_id
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        RETURNING
            id,
            title,
            description,
            scheduled_at,
            end_time,
            location,
            status
        """,
        (
            title,
            description,
            scheduled_at,
            end_time,
            location,
            user_id,
            previous_meeting_id
        ),
        fetch="one"
    )

    if not meeting:
        raise Exception("FAILED_CREATE_MEETING")

    # Tambahkan host
    execute_query(
        """
        INSERT INTO meeting_participants (
            meeting_id,
            user_id,
            role
        )
        VALUES (%s, %s, 'host')
        """,
        (meeting["id"], user_id),
        fetch="none"
    )

    # Tambahkan participant lain
    for pid in participant_ids:

        if pid == user_id:
            continue

        execute_query(
            """
            INSERT INTO meeting_participants (
                meeting_id,
                user_id,
                role
            )
            VALUES (%s, %s, 'participant')
            """,
            (meeting["id"], pid),
            fetch="none"
        )

    participants = execute_query(
        """
        SELECT
            mp.user_id,
            mp.role,
            u.name,
            u.email
        FROM meeting_participants mp
        JOIN users u
            ON mp.user_id = u.id
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

async def _get_meeting_detail_by_title(args: dict, user_id: str):
    title = (args.get("title") or "").strip()

    if not title:
        raise ValueError("title wajib diisi")

    meetings = find_user_meetings_by_title(user_id, title)

    if not meetings:
        raise Exception("Meeting tidak ditemukan")

    if len(meetings) > 1:
        return {
            "success": False,
            "message": "Ditemukan beberapa meeting dengan judul yang sama",
            "matches": meeting_title_match_summary(meetings),
        }

    meeting = meetings[0]

    # Ambil peserta meeting
    participants = execute_query(
        """
        SELECT
            u.id,
            u.name,
            u.email,
            mp.role
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
            "participants": participants or []
        }
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

    meeting = execute_query(
        "SELECT id, title, status FROM meetings WHERE id = %s",
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
        raise Exception("Hanya host yang dapat mengubah status meeting")

    execute_query(
        "UPDATE meetings SET status = %s WHERE id = %s",
        (status, meeting_id),
        fetch="none"
    )

    # panggil backend generate summary saat done
    if status == "done":
        try:
            await generate_meeting_summary(meeting_id, user_id)
        except Exception as e:
            print(f"[AI SUMMARY ERROR] {str(e)}")

        try:
            await send_meeting_summary_whatsapps(meeting_id)
        except Exception as e:
            print(f"[WA ERROR] meeting {meeting_id}: {str(e)}")

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
        """
        SELECT m.id, m.title, m.scheduled_at, m.end_time,
            m.location, m.status, mp.role as my_role
        FROM meetings m
        JOIN meeting_participants mp ON m.id = mp.meeting_id
        WHERE mp.user_id = %s
        AND m.status = 'scheduled'
        AND m.scheduled_at BETWEEN NOW() AND NOW() + (%s || ' days')::interval
        ORDER BY m.scheduled_at ASC
        """,
        (user_id, days),
        fetch="all"
    )

    return {
        "success": True,
        "meetings": meetings,
        "total": len(meetings),
        "days": days
    }


async def _get_meeting_notes(args: dict, user_id: str):
    meeting_id = args.get("meeting_id")
    title = (args.get("title") or "").strip()

    meeting = None

    # Cari berdasarkan meeting_id
    if meeting_id:
        access = execute_query(
            "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
            (meeting_id, user_id),
            fetch="one"
        )

        if not access:
            raise Exception("Kamu tidak memiliki akses ke meeting ini")

        meeting = execute_query(
            "SELECT id, title FROM meetings WHERE id = %s",
            (meeting_id,),
            fetch="one"
        )

        if not meeting:
            raise Exception("Meeting tidak ditemukan")

    # Cari berdasarkan title
    elif title:
        meetings = find_user_meetings_by_title(user_id, title)

        if not meetings:
            raise Exception("Meeting tidak ditemukan")

        if len(meetings) > 1:
            return {
                "success": False,
                "message": "Ditemukan beberapa meeting dengan judul yang sama",
                "matches": meeting_title_match_summary(meetings),
            }

        meeting = meetings[0]

    else:
        raise ValueError("meeting_id atau title wajib diisi")

    # Ambil note
    note = execute_query(
        """
        SELECT n.content, n.updated_at, u.name as created_by_name
        FROM notes n
        JOIN users u ON n.created_by = u.id
        WHERE n.meeting_id = %s
        """,
        (meeting["id"],),
        fetch="one"
    )

    if not note:
        return {
            "success": True,
            "meeting_id": meeting["id"],
            "meeting_title": meeting["title"],
            "note": None,
            "message": "Belum ada notulen untuk meeting ini"
        }

    # Konversi Tiptap JSON ke plain text
    content = note.get("content", {})
    plain_text = tiptap_to_text(content)

    return {
        "success": True,
        "meeting_id": meeting["id"],
        "meeting_title": meeting["title"],
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