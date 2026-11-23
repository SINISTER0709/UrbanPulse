import uuid
from datetime import datetime
from sqlalchemy import String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class ImageEvidence(Base):
    """
    Photo and image attachments submitted with reports.
    """
    __tablename__ = "image_evidence"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: f"img_{uuid.uuid4().hex[:10]}")
    report_id: Mapped[str] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=False, index=True)
    
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(64), nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    verification_status: Mapped[str] = mapped_column(String(32), default="pending", nullable=False)

    # Data source tag
    data_source: Mapped[str] = mapped_column(String(64), default="user_upload", nullable=False, index=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="image_evidence")
