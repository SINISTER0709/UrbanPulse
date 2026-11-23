from typing import Literal
from datetime import datetime
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.llm_client import classify_complaint_text
from app.services.ml_severity import estimate_severity_text

router = APIRouter(prefix="/analyze", tags=["Track A & B - AI Analysis"])


class AnalyzeCategoryRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000, description="Complaint free text")


class AnalyzeCategoryResponse(BaseModel):
    category: str
    department: str
    fallback_used: bool = False


class AnalyzeSeverityRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=2000, description="Complaint free text")
    submitted_at: datetime | str | None = None


class AnalyzeSeverityResponse(BaseModel):
    severity: Literal["Low", "Medium", "High", "Critical"]
    model_confidence: float


@router.post("/category", response_model=AnalyzeCategoryResponse)
def analyze_category(payload: AnalyzeCategoryRequest) -> AnalyzeCategoryResponse:
    """
    Track A: Classify free-text complaints into one of 6 fixed categories with department mapping.
    Input: {"text": "Large pothole outside ABC School causing traffic problems."}
    Output: {"category": "road_damage", "department": "Public Works", "fallback_used": false}
    """
    res = classify_complaint_text(payload.text)
    return AnalyzeCategoryResponse(
        category=res["category"],
        department=res["department"],
        fallback_used=res.get("fallback_used", False),
    )


@router.post("/severity", response_model=AnalyzeSeverityResponse)
def analyze_severity(payload: AnalyzeSeverityRequest) -> AnalyzeSeverityResponse:
    """
    Track B: Estimate complaint severity independently from text and submission features without image inputs.
    Input: {"text": "Large pothole outside ABC School causing traffic problems.", "submitted_at": "..."}
    Output: {"severity": "High", "model_confidence": 0.86}
    """
    sub_str = str(payload.submitted_at) if payload.submitted_at else None
    res = estimate_severity_text(payload.text, submitted_at=sub_str)
    return AnalyzeSeverityResponse(
        severity=res["severity"],
        model_confidence=res["model_confidence"],
    )
