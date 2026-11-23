from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from app.models.enums import Day0Category, IncidentStatus, IncidentPriority
from app.schemas.report import format_utc_z, ReportDetailResponse


class AdminOverrideRequest(BaseModel):
    """
    Admin human-in-the-loop override schema.
    Example: PATCH /api/incidents/inc_42/override {"severity": "Critical", "reason": "School bus route blocked"}
    """
    severity: Optional[str] = Field(None, description="Override severity (Low, Medium, High, Critical)")
    category: Optional[Day0Category] = Field(None, description="Override Day-0 category")
    priority: Optional[IncidentPriority] = Field(None, description="Override incident priority tier")
    reason: str = Field(..., min_length=3, description="Auditable justification for the override")


class DuplicateDecisionRequest(BaseModel):
    report_id: str = Field(..., description="ID of candidate report")
    is_duplicate: bool = Field(..., description="True to confirm duplicate and merge; False to split")
    reason: Optional[str] = Field(None, description="Explanation for decision")


class StatusTransitionRequest(BaseModel):
    status: IncidentStatus = Field(..., description="New lifecycle status")
    notes: Optional[str] = Field(None, description="Reason or notes for status transition")


class AssignmentRequest(BaseModel):
    department_name: str = Field(..., description="Department assigned (e.g. Public Works)")
    assigned_user_id: Optional[str] = None
    notes: Optional[str] = None
    due_date: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    department_name: str
    assigned_user_id: Optional[str] = None
    status: str
    notes: Optional[str] = None
    assigned_at: str

    @field_serializer("assigned_at")
    def serialize_assigned_at(self, value: datetime | str) -> str:
        return format_utc_z(value)


class AdminReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    decision: str
    notes: Optional[str] = None
    reviewer_user_id: str
    reviewed_at: str

    @field_serializer("reviewed_at")
    def serialize_reviewed_at(self, value: datetime | str) -> str:
        return format_utc_z(value)


class LocationCoords(BaseModel):
    latitude: float
    longitude: float


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    summary_text: str
    category: Day0Category
    status: IncidentStatus
    priority: IncidentPriority
    severity: str
    priority_score: float
    score_breakdown: Optional[Dict[str, float]] = None
    urgent_review_flag: bool
    image_verdict: Optional[str] = None
    data_source: str
    latitude: float
    longitude: float
    location: Optional[LocationCoords] = None
    address: Optional[str] = None
    photos: List[str] = []
    created_at: str
    updated_at: str
    linked_reports_count: int = 1
    reports: List[ReportDetailResponse] = []
    assignments: List[AssignmentResponse] = []
    admin_reviews: List[AdminReviewResponse] = []

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime | str) -> str:
        return format_utc_z(value)

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime | str) -> str:
        return format_utc_z(value)


class IncidentDetailResponse(IncidentResponse):
    linked_reports: List[ReportDetailResponse] = []

