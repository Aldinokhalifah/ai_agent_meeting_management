# AI Agent Meeting Management

Backend **FastAPI** untuk asisten meeting berbasis LLM: model dipanggil lewat **OpenRouter** (API kompatibel OpenAI), dengan **tool calling** ke PostgreSQL untuk meeting, peserta, action items, dan info jadwal/ruangan.

## Fitur utama

- Chat satu endpoint (`POST /chat`) yang menjalankan loop agen: LLM memilih dan mengeksekusi tools sampai menghasilkan jawaban akhir (Bahasa Indonesia).
- Tools dikelompokkan di `app/tools/` dan diregistrasi di `app/tools/__init__.py` (`get_all_tools`, `execute_tool`).
- Konfigurasi lingkungan dan konstanta aplikasi di `app/core/config.py`.
- `app/agent.py` memuat **system prompt**, membangun riwayat percakapan, menyuntikkan `user_id` ke setiap pemanggilan tool, dan membatasi iterasi loop agen.

## Struktur folder (ringkas)


| Lokasi                           | Peran                                                                                                                                                   |
| -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `app/main.py`                    | Aplikasi FastAPI: CORS, route `health`, `test-connection`, `chat`.                                                                                      |
| `app/agent.py`                   | Orkestrasi agen: `AsyncOpenAI` → OpenRouter, pemanggilan tools, respons `ChatResponse`.                                                                 |
| `app/core/config.py`             | Memuat `.env`: `DATABASE_URL`, `OPENROUTER_*`, `APP_HOST`, `APP_PORT`.                                                                                  |
| `app/tools/__init__.py`          | Menggabungkan definisi tools dan routing eksekutor per domain.                                                                                          |
| `app/tools/meeting_tools.py`     | Meeting: buat, daftar, detail, cari, status, hapus, peserta, mendatang, catatan, ringkasan AI.                                                          |
| `app/tools/participant_tools.py` | Peserta: cari user, tambah/hapus, ubah peran.                                                                                                           |
| `app/tools/action_item_tools.py` | Action items: milik user, buat, status, hapus, per meeting.                                                                                             |
| `app/tools/info_tools.py`        | Jadwal hari ini dan daftar ruangan (tersedia).                                                                                                          |
| `app/tools/continuation_tools.py`| Continuation meeting: buat meeting lanjutan dan akses meeting sebelumnya.                                                                              |
| `app/services/llm.py`            | Helper **LangChain** `ChatOpenAI` menuju OpenRouter dengan logika fallback model otomatis saat model utama error. |
| `app/schemas/chat.py`            | Model `ChatRequest` / `ChatResponse` dan `Message` untuk riwayat.                                                                                       |


### Nama tools (referensi)

- **Meeting:** `create_meeting`, `get_meetings`, `get_meeting_detail`, `search_meetings`, `update_meeting_status`, `remove_meeting`, `get_meeting_participants`, `get_upcoming_meetings`, `get_meeting_notes`, `get_ai_summary`
- **Continuation:** `create_continuation_meeting`, `get_previous_meeting`
- **Peserta:** `search_user`, `add_participant`, `remove_participant`, `update_role_participant`
- **Action items:** `get_my_action_items`, `create_action_item`, `update_action_item_status`, `delete_action_item`, `get_action_items_by_meeting`
- **Info:** `get_today_schedule`, `get_rooms`

## Konfigurasi

1. Salin `.env.example` menjadi `.env` dan isi variabel yang dipakai aplikasi.
2. `**DATABASE_URL`** — connection string PostgreSQL (dipakai `app/db/postgres.py` untuk tools dan `GET /test-connection`).
3. `**OPENROUTER_API_KEY**` — wajib untuk agen.
4. `**OPENROUTER_MODEL**` atau `**PRIMARY_MODEL**` — model OpenRouter utama; default di kode: `openai/gpt-oss-120b:free`.
5. `**FALLBACK_MODEL**` — model cadangan untuk dipakai jika model utama error; default: `meta-llama/llama-3.3-70b-instruct:free`.
6. `**APP_HOST**` / `**APP_PORT**` — opsional; default `0.0.0.0` dan `8000`.

Variabel `POSTGRES_*` dan lainnya di `.env.example` bisa Anda pakai untuk menyusun `DATABASE_URL` secara manual atau di orchestration.

## Setup & menjalankan server

1. Buat dan aktifkan virtual environment (PowerShell):
  `.\.venv\Scripts\Activate.ps1`
2. Pasang dependensi:
  `pip install -r requirements.txt`
3. Jalankan API dari folder `**app**` (import memakai modul setara `main`, `agent`, `core`, …):
  ```powershell
   cd app
   python -m uvicorn main:app --reload
  ```
   Alternatif:
   `python main.py`

## Endpoint HTTP


| Method | Path               | Keterangan                                                                                                                 |
| ------ | ------------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `GET`  | `/health`          | Status layanan.                                                                                                            |
| `GET`  | `/test-connection` | Tes koneksi DB (`SELECT NOW()`).                                                                                           |
| `POST` | `/chat`            | Body JSON: `message`, `user_id`, `conversation_history`. Respons: `response`, `actions_taken` (nama tools yang dipanggil). |


**Catatan:** Tidak ada prefix `/api` pada route yang aktif di `app/main.py`.

## Body contoh untuk `/chat`

```json
{
  "message": "Apa jadwalku hari ini?",
  "user_id": "user-123",
  "conversation_history": []
}
```

Dependencies utama: lihat `requirements.txt` (`fastapi`, `uvicorn`, `openai`, `psycopg2-binary`, `python-dotenv`, `pydantic`, `langchain`, `langchain-openai`).