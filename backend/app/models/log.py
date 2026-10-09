import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now


class Log(Base):
    __tablename__ = "logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    source: Mapped[str] = mapped_column(String(50), nullable=False)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    service: Mapped[str | None] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(100))
    message: Mapped[str] = mapped_column(Text, nullable=False)
    log_metadata: Mapped[dict] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        default=dict,
    )
    raw_message: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )

    incident_logs: Mapped[list["IncidentLog"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
    )
    evidence: Mapped[list["Evidence"]] = relationship(
        back_populates="log",
        cascade="all, delete-orphan",
    )