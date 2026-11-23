import uuid
from datetime import datetime
from sqlalchemy import String, Text, Float, Boolean, DateTime, ForeignKey, Index, Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base, SpatialPoint
from app.models.enums import Day0Category, ReportStatus, DataSource


def generate_report_id() -> str:
    """Generates a standardized report ID prefixed with 'rpt_' per specification."""
    return f"rpt_{uuid.uuid4().hex[:10]}"


class Report(Base):
    """
    Citizen complaint submission record.
    Must be persisted immediately upon submission with:
    - status = received_pending_ai
    - data_source = user_submitted
    - consent = true
    - PostGIS spatial point with GIST index
    """
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=generate_report_id)
    user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Description & locked Day-0 classification (initial submission can be unclassified or AI-pending)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    category: Mapped[Day0Category | None] = mapped_column(
        SAEnum(Day0Category, name="day0_category_enum", native_enum=False),
        nullable=True,
        index=True
    )

    # Ingestion metadata
    status: Mapped[str] = mapped_column(String(64), default=ReportStatus.received_pending_ai.value, nullable=False, index=True)
    data_source: Mapped[str] = mapped_column(String(64), default=DataSource.user_submitted.value, nullable=False, index=True)
    
    # Minimal data with explicit consent
    consent: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Spatial fields & PostGIS Point (SRID 4326)
    location = mapped_column(SpatialPoint, nullable=True)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Incident grouping link
    incident_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="reports")
    incident = relationship("Incident", back_populates="reports")
    ai_predictions = relationship("AIPrediction", back_populates="report", cascade="all, delete-orphan")
    image_evidence = relationship("ImageEvidence", back_populates="report", cascade="all, delete-orphan")
    admin_reviews = relationship("AdminReview", back_populates="report", cascade="all, delete-orphan")
    status_history = relationship("StatusHistory", back_populates="report", cascade="all, delete-orphan")

    __table_args__ = (
        Index("idx_reports_datasource_status", "data_source", "status"),
        Index("idx_reports_coords", "latitude", "longitude"),
    )
