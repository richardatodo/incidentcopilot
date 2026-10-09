import uuid

from sqlalchemy import Float, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base


class IncidentLog(Base):
    __tablename__ = "incident_logs"

    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        primary_key=True,
    )
    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("logs.id", ondelete="CASCADE"),
        primary_key=True,
    )
    relevance_score: Mapped[float | None] = mapped_column(Float)
    relationship_type: Mapped[str | None] = mapped_column(String(100))

    incident: Mapped["Incident"] = relationship(
        back_populates="incident_logs",
    )
    log: Mapped["Log"] = relationship(
        back_populates="incident_logs",
    )