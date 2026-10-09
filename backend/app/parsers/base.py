from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True, slots=True)
class NormalizedLog:
    source: str
    timestamp: datetime
    severity: str
    service: str | None
    event_type: str
    message: str
    metadata: dict[str, object]
    raw_message: str


class LogParser(Protocol):
    def parse(self, payload: object) -> NormalizedLog:
        """Convert a validated source payload to the common event model."""
        ...
