from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.incident import Incident
from backend.app.schemas.incident import IncidentResponse


router = APIRouter(prefix="/incidents", tags=["incidents"])


@router.get("", response_model=list[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)) -> list[Incident]:
    return list(
        db.scalars(
            select(Incident).order_by(Incident.created_at.desc())
        ).all()
    )