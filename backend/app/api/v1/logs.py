
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.models.log import Log
from backend.app.schemas.log import LogResponse
from backend.app.schemas.log_ingestion import (
    LogBatchIngestResponse,
    LogIngestRequest,
)
from backend.app.services.log_ingestion import (
    ingest_log,
    ingest_logs_batch,
)

router = APIRouter(prefix="/logs", tags=["logs"])


@router.post(
    "",
    response_model=LogResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_log(
    payload: LogIngestRequest,
    db: Session = Depends(get_db),
) -> Log:
    return ingest_log(db, payload)


@router.post(
    "/batch",
    response_model=LogBatchIngestResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_logs_batch(
    payloads: Annotated[
        list[LogIngestRequest],
        Field(min_length=1, max_length=100),
    ],
    db: Session = Depends(get_db),
) -> LogBatchIngestResponse:
    records = ingest_logs_batch(db, payloads)
    return LogBatchIngestResponse(count=len(records), logs=records)


@router.get("", response_model=list[LogResponse])
def list_logs(
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
    offset: Annotated[int, Query(ge=0)] = 0,
    db: Session = Depends(get_db),
) -> list[Log]:
    statement = (
        select(Log)
        .order_by(Log.timestamp.desc(), Log.created_at.desc())
        .offset(offset)
        .limit(limit)
    )
    return list(db.scalars(statement).all())


@router.get("/{log_id}", response_model=LogResponse)
def get_log(
    log_id: UUID,
    db: Session = Depends(get_db),
) -> Log:
    record = db.get(Log, log_id)

    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Log not found",
        )

    return record
