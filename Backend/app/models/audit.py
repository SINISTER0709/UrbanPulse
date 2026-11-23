import uuid
from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.models.base import Base


class PriorityHistory(Base):
    """
    Audit trail tracking changes to incident priorities.
    """
    __tablename__ = "priority_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    incident_id: Mapped[str] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    old_priority: Mapped[str] = mapped_column(String(32), nullable=False)
    new_priority: Mapped[str] = mapped_column(String(32), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    incident = relationship("Incident", back_populates="priority_history")


class StatusHistory(Base):
    """
    Audit trail tracking report and incident lifecycle transitions.
    """
    __tablename__ = "status_history"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    report_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("reports.id", ondelete="CASCADE"), nullable=True, index=True)
    incident_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=True, index=True)
    old_status: Mapped[str] = mapped_column(String(64), nullable=False)
    new_status: Mapped[str] = mapped_column(String(64), nullable=False)
    changed_by_user_id: Mapped[str | None] = mapped_column(String(36), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    changed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    report = relationship("Report", back_populates="status_history")
