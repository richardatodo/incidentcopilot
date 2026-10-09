import uuid
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now


class Diagnosis(Base):
    __tablename__ = "diagnoses"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("incidents.id", ondelete="CASCADE"),
        nullable=False,
    )
    incident_title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    error_summary: Mapped[str] = mapped_column(Text, nullable=False)
    likely_root_cause: Mapped[str] = mapped_column(Text, nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    raw_response: Mapped[dict | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    incident: Mapped["Incident"] = relationship(
        back_populates="diagnoses",
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="diagnosis",
        cascade="all, delete-orphan",
    )