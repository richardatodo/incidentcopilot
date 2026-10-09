import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IncidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str
    severity: str
    status: str
    started_at: datetime | None
    ended_at: datetime | None
    created_at: datetime
    updated_at: datetime