from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, field_serializer
from app.models.enums import Day0Category


def format_utc_z(dt: datetime | str) -> str:
    """Formats datetime as strict UTC ISO 8601 string ending in 'Z'."""
    if isinstance(dt, str):
        if not dt.endswith("Z") and "+" not in dt:
            return f"{dt}Z"
        return dt
    if dt.tzinfo is None:
        return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


class ComplaintCreateResponse(BaseModel):
    """
    Standard Fault-Tolerant Ingestion response.
    Returns immediately upon persistence.
    Example:
    201 Created {"report_id": "rpt_104", "status": "received_pending_ai",
                 "created_at": "2026-11-21T10:45:00Z", "data_source": "user_submitted"}
    """
    model_config = ConfigDict(from_attributes=True)

    report_id: str
    status: str
    created_at: str
    data_source: str

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime | str) -> str:
        return format_utc_z(value)


class ReportDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    description: str
    category: Day0Category | None = None
    status: str
    data_source: str
    latitude: float
    longitude: float
    address: Optional[str] = None
    consent: bool
    incident_id: Optional[str] = None
    incident_status: Optional[str] = None
    photos: List[str] = []
    created_at: str
    updated_at: str

    @field_serializer("created_at")
    def serialize_created_at(self, value: datetime | str) -> str:
        return format_utc_z(value)

    @field_serializer("updated_at")
    def serialize_updated_at(self, value: datetime | str) -> str:
        return format_utc_z(value)


class ComplaintListResponse(BaseModel):
    total: int
    items: List[ReportDetailResponse]
