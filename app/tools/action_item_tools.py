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
            "description": "Mengubah status action item menjadi selesai (done) atau dibuka kembali (open).",
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
    }
]


async def execute_action_item_tool(tool_name: str, args: dict):
    if tool_name == "get_my_action_items":
        return await _get_my_action_items(args)
    elif tool_name == "create_action_item":
        return await _create_action_item(args)
    elif tool_name == "update_action_item_status":
        return await _update_action_item_status(args)
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