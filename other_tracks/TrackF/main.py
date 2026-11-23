from fastapi import FastAPI
from app.router import router as track_f_router

app = FastAPI(title="UrbanPulse AI — Track F Service (Priority, Geo, Dedup & RAG)")
app.include_router(track_f_router)


@app.get("/health")
def health():
    return {"status": "ok", "service": "track-f"}