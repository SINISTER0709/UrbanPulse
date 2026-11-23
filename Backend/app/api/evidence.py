from typing import Annotated, Optional
from fastapi import APIRouter, File, Form, UploadFile
from pydantic import BaseModel

from app.services.yolo_evidence import verify_image_evidence

router = APIRouter(prefix="/evidence", tags=["Track C - Image Verification"])


class DetectionItem(BaseModel):
    label: str
    confidence: float


class EvidenceAnalyzeResponse(BaseModel):
    verdict: str
    detections: list[DetectionItem]
    scoring_weight: float = 0.0


@router.post("/analyze", response_model=EvidenceAnalyzeResponse)
async def analyze_evidence(
    reported_category: Annotated[str, Form(description="Category key against which to verify image")],
    image: Annotated[Optional[UploadFile], File(description="Optional image to verify")] = None,
) -> EvidenceAnalyzeResponse:
    """
    Track C: Check whether an optional citizen photo visually supports the reported category
    as evidence only, with strict 0% impact on severity or priority.
    Input: multipart/form-data: image=pothole.jpg, reported_category="road_damage"
    Output: {"verdict": "Visual Match", "detections": [{"label": "pothole", "confidence": 0.91}], "scoring_weight": 0.0}
    """
    raw_bytes = None
    if image is not None and image.filename:
        raw_bytes = await image.read()

    res = verify_image_evidence(raw_bytes, reported_category=reported_category)
    return EvidenceAnalyzeResponse(
        verdict=res["verdict"],
        detections=res.get("detections", []),
        scoring_weight=0.0,
    )
