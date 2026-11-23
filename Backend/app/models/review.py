import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AdminReview(Base):
    """
    Human-in-the-loop review and override audit records.
    Logs every override for incidents and reports per Track E2 requirements.
    """
    __tablename__ = "admin_reviews"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: f"rev_{uuid.uuid4().hex[:10]}")
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    incident_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    reviewer_user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="RESTRICT"), nullable=False)
    
    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # override, approved, rejected, modified, escalated
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)  # reason for override
    data_source: Mapped[str] = mapped_column(String(64), default="admin_portal", nullable=False)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="admin_reviews")
    incident = relationship("Incident", back_populates="admin_reviews")
