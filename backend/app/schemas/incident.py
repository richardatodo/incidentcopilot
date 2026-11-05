import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


IncidentSeverity = Literal["LOW", "MEDIUM", "HIGH", "CRITICAL"]
IncidentStatus = Literal["OPEN", "INVESTIGATING", "RESOLVED"]


class IncidentCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=255)
    severity: IncidentSeverity

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("title must not be blank")
        return value


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime


class IncidentLogAssociationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    log_ids: list[uuid.UUID] = Field(min_length=1, max_length=100)

    @field_validator("log_ids")
    @classmethod
    def log_ids_must_be_unique(cls, value: list[uuid.UUID]) -> list[uuid.UUID]:
        if len(value) != len(set(value)):
            raise ValueError("log_ids must not contain duplicates")
        return value


class IncidentTimelineEvent(BaseModel):
    event_type: Literal["observed_log", "correlation"]
    timestamp: datetime
    log_id: uuid.UUID
    related_log_id: uuid.UUID | None = None
    source: str | None = None
    severity: str | None = None
    service: str | None = None
    message: str | None = None
    relationship_type: str | None = None
    relevance_score: float | None = Field(default=None, ge=0.0, le=1.0)
    reason: str | None = None
