import uuid
from datetime import datetime

from sqlalchemy import DateTime, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.models.base import Base, generate_uuid, utc_now


class Incident(Base):
    __tablename__ = "incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=generate_uuid,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    severity: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    ended_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True)
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        onupdate=utc_now,
    )

    incident_logs: Mapped[list["IncidentLog"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    diagnoses: Mapped[list["Diagnosis"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )
    investigation_steps: Mapped[list["InvestigationStep"]] = relationship(
        back_populates="incident",
        cascade="all, delete-orphan",
    )