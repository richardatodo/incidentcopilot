
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from backend.app.models.log import Log


def create_log(
    db_session,
    *,
    timestamp: datetime,
    message: str,
    service: str = "payment-api",
    severity: str = "ERROR",
) -> Log:
    log = Log(
        source="application",
        timestamp=timestamp,
        severity=severity,
        service=service,
        event_type="exception",
        message=message,
        log_metadata={"service_name": service},
        raw_message=message,
    )
    db_session.add(log)
    db_session.flush()
    return log


def create_incident(client, title="Payment API unavailable", severity="HIGH"):
    response = client.post(
        "/api/v1/incidents",
        json={"title": title, "severity": severity},
    )
    assert response.status_code == 201, response.text
    return response.json()


def test_create_incident_starts_open(client):
    incident = create_incident(client)

    assert incident["title"] == "Payment API unavailable"
    assert incident["severity"] == "HIGH"
    assert incident["status"] == "OPEN"
    assert incident["started_at"] is not None
    assert incident["ended_at"] is None


def test_incident_title_is_trimmed(client):
    incident = create_incident(client, title="  API unavailable  ")

    assert incident["title"] == "API unavailable"


def test_blank_incident_title_is_rejected(client):
    response = client.post(
        "/api/v1/incidents",
        json={"title": "   ", "severity": "HIGH"},
    )

    assert response.status_code == 422


def test_invalid_incident_severity_is_rejected(client):
    response = client.post(
        "/api/v1/incidents",
        json={"title": "API unavailable", "severity": "URGENT"},
    )

    assert response.status_code == 422


def test_list_incidents_includes_created_incident(client):
    incident = create_incident(client)

    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    assert any(item["id"] == incident["id"] for item in response.json())


def test_get_incident_by_id(client):
    incident = create_incident(client)

    response = client.get(f"/api/v1/incidents/{incident['id']}")

    assert response.status_code == 200
    assert response.json()["id"] == incident["id"]


def test_unknown_incident_returns_404(client):
    response = client.get(f"/api/v1/incidents/{uuid4()}")

    assert response.status_code == 404


def test_investigate_transitions_open_incident(client):
    incident = create_incident(client)

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/investigate"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "INVESTIGATING"


def test_investigating_an_investigating_incident_is_idempotent(client):
    incident = create_incident(client)
    url = f"/api/v1/incidents/{incident['id']}/investigate"

    first = client.post(url)
    second = client.post(url)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["status"] == "INVESTIGATING"


def test_resolve_open_incident(client):
    incident = create_incident(client)

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/resolve"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"
    assert response.json()["ended_at"] is not None


def test_resolve_investigating_incident(client):
    incident = create_incident(client)
    client.post(f"/api/v1/incidents/{incident['id']}/investigate")

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/resolve"
    )

    assert response.status_code == 200
    assert response.json()["status"] == "RESOLVED"


def test_repeated_resolution_preserves_ended_at(client):
    incident = create_incident(client)
    url = f"/api/v1/incidents/{incident['id']}/resolve"

    first = client.post(url)
    original_ended_at = first.json()["ended_at"]

    second = client.post(url)

    assert second.status_code == 200
    assert second.json()["ended_at"] == original_ended_at


def test_resolved_incident_cannot_be_reopened(client):
    incident = create_incident(client)

    client.post(f"/api/v1/incidents/{incident['id']}/resolve")

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/investigate"
    )

    assert response.status_code == 409


def test_associating_logs_does_not_change_incident_status(
    client,
    db_session,
):
    incident = create_incident(client)

    log = create_log(
        db_session,
        timestamp=datetime.now(timezone.utc),
        message="Payment database connection refused",
    )

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={"log_ids": [str(log.id)]},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "OPEN"


def test_associated_logs_appear_in_timeline(client, db_session):
    incident = create_incident(client)

    timestamp = datetime.now(timezone.utc)
    log = create_log(
        db_session,
        timestamp=timestamp,
        message="Payment database connection refused",
    )

    attach_response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={"log_ids": [str(log.id)]},
    )

    assert attach_response.status_code == 200

    response = client.get(
        f"/api/v1/incidents/{incident['id']}/events"
    )

    assert response.status_code == 200

    events = response.json()
    assert len(events) == 1
    assert events[0]["event_type"] == "observed_log"
    assert events[0]["log_id"] == str(log.id)


def test_timeline_contains_directional_correlation_event(
    client,
    db_session,
):
    incident = create_incident(client)

    earlier_timestamp = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)
    later_timestamp = earlier_timestamp + timedelta(seconds=10)

    earlier_log = create_log(
        db_session,
        timestamp=earlier_timestamp,
        message="Database connection refused",
    )
    later_log = create_log(
        db_session,
        timestamp=later_timestamp,
        message="Database connection refused while processing payment",
    )

    attach_response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={
            "log_ids": [
                str(earlier_log.id),
                str(later_log.id),
            ]
        },
    )

    assert attach_response.status_code == 200

    response = client.get(
        f"/api/v1/incidents/{incident['id']}/events"
    )

    assert response.status_code == 200

    events = response.json()

    observed_events = [
        event for event in events
        if event["event_type"] == "observed_log"
    ]
    correlation_events = [
        event for event in events
        if event["event_type"] == "correlation"
    ]

    assert len(observed_events) == 2
    assert len(correlation_events) >= 1

    correlation = next(
        event for event in correlation_events
        if event["log_id"] == str(later_log.id)
        and event["related_log_id"] == str(earlier_log.id)
    )

    assert correlation["relationship_type"] in {
        "combined_signal",
        "error_signature",
        "service_relationship",
    }
    assert 0.0 <= correlation["relevance_score"] <= 1.0
    assert correlation["reason"] is None or isinstance(
        correlation["reason"], str
    )


def test_timeline_is_chronological(client, db_session):
    incident = create_incident(client)

    base_time = datetime(2026, 10, 1, 10, 0, tzinfo=timezone.utc)

    later_log = create_log(
        db_session,
        timestamp=base_time + timedelta(minutes=2),
        message="Later payment failure",
        service="payment-api",
    )
    earlier_log = create_log(
        db_session,
        timestamp=base_time,
        message="Earlier payment failure",
        service="payment-api",
    )

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={
            "log_ids": [
                str(later_log.id),
                str(earlier_log.id),
            ]
        },
    )

    assert response.status_code == 200

    timeline_response = client.get(
        f"/api/v1/incidents/{incident['id']}/events"
    )

    assert timeline_response.status_code == 200

    timestamps = [
        event["timestamp"]
        for event in timeline_response.json()
    ]

    assert timestamps == sorted(timestamps)


def test_associating_unknown_log_returns_404(client):
    incident = create_incident(client)

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={"log_ids": [str(uuid4())]},
    )

    assert response.status_code == 404


def test_duplicate_log_ids_are_rejected(client):
    incident = create_incident(client)
    log_id = str(uuid4())

    response = client.post(
        f"/api/v1/incidents/{incident['id']}/logs",
        json={"log_ids": [log_id, log_id]},
    )

    assert response.status_code == 422


def test_timeline_for_unknown_incident_returns_404(client):
    response = client.get(
        f"/api/v1/incidents/{uuid4()}/events"
    )

    assert response.status_code == 404
