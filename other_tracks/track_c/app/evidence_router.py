import io
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image, UnidentifiedImageError
from ultralytics import YOLO

router = APIRouter(prefix="/api/evidence", tags=["Track C - Image Evidence"])

WEIGHTS_PATH = Path("weights/best.pt")

LABEL_TO_CATEGORY = {
    "pothole":     "road_damage",
    "litter":      "garbage_sanitation",
    "streetlight": "streetlight_electrical",
    "water_leak":  "water_supply",
    "flooding":    "drainage_flooding",
}

MATCH_THRESH = {
    "pothole":     0.40,
    "litter":      0.25,
    "streetlight": 0.40,
    "water_leak":  0.35,
    "flooding":    0.40,
}

MIN_CONF = min(MATCH_THRESH.values())
CONF_MISMATCH = 0.55


@lru_cache(maxsize=1)
def get_model() -> YOLO:
    if not WEIGHTS_PATH.exists():
        raise FileNotFoundError(f"YOLO weights not found at {WEIGHTS_PATH.resolve()}")
    return YOLO(str(WEIGHTS_PATH))


@router.post("/analyze")
async def analyze_evidence(
    reported_category: str = Form(...),
    image: UploadFile | None = File(default=None),
):
    if image is None or not image.filename:
        return {"verdict": "Not Provided", "detections": [], "scoring_weight": 0.0}

    raw_bytes = await image.read()
    if not raw_bytes:
        return {"verdict": "Not Provided", "detections": [], "scoring_weight": 0.0}

    try:
        img = Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="Uploaded file is not a valid image.")

    model = get_model()
    result = model.predict(img, conf=MIN_CONF, iou=0.5, verbose=False)[0]

    detections = sorted(
        [
            {"label": result.names[int(b.cls[0])], "confidence": round(float(b.conf[0]), 2)}
            for b in result.boxes
            if float(b.conf[0]) >= MATCH_THRESH.get(result.names[int(b.cls[0])], 0.40)
        ],
        key=lambda d: d["confidence"],
        reverse=True,
    )

    if reported_category not in LABEL_TO_CATEGORY.values() or not detections:
        verdict = "Inconclusive"
    elif any(LABEL_TO_CATEGORY[d["label"]] == reported_category for d in detections):
        verdict = "Visual Match"
    elif any(d["confidence"] >= CONF_MISMATCH for d in detections):
        verdict = "Mismatch"
    else:
        verdict = "Inconclusive"

    return {
        "verdict": verdict,
        "detections": detections,
        "scoring_weight": 0.0,
    }
