import httpx
from core.config import WHATSAPP_API_TOKEN, WHATSAPP_API_URL


async def send_whatsapp_text(to: str, message: str) -> dict:
    """
    Kirim pesan teks WhatsApp lewat HTTP (default: Fonnte).
    Override dengan WHATSAPP_API_URL di .env jika memakai provider lain
    yang kompatibel (POST form-urlencoded: target, message).
    """
    if not WHATSAPP_API_TOKEN:
        raise Exception("WHATSAPP_API_TOKEN tidak dikonfigurasi di .env")

    async with httpx.AsyncClient(timeout=15) as client:
        res = await client.post(
            WHATSAPP_API_URL,
            headers={"Authorization": WHATSAPP_API_TOKEN},
            data={"target": to, "message": message},
        )

    try:
        parsed = res.json()
    except ValueError:
        parsed = {"raw": res.text}

    if res.status_code >= 400:
        detail = parsed if isinstance(parsed, dict) else res.text
        raise Exception(f"WhatsApp API gagal ({res.status_code}): {detail}")

    return parsed