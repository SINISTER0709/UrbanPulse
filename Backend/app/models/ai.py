import uuid
from datetime import datetime
from sqlalchemy import String, Float, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class AIPrediction(Base):
    """
    Downstream AI classification, severity estimation, duplicate detection, and embedding metadata.
    Decoupled from ingestion to maintain fault tolerance.
    """
    __tablename__ = "ai_predictions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: f"pred_{uuid.uuid4().hex[:10]}")
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    
    predicted_category: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    severity_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    is_duplicate: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    duplicate_of_report_id: Mapped[str | None] = mapped_column(String(36), nullable=True)
    
    # Data source tag
    data_source: Mapped[str] = mapped_column(String(64), default="ai_inference", nullable=False, index=True)

    raw_response: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="ai_predictions")
