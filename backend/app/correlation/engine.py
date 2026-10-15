"""Deterministic, explainable correlation for normalized log events."""
from __future__ import annotations

import re
from datetime import datetime
from typing import Sequence

from backend.app.core.config import settings
from backend.app.correlation.models import CorrelationEvent, CorrelationSignal


_SEVERITY_RANK = {
    "TRACE": 0, "DEBUG": 0, "INFO": 1, "WARN": 2, "WARNING": 2,
    "ERROR": 3, "CRITICAL": 4, "FATAL": 4,
}
_SIGNATURE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("connection_refused", re.compile(r"connection refused|econnrefused", re.I)),
    ("timeout", re.compile(r"\btimeout\b|timed out|deadline exceeded", re.I)),
    ("crash_loop_back_off", re.compile(r"crashloopbackoff", re.I)),
    ("oom_killed", re.compile(r"oomkilled|out of memory|oom kill", re.I)),
    ("http_5xx", re.compile(r"\b5(?:00|02|03|04)\b|HTTP\s+5\d\d", re.I)),
    ("deployment_failure", re.compile(r"deployment (?:failed|failure)|workflow failure|job failed", re.I)),
)

_SERVICE_KEYS = {
    "service", "service_name", "container_name", "pod_name",
    "upstream_service", "target_service", "dependency",
}

_KUBERNETES_SUFFIX = re.compile(r"-[a-z0-9]{5,10}$", re.I)

# Explicit, deterministic weights. Their maximum total is 1.0.
_TEMPORAL_WEIGHT = 0.25
_SERVICE_WEIGHT = 0.25
_SIGNATURE_WEIGHT = 0.25
_SEVERITY_WEIGHT = 0.15
_ORDERING_WEIGHT = 0.10


def _severity_rank(value: str) -> int:
    return _SEVERITY_RANK.get(value.upper(), 1)


def _event_text(event: CorrelationEvent) -> str:
    metadata_text = " ".join(
        str(value) for value in event.metadata.values()
        if isinstance(value, (str, int, float, bool))
    )
    return " ".join((event.message, event.raw_message, event.event_type, metadata_text))


def _signatures(event: CorrelationEvent) -> set[str]:
    text = _event_text(event)
    return {name for name, pattern in _SIGNATURE_PATTERNS if pattern.search(text)}


def _normalise_service(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    return value.strip().lower() or None


def _service_identities(event: CorrelationEvent) -> set[str]:
    identities: set[str] = set()
    candidates: list[object] = [event.service]
    candidates.extend(
        value for key, value in event.metadata.items()
        if key.lower() in _SERVICE_KEYS
    )
    for candidate in candidates:
        identity = _normalise_service(candidate)
        if identity:
            identities.add(identity)
            base = _KUBERNETES_SUFFIX.sub("", identity)
            if base != identity:
                identities.add(base)
    return identities


def _validate_timestamp(value: datetime) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("correlation timestamps must include a timezone")


def _reason_for(
    earlier: CorrelationEvent,
    later: CorrelationEvent,
    delta_seconds: float,
    window_seconds: int,
    shared_services: set[str],
    shared_signatures: set[str],
    has_ordering_signal: bool,
) -> str:
    parts = [
        f"Events occurred {delta_seconds:g} seconds apart within the "
        f"{window_seconds}-second correlation window."
    ]
    if shared_services:
        parts.append("Matching service identity: " + ", ".join(sorted(shared_services)) + ".")
    if shared_signatures:
        parts.append("Shared error signature: " + ", ".join(sorted(shared_signatures)) + ".")
    if has_ordering_signal:
        parts.append(
            f"Earlier {earlier.severity.upper()} event preceded the later "
            f"{later.severity.upper()} event; ordering is an investigative "
            "clue, not proof of causation."
        )
    return " ".join(parts)


def correlate_events(
    events: Sequence[CorrelationEvent],
    *,
    window_seconds: int | None = None,
) -> list[CorrelationSignal]:
    """Correlate event pairs without database access or LLM calls.

    ``log_id`` identifies the later event and ``related_log_id`` identifies
    the earlier/related event. Mere temporal proximity is insufficient unless
    both events are high-severity and very close in time.
    """
    window = settings.log_correlation_window_seconds if window_seconds is None else window_seconds
    if window <= 0:
        raise ValueError("window_seconds must be greater than zero")
    for event in events:
        _validate_timestamp(event.timestamp)

    ordered = sorted(events, key=lambda item: (item.timestamp, str(item.id)))
    signals: list[CorrelationSignal] = []
    for index, first in enumerate(ordered):
        for second in ordered[index + 1:]:
            delta = (second.timestamp - first.timestamp).total_seconds()
            if delta > window:
                break

            shared_services = _service_identities(first) & _service_identities(second)
            shared_signatures = _signatures(first) & _signatures(second)
            first_rank = _severity_rank(first.severity)
            second_rank = _severity_rank(second.severity)
            close_high_severity = (
                delta <= max(1.0, window * 0.05)
                and first_rank >= _SEVERITY_RANK["ERROR"]
                and second_rank >= _SEVERITY_RANK["ERROR"]
            )
            if not shared_services and not shared_signatures and not close_high_severity:
                continue

            temporal_score = max(0.0, 1.0 - delta / window)
            severity_score = max(first_rank, second_rank) / 4
            has_ordering_signal = (
                first.timestamp < second.timestamp
                and first_rank >= _SEVERITY_RANK["WARNING"]
                and (bool(_signatures(second)) or second_rank >= _SEVERITY_RANK["WARNING"])
            )
            score = (
                _TEMPORAL_WEIGHT * temporal_score
                + (_SERVICE_WEIGHT if shared_services else 0.0)
                + (_SIGNATURE_WEIGHT if shared_signatures else 0.0)
                + _SEVERITY_WEIGHT * severity_score
                + (_ORDERING_WEIGHT if has_ordering_signal else 0.0)
            )
            score = round(min(1.0, score), 2)

            if shared_services and shared_signatures:
                relationship_type = "combined_signal"
            elif shared_signatures:
                relationship_type = "error_signature"
            elif shared_services:
                relationship_type = "service_relationship"
            else:
                relationship_type = "temporal_dependency"

            signals.append(CorrelationSignal(
                log_id=second.id,
                related_log_id=first.id,
                relevance_score=score,
                relationship_type=relationship_type,
                reason=_reason_for(
                    first, second, delta, window, shared_services,
                    shared_signatures, has_ordering_signal,
                ),
            ))

    return sorted(
        signals,
        key=lambda signal: (-signal.relevance_score, str(signal.log_id), str(signal.related_log_id)),
    )
