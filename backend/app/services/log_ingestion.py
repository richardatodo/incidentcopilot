from collections.abc import Sequence

from sqlalchemy.orm import Session

from backend.app.models.log import Log
from backend.app.parsers import parse_log
from backend.app.schemas.log_ingestion import LogIngestRequest


def _to_model(payload: LogIngestRequest) -> Log:
    normalized = parse_log(payload)
    return Log(
        source=normalized.source, timestamp=normalized.timestamp, severity=normalized.severity,
        service=normalized.service, event_type=normalized.event_type, message=normalized.message,
        log_metadata=normalized.metadata, raw_message=normalized.raw_message,
    )


def ingest_log(db: Session, payload: LogIngestRequest) -> Log:
    record = _to_model(payload)
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def ingest_logs_batch(db: Session, payloads: Sequence[LogIngestRequest]) -> list[Log]:
    records = [_to_model(payload) for payload in payloads]
    try:
        db.add_all(records)
        db.commit()
    except Exception:
        db.rollback()
        raise
    for record in records:
        db.refresh(record)
    return records
