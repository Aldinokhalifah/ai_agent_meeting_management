# AI Agent Meeting Management

Starter project Python AI agent dengan FastAPI + LangChain.

## Setup

1. Aktifkan virtual environment:
   - PowerShell: `.\.venv\Scripts\Activate.ps1`
2. Salin `.env.example` menjadi `.env`, lalu isi nilainya.
3. Jalankan server:
   - `.\.venv\Scripts\python -m uvicorn app.main:app --reload`

## Endpoint

- `GET /api/health`
- `POST /api/chat`
