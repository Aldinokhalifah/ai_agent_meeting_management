from db.postgres import execute_query
from datetime import datetime

ROOMS = [
    { "id": 1, "name": 'Ruang Rapat Lounge', "capacity": 10, "description": '' },
    { "id": 2, "name": 'Ruang Rapat Turbo', "capacity": 25, "description": '' },
    { "id": 3, "name": 'Ruang Rapat Piston', "capacity": 4, "description": '' },
    { "id": 4, "name": 'Ruang Rapat Kaca', "capacity": 4, "description": '' },
    { "id": 5, "name": 'Ruang Rapat Sales', "capacity": 6, "description": '' },
]

INFO_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_today_schedule",
            "description": "Mengambil jadwal meeting hari ini milik user.",
            "parameters": {
                "type": "object",
                "properties": {
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
            "name": "get_rooms",
            "description": "Mengambil informasi ruangan meeting yang tersedia beserta status ketersediaannya saat ini.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "ID user (diisi otomatis)"
                    }
                },
                "required": ["user_id"]
            }
        }
    }
]


async def execute_info_tool(tool_name: str, args: dict):
    if tool_name == "get_today_schedule":
        return await _get_today_schedule(args)
    elif tool_name == "get_rooms":
        return await _get_rooms(args)
    else:
        raise ValueError(f"Info tool '{tool_name}' tidak ditemukan")


async def _get_today_schedule(args: dict):
    user_id = args["user_id"]
    today = datetime.now().date()

    meetings = execute_query(
        """SELECT m.id, m.title, m.scheduled_at, m.end_time,
            m.location, m.status, mp.role as my_role
            FROM meetings m
            JOIN meeting_participants mp ON m.id = mp.meeting_id
            WHERE mp.user_id = %s
            AND DATE(m.scheduled_at) = %s
            AND m.status NOT IN ('cancelled')
            ORDER BY m.scheduled_at ASC""",
        (user_id, today)
    )

    return {
        "success": True,
        "date": str(today),
        "meetings": meetings,
        "total": len(meetings)
    }


async def _get_rooms(args: dict):
    # Cek ruangan yang sedang dipakai (ongoing)
    ongoing = execute_query(
        """SELECT location FROM meetings
            WHERE status = 'ongoing'
            AND location IS NOT NULL"""
    )

    occupied_locations = [m["location"] for m in ongoing]

    rooms_with_status = []
    for room in ROOMS:
        is_occupied = room["name"] in occupied_locations
        rooms_with_status.append({
            **room,
            "status": "occupied" if is_occupied else "available"
        })

    return {
        "success": True,
        "rooms": rooms_with_status
    }