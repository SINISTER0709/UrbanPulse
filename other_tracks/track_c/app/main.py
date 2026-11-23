from fastapi import FastAPI
from app.evidence_router import router as evidence_router

app = FastAPI(title="Track C - YOLO Image Verification")
app.include_router(evidence_router)


@app.get("/health")
def health():
    return {"status": "ok"}
