from datetime import datetime, timedelta, timezone
from unittest import signals
from uuid import UUID

import pytest

from backend.app.correlation import CorrelationEvent, correlate_events


BASE_TIME = datetime(2026, 10, 14, 10, 0, tzinfo=timezone.utc)


def event(
    id_suffix: int,
    *,
    seconds: int = 0,
    source: str = "application",
    severity: str = "ERROR",
    service: str | None = "api",
    event_type: str = "application_log",
    message: str = "request failed",
    metadata: dict[str, object] | None = None,
) -> CorrelationEvent:
    return CorrelationEvent(
        id=UUID(f"00000000-0000-0000-0000-{id_suffix:012d}"),
        source=source,
        timestamp=BASE_TIME + timedelta(seconds=seconds),
        severity=severity,
        service=service,
        event_type=event_type,
        message=message,
        metadata=metadata or {},
        raw_message=message,
    )


def test_temporal_correlation_emits_explainable_signal() -> None:
    earlier = event(1, service=None, message="worker failed")
    later = event(2, seconds=2, service=None, message="request failed")
    signals = correlate_events([later, earlier], window_seconds=300)
    assert len(signals) == 1
    assert signals[0].log_id == later.id
    assert signals[0].related_log_id == earlier.id
    assert signals[0].relationship_type == "temporal_dependency"
    assert signals[0].relevance_score > 0
    assert "2 seconds apart" in signals[0].reason
    assert "not proof of causation" in signals[0].reason


def test_error_signature_matching_correlates_equivalent_signatures() -> None:
    first = event(1, service="billing-api", message="database connection refused")
    second = event(2, seconds=10, service="checkout-api", message="ECONNREFUSED from database")
    signals = correlate_events([first, second], window_seconds=60)
    assert len(signals) == 1
    assert signals[0].relationship_type == "error_signature"
    assert "connection_refused" in signals[0].reason


def test_higher_severity_increases_relevance_score() -> None:
    warning_pair = [
        event(1, severity="WARNING", service="api", message="generic event"),
        event(2, seconds=10, severity="INFO", service="api", message="generic event"),
    ]
    error_pair = [
        event(3, severity="ERROR", service="api", message="generic event"),
        event(4, seconds=10, severity="INFO", service="api", message="generic event"),
    ]
    warning_signal = correlate_events(warning_pair, window_seconds=60)[0]
    error_signal = correlate_events(error_pair, window_seconds=60)[0]
    assert error_signal.relevance_score > warning_signal.relevance_score


def test_service_relationship_matches_kubernetes_pod_and_container_name() -> None:
    kubernetes = event(
        1, source="kubernetes", service="api-7d8f9", severity="WARNING",
        message="readiness probe failed",
        metadata={"pod_name": "api-7d8f9", "namespace": "production"},
    )
    docker = event(
        2, seconds=5, source="docker", service="api", severity="ERROR",
        message="container exited", metadata={"container_name": "api"},
    )
    signals = correlate_events([kubernetes, docker], window_seconds=60)
    assert len(signals) == 1
    assert signals[0].relationship_type == "service_relationship"
    assert "api" in signals[0].reason


def test_unrelated_low_severity_logs_are_not_correlated() -> None:
    first = event(1, severity="INFO", service="catalog", message="cache refreshed")
    second = event(
        2, seconds=3, source="docker", severity="INFO",
        service="metrics", message="container is healthy",
    )
    assert correlate_events([first, second], window_seconds=300) == []


def test_causal_ordering_points_from_later_symptom_to_earlier_error() -> None:
    earlier = event(
        1, source="application", severity="ERROR", service="api",
        message="database connection refused",
    )
    later = event(
        2, seconds=2, source="nginx", severity="ERROR", service="nginx",
        message="upstream returned HTTP 502",
    )
    signals = correlate_events([later, earlier], window_seconds=60)
    assert len(signals) == 1
    assert signals[0].log_id == later.id
    assert signals[0].related_log_id == earlier.id
    assert "Earlier ERROR event preceded the later ERROR event" in signals[0].reason
    assert "not proof of causation" in signals[0].reason


def test_events_outside_window_are_not_correlated() -> None:
    first = event(1, seconds=0, service="api", message="connection refused")
    second = event(2, seconds=61, service="api", message="connection refused")
    assert correlate_events([first, second], window_seconds=60) == []


def test_invalid_window_is_rejected() -> None:
    with pytest.raises(ValueError, match="greater than zero"):
        correlate_events([], window_seconds=0)


def test_naive_timestamp_is_rejected() -> None:
    malformed = CorrelationEvent(
        id=UUID("00000000-0000-0000-0000-000000000001"),
        source="application",
        timestamp=datetime(2026, 10, 14, 10, 0),
        severity="ERROR",
        service="api",
        event_type="exception",
        message="connection refused",
        metadata={},
        raw_message="connection refused",
    )
    with pytest.raises(ValueError, match="timezone"):
        correlate_events([malformed], window_seconds=60)


def test_database_name_does_not_match_unrelated_service_name() -> None:
    frontend = event(
        1,
        service="frontend",
        message="request failed",
        metadata={"database_name": "api"},
    )
    api_service = event(
        2,
        seconds=5,
        service="api",
        message="request failed",
        metadata={"database_name": "postgres"},
    )

    assert correlate_events([frontend, api_service], window_seconds=60) == []


def test_kubernetes_replica_set_hash_matches_base_service_name() -> None:
    kubernetes = event(
        1,
        source="kubernetes",
        service="api-7d8f9abc12",
        severity="WARNING",
        message="readiness probe failed",
        metadata={"pod_name": "api-7d8f9abc12"},
    )
    docker = event(
        2,
        seconds=5,
        source="docker",
        service="api",
        severity="ERROR",
        message="container exited",
        metadata={"container_name": "api"},
    )

    signals = correlate_events([kubernetes, docker], window_seconds=60)

    assert len(signals) == 1
    assert signals[0].relationship_type == "service_relationship"


def test_shared_generic_timeout_is_reported_as_a_signal_not_proven_cause() -> None:
    first = event(
        1,
        service="billing-api",
        message="database timeout",
    )
    second = event(
        2,
        seconds=5,
        service="catalog-api",
        message="request timed out",
    )

    signals = correlate_events([first, second], window_seconds=60)

    # Matching signatures are a correlation clue, not proof of causation.
    assert len(signals) == 1
    assert signals[0].relationship_type == "error_signature"
    assert "timeout" in signals[0].reason
    assert "not proof of causation" in signals[0].reason

def test_all_relevance_scores_stay_between_zero_and_one() -> None:
    events = [
        event(
            1,
            service="api",
            severity="CRITICAL",
            message="connection refused",
        ),
        event(
            2,
            seconds=1,
            service="api",
            severity="FATAL",
            message="connection refused",
        ),
    ]

    signals = correlate_events(events, window_seconds=60)

    assert signals
    assert all(0.0 <= signal.relevance_score <= 1.0 for signal in signals)
