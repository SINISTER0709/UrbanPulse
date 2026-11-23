from datetime import datetime
from typing import Literal, Optional, Annotated
from fastapi import APIRouter, Query, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services.hotspot_service import compute_hotspots_and_trends
from app.services.dedup_service import find_duplicate_candidates
from app.services.priority_engine import score_from_normalized_factors, score_incident

router = APIRouter(tags=["Track F - Geospatial, Priority & Analytics"])


class RawFactorsRequest(BaseModel):
    S: float = Field(..., ge=0, le=100, description="Normalized Severity Factor (0-100)")
    R: float = Field(..., ge=0, le=100, description="Normalized Report Volume Factor (0-100)")
    T: float = Field(..., ge=0, le=100, description="Normalized Time Factor (0-100)")
    L: float = Field(..., ge=0, le=100, description="Normalized Location Risk Factor (0-100)")
    E: float = Field(..., ge=0, le=100, description="Normalized Escalation Factor (0-100)")
    severity_label: Optional[Literal["Low", "Medium", "High", "Critical"]] = None
    text: Optional[str] = None


class IncidentPriorityRequest(BaseModel):
    severity: Literal["Low", "Medium", "High", "Critical"]
    report_count: int = Field(default=1, ge=1)
    unresolved_days: Optional[float] = Field(default=None, ge=0)
    created_at: Optional[datetime] = None
    lat: Optional[float] = Field(default=None, ge=-90, le=90)
    lng: Optional[float] = Field(default=None, ge=-180, le=180)
    location_context: Optional[str] = None
    escalation_level: Optional[Literal["none", "mild", "moderate", "confirmed_worsening"]] = None
    severity_history: Optional[list[str]] = None
    reopen_count: int = Field(default=0, ge=0)
    worsening_reports: int = Field(default=0, ge=0)
    text: Optional[str] = None


class MatchIncidentRequest(BaseModel):
    report_id: Optional[str] = None
    text: str = Field(..., min_length=3, max_length=2000)
    category: str
    lat: float = Field(..., ge=-90, le=90)
    lng: float = Field(..., ge=-180, le=180)
    created_at: Optional[datetime] = None


@router.post("/priority/calculate", summary="Calculate Priority from Normalized Factors")
def calculate_priority_from_factors(payload: RawFactorsRequest):
    """
    Track F: Computes P = 0.40S + 0.20R + 0.15T + 0.15L + 0.10E from normalized 0-100 factors.
    Output: {"priority_score": 55.0, "breakdown": {"S": 30.0, "R": 10.0, "T": 0.0, "L": 15.0, "E": 0.0}, "urgent_review_flag": false}
    """
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


@router.post("/priority/score-incident", summary="Calculate Priority from Incident Metadata")
def calculate_priority_from_incident(payload: IncidentPriorityRequest):
    """
    Computes S, R, T, L (via POI proximity), and E from raw incident parameters.
    """
    return score_incident(**payload.model_dump())


@router.post("/incidents/match", summary="Find Spatial & Semantic Duplicate Candidates")
def match_duplicate_incidents(
    payload: MatchIncidentRequest,
    db: Annotated[Session, Depends(get_db)],
):
    """
    Track F: Deduplicate reports into distinct incidents (PostGIS radius + category/time + embeddings).
    Output: {"candidates": [{"incident_id": "inc_42", "similarity": 0.89, "distance_m": 35, "status": "needs_admin_confirmation"}]}
    """
    return find_duplicate_candidates(
        text=payload.text,
        category=payload.category,
        lat=payload.lat,
        lng=payload.lng,
        created_at=payload.created_at,
        report_id=payload.report_id,
        db=db,
    )


@router.get("/analytics/hotspots", summary="Get Geospatial Hotspots & Trends")
def get_incident_hotspots(
    category: Optional[str] = Query(default=None, description="Optional category filter"),
    days: int = Query(default=30, ge=1, le=365, description="Lookback window in days"),
    data_source: Optional[str] = Query(default=None, description="Optional data_source filter"),
    db: Annotated[Session, Depends(get_db)] = None,
):
    """
    Track F: DBSCAN clustering on distinct incidents + category & area trends.
    Output: {"clusters": [{"cluster_id": 1, "distinct_incidents": 12, "centroid": [28.45, 77.58]}], "trends": [{"category": "road_damage", "count": 19}]}
    """
    return compute_hotspots_and_trends(
        category=category,
        days=days,
        data_source=data_source,
        db=db,
    )
