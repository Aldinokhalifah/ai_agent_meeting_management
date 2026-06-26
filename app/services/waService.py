from db.postgres import execute_query
from utils.normalize_phone import normalize_indonesia_whatsapp
from utils.wa_templates import invitation_message, meeting_summary_message
from utils.wa_client import send_whatsapp_text
from utils.tiptap_to_text import tiptap_to_text


async def send_invitation_whatsapp(recipient_phone, recipient_name, meeting: dict, host_name: str):
    to = normalize_indonesia_whatsapp(recipient_phone)
    if not to:
        raise Exception("Nomor WhatsApp penerima tidak valid")

    message = invitation_message(
        recipient_name=recipient_name,
        meeting_title=meeting["title"],
        scheduled_at=meeting["scheduled_at"],
        end_time=meeting.get("end_time"),
        location=meeting.get("location"),
        host_name=host_name,
    )

    result = await send_whatsapp_text(to, message)
    print(f"✓ WA undangan → {to}")
    return result


async def send_meeting_summary_whatsapps(meeting_id: str):
    meeting = execute_query(
        "SELECT id, title, scheduled_at, location, ai_summary FROM meetings WHERE id = %s",
        (meeting_id,),
        fetch="one",
    )
    if not meeting:
        raise Exception("Meeting tidak ditemukan")

    participants = execute_query(
        """
        SELECT u.id, u.name, u.whatsapp_phone
        FROM meeting_participants mp
        JOIN users u ON mp.user_id = u.id
        WHERE mp.meeting_id = %s
        """,
        (meeting_id,),
        fetch="all",
    )

    note = execute_query(
        "SELECT content FROM notes WHERE meeting_id = %s",
        (meeting_id,),
        fetch="one",
    )
    note_text = tiptap_to_text(note["content"]) if note and note.get("content") else None

    action_items = execute_query(
        "SELECT description, assigned_to, status FROM action_items WHERE meeting_id = %s",
        (meeting_id,),
        fetch="all",
    )

    results = []
    for participant in participants:
        to = normalize_indonesia_whatsapp(participant.get("whatsapp_phone"))
        if not to:
            results.append({"status": "skipped", "user_id": participant["id"], "reason": "invalid_phone"})
            continue

        my_action_items = [
            item for item in action_items
            if item["assigned_to"] == participant["id"] and item["status"] != "done"
        ]

        try:
            message = meeting_summary_message(
                recipient_name=participant["name"],
                meeting_title=meeting["title"],
                scheduled_at=meeting["scheduled_at"],
                location=meeting.get("location"),
                ai_summary=meeting.get("ai_summary"),
                note_text=note_text,
                my_action_items=my_action_items,
            )
            result = await send_whatsapp_text(to, message)
            print(f"✓ WA ringkasan meeting → {participant['name']} ({to})")
            results.append({"status": "fulfilled", "user_id": participant["id"], "result": result})
        except Exception as e:
            print(f"✗ WA ringkasan gagal → {participant['name']}: {e}")
            results.append({"status": "rejected", "user_id": participant["id"], "error": str(e)})

    ok = len([r for r in results if r["status"] == "fulfilled"])
    print(f"[WA Summary] meeting {meeting_id}: {ok}/{len(results)} terkirim")
    return results