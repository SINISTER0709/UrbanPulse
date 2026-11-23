from fastapi import FastAPI
from app.config import LLM_BASE_URL, LLM_MODEL
from app.router import router as analyze_router

app = FastAPI(title="UrbanPulse AI — Track A Classification Service")
app.include_router(analyze_router)


@app.get("/health")
def health():
    return {"status": "ok", "model": LLM_MODEL, "base_url": LLM_BASE_URL}