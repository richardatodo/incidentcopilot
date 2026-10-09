import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class LogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    source: str
    timestamp: datetime
    severity: str
    service: str | None
    event_type: str | None
    message: str
    metadata: dict[str, Any] = Field(validation_alias="log_metadata")
    raw_message: str
    created_at: datetime