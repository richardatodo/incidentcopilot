
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.correlation import CorrelationEvent, correlate_events
from backend.app.models.incident import Incident
from backend.app.models.incident_log import IncidentLog
from backend.app.models.log import Log
from backend.app.schemas.incident import IncidentCreate, IncidentTimelineEvent


class IncidentNotFoundError(Exception):
    pass


class IncidentLogNotFoundError(Exception):
    pass


class InvalidIncidentTransitionError(Exception):
    pass


def list_incidents(db: Session) -> list[Incident]:
    statement = select(Incident).order_by(Incident.created_at.desc())
    return list(db.scalars(statement).all())


def get_incident(db: Session, incident_id: UUID) -> Incident:
    incident = db.get(Incident, incident_id)

    if incident is None:
        raise IncidentNotFoundError("Incident not found")

    return incident


def create_incident(db: Session, payload: IncidentCreate) -> Incident:
    incident = Incident(
        title=payload.title,
        severity=payload.severity,
        status="OPEN",
        started_at=datetime.now(timezone.utc),
    )

    db.add(incident)
    db.commit()
    db.refresh(incident)

    return incident


def investigate_incident(db: Session, incident_id: UUID) -> Incident:
    incident = get_incident(db, incident_id)

    if incident.status == "RESOLVED":
        raise InvalidIncidentTransitionError(
            "A resolved incident cannot be moved to INVESTIGATING"
        )

    if incident.status == "OPEN":
        incident.status = "INVESTIGATING"
        db.commit()
        db.refresh(incident)

    return incident


def resolve_incident(db: Session, incident_id: UUID) -> Incident:
    incident = get_incident(db, incident_id)

    # Repeated resolution must not overwrite the original ended_at.
    if incident.status == "RESOLVED":
        return incident

    incident.status = "RESOLVED"
    incident.ended_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(incident)

    return incident


def _to_correlation_event(log: Log) -> CorrelationEvent:
    return CorrelationEvent(
        id=log.id,
        source=log.source,
        timestamp=log.timestamp,
        severity=log.severity,
        service=log.service,
        event_type=log.event_type or "unknown",
        message=log.message,
        metadata=log.log_metadata or {},
        raw_message=log.raw_message,
    )


def associate_logs(
    db: Session,
    incident_id: UUID,
    log_ids: list[UUID],
) -> Incident:
    incident = get_incident(db, incident_id)

    requested_logs = db.scalars(
        select(Log).where(Log.id.in_(log_ids))
    ).all()

    found_ids = {log.id for log in requested_logs}
    missing_ids = set(log_ids) - found_ids

    if missing_ids:
        missing = ", ".join(str(log_id) for log_id in sorted(missing_ids))
        raise IncidentLogNotFoundError(f"Logs not found: {missing}")

    existing_logs = db.scalars(
        select(Log)
        .join(IncidentLog, IncidentLog.log_id == Log.id)
        .where(IncidentLog.incident_id == incident_id)
    ).all()

    # Keep existing associations so that adding new logs can refresh
    # correlation information across the incident's complete log set.
    all_logs_by_id = {log.id: log for log in existing_logs}
    all_logs_by_id.update({log.id: log for log in requested_logs})
    all_logs = list(all_logs_by_id.values())

    signals = correlate_events(
        [_to_correlation_event(log) for log in all_logs]
    )

        # Correlation signals are directional: log_id is the later event.
    # Store the signal metadata against that event only.
    strongest_signal: dict[UUID, tuple[float, str]] = {}

    for signal in signals:
        current = strongest_signal.get(signal.log_id)

        if current is None or signal.relevance_score > current[0]:
            strongest_signal[signal.log_id] = (
                signal.relevance_score,
                signal.relationship_type,
            )

    existing_associations = {
        association.log_id: association
        for association in db.scalars(
            select(IncidentLog).where(
                IncidentLog.incident_id == incident_id
            )
        ).all()
    }

    try:
        # Refresh metadata for the complete incident log set, not just
        # newly requested logs. This keeps older associations current
        # when additional logs introduce stronger correlations.
        for log in all_logs:
            signal = strongest_signal.get(log.id)
            association = existing_associations.get(log.id)

            if association is None:
                association = IncidentLog(
                    incident_id=incident_id,
                    log_id=log.id,
                    relevance_score=signal[0] if signal else None,
                    relationship_type=signal[1] if signal else None,
                )
                db.add(association)
            elif signal is not None:
                association.relevance_score = signal[0]
                association.relationship_type = signal[1]

        db.commit()
    except Exception:
        db.rollback()
        raise

    return get_incident(db, incident_id)


def get_incident_timeline(
    db: Session,
    incident_id: UUID,
) -> list[IncidentTimelineEvent]:
    get_incident(db, incident_id)

    logs = db.scalars(
        select(Log)
        .join(IncidentLog, IncidentLog.log_id == Log.id)
        .where(IncidentLog.incident_id == incident_id)
        .order_by(Log.timestamp.asc(), Log.id.asc())
    ).all()

    timeline: list[IncidentTimelineEvent] = []

    for log in logs:
        timeline.append(
            IncidentTimelineEvent(
                event_type="observed_log",
                timestamp=log.timestamp,
                log_id=log.id,
                source=log.source,
                severity=log.severity,
                service=log.service,
                message=log.message,
            )
        )

    signals = correlate_events(
        [_to_correlation_event(log) for log in logs]
    )

    logs_by_id = {log.id: log for log in logs}

    for signal in signals:
        later_log = logs_by_id.get(signal.log_id)

        if later_log is None:
            continue

        timeline.append(
            IncidentTimelineEvent(
                event_type="correlation",
                timestamp=later_log.timestamp,
                log_id=signal.log_id,
                related_log_id=signal.related_log_id,
                relationship_type=signal.relationship_type,
                relevance_score=signal.relevance_score,
                reason=signal.reason,
            )
        )

    # At identical timestamps, show the observed event before its
    # derived correlation information.
    timeline.sort(
        key=lambda event: (
            event.timestamp,
            0 if event.event_type == "observed_log" else 1,
            str(event.log_id),
            str(event.related_log_id or ""),
        )
    )

    return timeline
