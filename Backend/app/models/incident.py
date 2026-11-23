import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Boolean, DateTime, Enum as SAEnum, ForeignKey, Index, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship, synonym
from app.models.base import Base, SpatialPoint
from app.models.enums import Day0Category, IncidentStatus, IncidentPriority, DataSource


def generate_incident_id() -> str:
    return f"inc_{uuid.uuid4().hex[:10]}"


class Incident(Base):
    """
    Consolidated incident cluster grouping multiple citizen reports.
    Enriched through Stage E2 asynchronous pipeline processing.
    """
    __tablename__ = "incidents"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_incident_id)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    summary_text: Mapped[str] = mapped_column(Text, nullable=False)
    description = synonym("summary_text")

    category: Mapped[Day0Category] = mapped_column(
        SAEnum(Day0Category, name="incident_day0_category_enum", native_enum=False),
        nullable=False,
        index=True
    )
    status: Mapped[IncidentStatus] = mapped_column(
        SAEnum(IncidentStatus, name="incident_status_enum", native_enum=False),
        default=IncidentStatus.open,
        nullable=False,
        index=True
    )
    priority: Mapped[IncidentPriority] = mapped_column(
        SAEnum(IncidentPriority, name="incident_priority_enum", native_enum=False),
        default=IncidentPriority.medium,
        nullable=False,
        index=True
    )

    # Stage E2 Enriched Pipeline Attributes
    severity: Mapped[str] = mapped_column(String(32), default="Medium", nullable=False)  # Low, Medium, High, Critical
    priority_score: Mapped[float] = mapped_column(Float, default=50.0, nullable=False)
    urgent_review_flag: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    score_breakdown: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # {"S": 30.0, "R": 10.0, "T": 0.0, "L": 15.0, "E": 0.0}
    image_verdict: Mapped[str | None] = mapped_column(String(64), default="Not Provided", nullable=True)

    # Data source tag
    data_source: Mapped[str] = mapped_column(String(64), default=DataSource.user_submitted.value, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Centroid / location with PostGIS Spatial Point
    location = mapped_column(SpatialPoint, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    reports = relationship("Report", back_populates="incident")
    assignments = relationship("Assignment", back_populates="incident", cascade="all, delete-orphan")
    action_briefs = relationship("ActionBrief", back_populates="incident", cascade="all, delete-orphan")
    priority_history = relationship("PriorityHistory", back_populates="incident", cascade="all, delete-orphan")
    incident_reports = relationship("IncidentReport", back_populates="incident", cascade="all, delete-orphan")
    admin_reviews = relationship("AdminReview", back_populates="incident", cascade="all, delete-orphan")


class IncidentReport(Base):
    """
    Association table tracking which reports formed an incident with confidence scores.
    """
    __tablename__ = "incident_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: f"ir_{uuid.uuid4().hex[:10]}")
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    confidence_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)
    data_source: Mapped[str] = mapped_column(String(64), default="clustering_engine", nullable=False)
    linked_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="incident_reports")
