from typing import NoReturn
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.schemas.incident import (
    IncidentCreate,
    IncidentLogAssociationRequest,
    IncidentResponse,
    IncidentTimelineEvent,
)
from backend.app.services.incident_lifecycle import (
    IncidentLogNotFoundError,
    IncidentNotFoundError,
    InvalidIncidentTransitionError,
    associate_logs,
    create_incident,
    get_incident,
    get_incident_timeline,
    investigate_incident,
    list_incidents,
    resolve_incident,
)

router = APIRouter(prefix="/incidents", tags=["Incidents"])


def _raise_not_found(error: Exception) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail=str(error),
    ) from error


def _raise_invalid_transition(error: Exception) -> NoReturn:
    raise HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(error),
    ) from error


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_incident_endpoint(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
):
    return create_incident(db, payload)


@router.get("", response_model=list[IncidentResponse])
def list_incidents_endpoint(
    db: Session = Depends(get_db),
):
    return list_incidents(db)


@router.get("/{incident_id}", response_model=IncidentResponse)
def get_incident_endpoint(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_incident(db, incident_id)
    except IncidentNotFoundError as error:
        _raise_not_found(error)


@router.get(
    "/{incident_id}/events",
    response_model=list[IncidentTimelineEvent],
)
def get_incident_events_endpoint(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return get_incident_timeline(db, incident_id)
    except IncidentNotFoundError as error:
        _raise_not_found(error)


@router.post(
    "/{incident_id}/logs",
    response_model=IncidentResponse,
)
def associate_incident_logs_endpoint(
    incident_id: UUID,
    payload: IncidentLogAssociationRequest,
    db: Session = Depends(get_db),
):
    try:
        return associate_logs(db, incident_id, payload.log_ids)
    except IncidentNotFoundError as error:
        _raise_not_found(error)
    except IncidentLogNotFoundError as error:
        _raise_not_found(error)


@router.post(
    "/{incident_id}/investigate",
    response_model=IncidentResponse,
)
def investigate_incident_endpoint(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return investigate_incident(db, incident_id)
    except IncidentNotFoundError as error:
        _raise_not_found(error)
    except InvalidIncidentTransitionError as error:
        _raise_invalid_transition(error)


@router.post(
    "/{incident_id}/resolve",
    response_model=IncidentResponse,
)
def resolve_incident_endpoint(
    incident_id: UUID,
    db: Session = Depends(get_db),
):
    try:
        return resolve_incident(db, incident_id)
    except IncidentNotFoundError as error:
        _raise_not_found(error)
