from openai import AsyncOpenAI
from core.config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL
from services.llm import chat_completions_with_fallback
from schemas.chat import ChatResponse
import json
import traceback
from utils.system_prompt import SYSTEM_PROMPT

# Setup OpenRouter client
client = AsyncOpenAI(
    base_url=OPENROUTER_BASE_URL,
    api_key=OPENROUTER_API_KEY,
)

async def run_agent(message: str, user_id: str, history: list) -> ChatResponse:
    # Import tools di sini untuk menghindari circular import
    from tools import get_all_tools, execute_tool

    tools = get_all_tools()
    actions_taken = []

    # Bangun conversation history
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Tambahkan history sebelumnya
    for h in history[:-1]:  # ← [:-1] skip item terakhir
        messages.append({"role": h.role, "content": h.content})

    # Tambahkan pesan user terbaru
    messages.append({"role": "user", "content": message})

    print(f"\n[Agent] History received: {len(history)} messages")
    print(f"[Agent] Messages to LLM: {len(messages)} (after processing)")
    # Agent loop — maksimal 5 iterasi untuk hindari infinite loop
    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1

        # Kirim ke LLM (primary, lalu fallback jika error)
        response = await chat_completions_with_fallback(
            client,
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