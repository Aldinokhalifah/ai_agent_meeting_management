from openai import AsyncOpenAI
from core.config import OPENROUTER_API_KEY, OPENROUTER_MODEL
from schemas.chat import ChatResponse
import json
import traceback

# Setup OpenRouter client
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# System prompt untuk agent
SYSTEM_PROMPT = """
Kamu adalah asisten meeting management yang membantu user mengelola meeting mereka.
Kamu berbicara dalam Bahasa Indonesia yang natural dan ramah.

Kamu bisa membantu:
- Membuat, melihat, dan mengelola meeting
- Menambahkan peserta ke meeting
- Membuat dan mengelola action items
- Melihat jadwal hari ini
- Mencari informasi meeting

Aturan penting:
- Selalu gunakan tools yang tersedia untuk mengambil atau mengubah data
- Jangan mengarang data — selalu ambil dari tools
- Jika user menyebut lokasi yang tidak ada, tanyakan ruangan mana yang ingin dipakai
- Kalau user minta buat meeting tapi detail kurang lengkap, tanyakan dulu sebelum eksekusi
- Jawab dengan ringkas dan jelas
- Format tanggal dalam Bahasa Indonesia yang mudah dipahami
- Kalau ada error dari tool, sampaikan dengan bahasa yang ramah
- Untuk waktu, selalu konversi ke format ISO 8601 (contoh: 2025-05-01T09:00:00)
- Jika user bilang 'hari ini', gunakan tanggal hari ini
- Jika user bilang 'besok', gunakan tanggal besok
"""

async def run_agent(message: str, user_id: str, history: list) -> ChatResponse:
    # Import tools di sini untuk menghindari circular import
    from tools import get_all_tools, execute_tool

    tools = get_all_tools()
    actions_taken = []

    # Bangun conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Tambahkan history sebelumnya
    for h in history:
        messages.append({"role": h.role, "content": h.content})

    # Tambahkan pesan user terbaru
    messages.append({"role": "user", "content": message})

    # Agent loop — maksimal 5 iterasi untuk hindari infinite loop
    max_iterations = 5
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Kirim ke LLM
        response = await client.chat.completions.create(
            model=OPENROUTER_MODEL,
            messages=messages,
            tools=tools,
            tool_choice="auto",
            max_tokens=1000,
            temperature=0.3,
            extra_headers={
                "HTTP-Referer": "http://localhost:3000",
                "X-Title": "Meeting Management App",
            }
        )

        choice = response.choices[0]
        message_response = choice.message

        # Tambahkan response LLM ke history
        messages.append({
            "role": "assistant",
            "content": message_response.content or "",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments
                    }
                }
                for tc in (message_response.tool_calls or [])
            ] if message_response.tool_calls else None
        })

        # Kalau tidak ada tool call → LLM sudah selesai
        if not message_response.tool_calls:
            return ChatResponse(
                response=message_response.content or "Maaf, aku tidak bisa memproses permintaan ini.",
                actions_taken=actions_taken
            )

        # Eksekusi semua tool calls
        for tool_call in message_response.tool_calls:
            tool_name = tool_call.function.name
            tool_args = json.loads(tool_call.function.arguments)

            # Selalu inject user_id ke setiap tool call
            tool_args["user_id"] = user_id

            actions_taken.append(tool_name)

            try:
                tool_result = await execute_tool(tool_name, tool_args)
                result_str = json.dumps(tool_result, ensure_ascii=False, default=str)
            except Exception as e:
                # Tambahkan print untuk debug
                print(f"[Tool Error] {tool_name}: {str(e)}")
                traceback.print_exc()
                result_str = json.dumps({
                    "error": True,
                    "message": str(e)
                }, ensure_ascii=False)

            # Tambahkan hasil tool ke history
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result_str,
            })

    # Kalau sudah max iterasi tapi belum selesai
    return ChatResponse(
        response="Maaf, permintaanmu terlalu kompleks untuk diproses sekarang. Coba pecah menjadi beberapa permintaan yang lebih sederhana.",
        actions_taken=actions_taken
    )