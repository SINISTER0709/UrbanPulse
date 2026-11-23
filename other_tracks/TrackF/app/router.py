from datetime import datetime
from typing import Literal
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.priority_engine import score_from_normalized_factors, score_incident
from app.dedup_service import find_duplicate_candidates
from fastapi import Query
from app.hotspot_service import compute_hotspots_and_trends
from app.rag_service import generate_action_brief

router = APIRouter(prefix="/api", tags=["Track F - Geospatial, Priority & RAG"])


class RawFactorsRequest(BaseModel):
    S: float = Field(..., ge=0, le=100)
    R: float = Field(..., ge=0, le=100)
    T: float = Field(..., ge=0, le=100)
    L: float = Field(..., ge=0, le=100)
    E: float = Field(..., ge=0, le=100)
    severity_label: Literal["Low", "Medium", "High", "Critical"] | None = None
    text: str | None = None


class IncidentPriorityRequest(BaseModel):
    severity: Literal["Low", "Medium", "High", "Critical"]
    report_count: int = Field(default=1, ge=1)
    unresolved_days: float | None = Field(default=None, ge=0)
    created_at: datetime | None = None
    lat: float | None = Field(default=None, ge=-90, le=90)
    lng: float | None = Field(default=None, ge=-180, le=180)
    location_context: str | None = None
    escalation_level: Literal["none", "mild", "moderate", "confirmed_worsening"] | None = None
    severity_history: list[str] | None = None
    reopen_count: int = Field(default=0, ge=0)
    worsening_reports: int = Field(default=0, ge=0)
    text: str | None = None


@router.post("/priority/calculate")
def calculate_priority_from_factors(payload: RawFactorsRequest):
    """Exact Track F contract endpoint for normalized 0-100 factors."""
    res = score_from_normalized_factors(
        S=payload.S,
        R=payload.R,
        T=payload.T,
        L=payload.L,
        E=payload.E,
        severity_label=payload.severity_label,
        text=payload.text,
    )
    return {
        "priority_score": res["priority_score"],
        "breakdown": res["breakdown"],
        "urgent_review_flag": res["urgent_review_flag"],
    }


@router.post("/priority/score-incident")
def calculate_priority_from_incident(payload: IncidentPriorityRequest):
    """Computes S, R, T, L (via POI lookup), and E from raw incident metadata."""
    try:
        return score_incident(**payload.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

class MatchIncidentRequest(BaseModel):
    report_id: str | None = None
    text: str = Field(..., min_length=3, max_length=2000)
    category: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    created_at: datetime | None = None


@router.post("/incidents/match")
def match_duplicate_incidents(payload: MatchIncidentRequest):
    """Spatial + category + time + Sentence-Transformer duplicate candidate matching."""
    return find_duplicate_candidates(
        text=payload.text,
        category=payload.category,
        lat=payload.lat,
        lng=payload.lng,
        created_at=payload.created_at,
        report_id=payload.report_id,
    )

@router.get("/analytics/hotspots")
def get_incident_hotspots(
    category: str | None = Query(default=None),
    days: int = Query(default=30, ge=1, le=365),
    data_source: str | None = Query(default=None),
):
    """DBSCAN + GeoPandas hotspot clustering on distinct incidents + category trends."""
    return compute_hotspots_and_trends(
        category=category,
        days=days,
        data_source=data_source,
    )

class ActionBriefRequest(BaseModel):
    incident_id: str | None = None
    category: str
    severity: Literal["Low", "Medium", "High", "Critical"]
    location_context: str = "low_exposure"
    summary_text: str | None = None


@router.post("/incidents/{incident_id}/action-brief")
def create_incident_action_brief(incident_id: str, payload: ActionBriefRequest):
    """Retrieves SOP chunks from ChromaDB and drafts a cited advisory brief via Llama 3.2."""
    return generate_action_brief(
        incident_id=incident_id,
        category=payload.category,
        severity=payload.severity,
        location_context=payload.location_context,
        summary_text=payload.summary_text,
    )