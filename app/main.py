from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from schemas.chat import ChatRequest, ChatResponse
from agent import run_agent
from core.config import APP_HOST, APP_PORT
import uvicorn

app = FastAPI(title="Meeting Management AI Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health():
    return { "status": "ok", "service": "Meeting AI Agent" }

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = await run_agent(
            message=request.message,
            user_id=request.user_id,
            history=request.conversation_history,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host=APP_HOST, port=APP_PORT, reload=True)