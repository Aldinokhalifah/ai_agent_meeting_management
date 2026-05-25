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
                        "enum": ["open", "done", "carried_over", "all"],
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
            "description": "Mengubah status action item menjadi selesai (done), dibuka kembali (open), atau carried over berdasarkan item_id.",
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
                        "enum": ["open", "done", "carried_over"],
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
                        "enum": ["open", "done", "carried_over"],
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
                        "enum": ["open", "done", "carried_over", "all"],
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
                ORDER BY ai.due_date ASC NULLS LAST
                LIMIT 20""",
            (user_id,),
            fetch="all"
        )
    else:
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                m.title as meeting_title, m.id as meeting_id
                FROM action_items ai
                JOIN meetings m ON ai.meeting_id = m.id
                WHERE ai.assigned_to = %s AND ai.status = %s
                ORDER BY ai.due_date ASC NULLS LAST
                LIMIT 20""",
            (user_id, status),
            fetch="all"
        )

    return {
        "success": True,
        "action_items": items,
        "total": len(items)
    }


async def _create_action_item(args: dict):
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]
    description = (args.get("description") or "").strip()
    assigned_to = args.get("assigned_to")
    due_date = args.get("due_date")

    if not description:
        raise Exception("DESCRIPTION_REQUIRED")

    if due_date:
        try:
            from datetime import datetime
            is_valid_date = not isinstance(datetime.fromisoformat(due_date), type(None))
        except Exception:
            raise Exception("INVALID_DATE_FORMAT")

        from datetime import datetime
        due_dt = datetime.fromisoformat(due_date)
        today = datetime.now()
        today = today.replace(hour=0, minute=0, second=0, microsecond=0)
        if due_dt < today:
            raise Exception("DUE_DATE_IN_THE_PAST")

    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )
    if not role or role["role"] not in ("host", "secretary"):
        raise Exception("Hanya host dan secretary yang dapat membuat action item")

    if assigned_to is not None:
        assignee_is_participant = execute_query(
            "SELECT 1 FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
            (meeting_id, assigned_to),
            fetch="one"
        )
        if not assignee_is_participant:
            raise Exception("ASSIGNEE_MUST_BE_PARTICIPANT")

    item = execute_query(
        """INSERT INTO action_items (meeting_id, description, assigned_to, due_date)
           VALUES (%s, %s, %s, %s)
           RETURNING id, description, status, due_date""",
        (
            meeting_id,
            description,
            assigned_to,
            due_date,
        ),
        fetch="one"
    )

    return {
        "success": True,
        "action_item": item,
        "message": f"Action item '{item['description']}' berhasil dibuat"
    }


def _assert_can_update_action_item_status(role: dict | None, assigned_to, user_id: str, current_status: str, new_status: str):
    is_host_or_secretary = role and role["role"] in ("host", "secretary")
    is_assignee = str(assigned_to) == str(user_id)

    if is_host_or_secretary:
        return

    if is_assignee:
        if current_status == "carried_over":
            raise Exception("ACTION_ITEM_CANNOT_BE_UPDATED")
        if new_status == "done":
            return
        raise Exception("ASSIGNEE_CAN_ONLY_MARK_DONE")

    raise Exception("Kamu tidak memiliki izin untuk mengubah action item ini")


async def _update_action_item_status(args: dict):
    item_id = args["item_id"]
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]
    status = args["status"]

    action_item = execute_query(
        """SELECT id, description, assigned_to, status
           FROM action_items
           WHERE id = %s AND meeting_id = %s""",
        (item_id, meeting_id),
        fetch="one"
    )
    if not action_item:
        raise Exception("Action item tidak ditemukan")

    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )

    _assert_can_update_action_item_status(
        role,
        action_item["assigned_to"],
        user_id,
        action_item["status"],
        status
    )

    execute_query(
        "UPDATE action_items SET status = %s WHERE id = %s AND meeting_id = %s",
        (status, item_id, meeting_id),
        fetch="none"
    )

    return {
        "success": True,
        "message": f"Status action item '{action_item['description']}' berhasil diubah menjadi '{status}'"
    }


async def _update_action_item_status_by_description(args: dict):
    meeting_id = args["meeting_id"]
    description = (args["description"] or "").strip()
    user_id = args["user_id"]
    status = args["status"]

    if not description:
        raise Exception("DESCRIPTION_REQUIRED")

    items = execute_query(
        """
        SELECT id, description, status, assigned_to, created_at
        FROM action_items
        WHERE meeting_id = %s AND description ILIKE %s
        ORDER BY created_at ASC
        """,
        (meeting_id, f"%{description}%"),
        fetch="all"
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

    role = execute_query(
        "SELECT role FROM meeting_participants WHERE meeting_id = %s AND user_id = %s",
        (meeting_id, user_id),
        fetch="one"
    )

    _assert_can_update_action_item_status(
        role,
        item["assigned_to"],
        user_id,
        item["status"],
        status
    )

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


async def _delete_action_item(args: dict):
    item_id = args["item_id"]
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]

    meeting = execute_query(
        """SELECT id, title, description, scheduled_at, end_time,
            location, status, created_by
            FROM meetings WHERE id = %s""",
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


async def _get_action_items_by_meeting(args: dict):
    meeting_id = args["meeting_id"]
    user_id = args["user_id"]
    status = args.get("status", "all")

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
            (meeting_id,),
            fetch="all"
        )
    else:
        items = execute_query(
            """SELECT ai.id, ai.description, ai.status, ai.due_date,
                u.name as assigned_to_name
                FROM action_items ai
                LEFT JOIN users u ON ai.assigned_to = u.id
                WHERE ai.meeting_id = %s AND ai.status = %s
                ORDER BY ai.created_at ASC""",
            (meeting_id, status),
            fetch="all"
        )

    return {
        "success": True,
        "action_items": items,
        "total": len(items)
    }