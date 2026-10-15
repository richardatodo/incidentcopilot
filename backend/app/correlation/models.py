"""Typed data contracts for deterministic log correlation."""
from dataclasses import dataclass
from datetime import datetime
from typing import Mapping
from uuid import UUID


@dataclass(frozen=True, slots=True)
class CorrelationEvent:
    """Persisted log represented independently of the ORM."""
    id: UUID
    source: str
    timestamp: datetime
    severity: str
    service: str | None
    event_type: str
    message: str
    metadata: Mapping[str, object]
    raw_message: str


@dataclass(frozen=True, slots=True)
class CorrelationSignal:
    """An explainable relationship pointing from a later event to a related event."""
    log_id: UUID
    related_log_id: UUID
    relevance_score: float
    relationship_type: str
    reason: str
