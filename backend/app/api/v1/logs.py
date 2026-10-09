from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.log import Log
from backend.app.schemas.log import LogResponse


router = APIRouter(prefix="/logs", tags=["logs"])


@router.get("", response_model=list[LogResponse])
def list_logs(db: Session = Depends(get_db)) -> list[Log]:
    return list(
        db.scalars(
            select(Log).order_by(Log.timestamp.desc())
        ).all()
    )