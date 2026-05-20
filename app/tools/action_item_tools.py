from db.postgres import execute_query

from db.postgres import execute_query

ACTION_ITEM_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_my_action_items",
            "description": "Mengambil semua action items yang ditugaskan ke user yang sedang login.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["open", "done", "all"],
                        "description": "Filter status action item"
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
            "name": "create_action_item",
            "description": "Membuat action item baru di sebuah meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "description": {
                        "type": "string",
                        "description": "Deskripsi action item"
                    },
                    "assigned_to": {
                        "type": "string",
                        "description": "ID user yang ditugaskan (opsional)"
                    },
                    "due_date": {
                        "type": "string",
                        "description": "Deadline dalam format YYYY-MM-DD (opsional)"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "description", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_action_item_status",
            "description": "Mengubah status action item menjadi selesai (done) atau dibuka kembali (open) berdasarkan item_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "ID action item"
                    },
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting tempat action item berada"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "done"],
                        "description": "Status baru action item"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["item_id", "meeting_id", "status", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "update_action_item_status_by_description",
            "description": "Mengubah status action item berdasarkan deskripsi action item.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting tempat action item berada"
                    },
                    "description": {
                        "type": "string",
                        "description": "Deskripsi action item yang akan dicari"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "done"],
                        "description": "Status baru action item"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["meeting_id", "description", "status", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_action_item",
            "description": "Menghapus action item di sebuah meeting.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "ID action item"
                    },
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting tempat action item berada"
                    },
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["item_id", "meeting_id", "user_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_action_items_by_meeting",
            "description": "Mengambil semua action items dari sebuah meeting tertentu.",
            "parameters": {
                "type": "object",
                "properties": {
                    "meeting_id": {
                        "type": "string",
                        "description": "ID meeting"
                    },
                    "status": {
                        "type": "string",
                        "enum": ["open", "done", "all"],
                        "description": "Filter status action item (default: all)"
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


async def execute_action_item_tool(tool_name: str, args: dict):
    if tool_name == "get_my_action_items":
        return await _get_my_action_items(args)
    elif tool_name == "create_action_item":
        return await _create_action_item(args)
    elif tool_name == "update_action_item_status":
        return await _update_action_item_status(args)
    elif tool_name == "update_action_item_status_by_description":
        return await _update_action_item_status_by_description(args)
    elif tool_name == "delete_action_item":
        return await _delete_action_item(args)
    elif tool_name == "get_action_items_by_meeting":
        return await _get_action_items_by_meeting(args)
    else:
        raise ValueError(f"Action item tool '{tool_name}' tidak ditemukan")


async def _get_my_action_items(args: dict):
    user_id = args["user_id"]
    status = args.get("status", "open")

    if status == "all":
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                m.title as meeting_title, m.id as meeting_id
                FROM action_items ai
                JOIN meetings m ON ai.meeting_id = m.id
                WHERE ai.assigned_to = %s
                ORDER BY ai.due_date ASC NULLS LAST LIMIT 20""",
            (user_id,)
        )
    else:
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                m.title as meeting_title, m.id as meeting_id
                FROM action_items ai
                JOIN meetings m ON ai.meeting_id = m.id
                WHERE ai.assigned_to = %s AND ai.status = %s
                ORDER BY ai.due_date ASC NULLS LAST LIMIT 20""",
            (user_id, status)
        )

    return {
        "success": True,
        "action_items": items,
        "total": len(items)
    }


async def _create_action_item(args: dict):
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]

    # Cek role — hanya host dan secretary
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] not in ("host", "secretary"):
        raise Exception("Hanya host dan secretary yang dapat membuat action item")

    item = execute_query(
        """INSERT INTO action_items (meeting_id, description, assigned_to, due_date)
            VALUES (%s, %s, %s, %s)
            RETURNING id, description, status, due_date""",
        (
            meeting_id,
            args["description"],
            args.get("assigned_to"),
            args.get("due_date"),
        ),
        fetch="one"
    )

    return {
        "success": True,
        "action_item": item,
        "message": f"Action item '{item['description']}' berhasil dibuat"
    }


async def _update_action_item_status(args: dict):
    item_id = args["item_id"]
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]
    status = args["status"]

    # Cek role
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] not in ("host", "secretary"):
        raise Exception("Hanya host dan secretary yang dapat mengubah action item")

    execute_query(
        "UPDATE action_items SET status = %s WHERE id = %s AND meeting_id = %s",
        (status, item_id, meeting_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Status action item berhasil diubah menjadi '{status}'"
    }

async def _delete_action_item(args: dict):
    item_id = args["item_id"]
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]

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

    # Cek role
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] not in ("host", "secretary"):
        raise Exception("Hanya host dan secretary yang dapat mengubah action item")

    action_item = execute_query(
        """SELECT id, meeting_id, carried_from_id, description, assigned_to, due_date, status, created_at
            FROM action_items
            WHERE id = %s AND meeting_id = %s""",
        (item_id, meeting_id),
        fetch="one"
    )

    if not action_item:
        raise Exception("Action item tidak ditemukan")

    execute_query(
        "DELETE FROM action_items WHERE id = %s AND meeting_id = %s",
        (item_id, meeting_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Action item: {action_item['description']} berhasil dihapus"
    }

async def _update_action_item_status_by_description(args: dict):
    meeting_id = args["meeting_id"]
    description = args["description"].strip()
    user_id = args["user_id"]
    status = args["status"]

    # Cek role
    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] not in ("host", "secretary"):
        raise Exception("Hanya host dan secretary yang dapat mengubah action item")

    # Cari action item berdasarkan deskripsi di meeting yang sama
    items = execute_query(
        """
        SELECT id, description, status, created_at FROM action_items WHERE meeting_id = %s
        AND description ILIKE %s
        ORDER BY created_at ASC
        """,
        (meeting_id, f"%{description}%")
    )

    if not items:
        raise Exception("Action item tidak ditemukan")

    if len(items) > 1:
        return {
            "success": False,
            "message": "Ditemukan beberapa action item yang mirip",
            "matches": [
                {
                    "id": item["id"],
                    "description": item["description"],
                    "status": item["status"]
                }
                for item in items
            ]
        }

    item = items[0]

    execute_query(
        "UPDATE action_items SET status = %s WHERE id = %s AND meeting_id = %s",
        (status, item["id"], meeting_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Status action item '{item['description']}' berhasil diubah menjadi '{status}'",
        "action_item": {
            "id": item["id"],
            "description": item["description"],
            "status": status
        }
    }

async def _get_action_items_by_meeting(args: dict):
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]
    status = args.get("status", "all")

    # Cek akses
    access = execute_query(
        "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not access:
        raise Exception("Kamu tidak memiliki akses ke meeting ini")

    if status == "all":
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                u.name as assigned_to_name
                FROM action_items ai
                LEFT JOIN users u ON ai.assigned_to = u.id
                WHERE ai.meeting_id = %s
                ORDER BY ai.created_at ASC""",
            (meeting_id,)
        )
    else:
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                u.name as assigned_to_name
                FROM action_items ai
                LEFT JOIN users u ON ai.assigned_to = u.id
                WHERE ai.meeting_id = %s AND ai.status = %s
                ORDER BY ai.created_at ASC""",
            (meeting_id, status)
        )

    return {
        "success": True,
        "action_items": items,
        "total": len(items)
    }