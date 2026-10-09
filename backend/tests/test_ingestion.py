import json
from pathlib import Path
from typing import Any, Iterator
from uuid import UUID

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete

from backend.app.core.database import SessionLocal
from backend.app.main import app
from backend.app.models.log import Log

client = TestClient(app)
FIXTURES_DIR = Path(__file__).parent / "fixtures" / "logs"


def load_fixture(source: str) -> dict[str, Any]:
    return json.loads((FIXTURES_DIR / f"{source}.json").read_text(encoding="utf-8"))


@pytest.fixture
def created_log_ids() -> Iterator[list[UUID]]:
    ids: list[UUID] = []
    yield ids
    if ids:
        with SessionLocal() as db:
            db.execute(delete(Log).where(Log.id.in_(ids)))
            db.commit()


SOURCES = [
    ("nginx", "ERROR", "nginx", "http_request"),
    ("kubernetes", "WARNING", "api-7d8f9", "kubernetes_event"),
    ("docker", "ERROR", "api", "container_log"),
    ("application", "ERROR", "user-api", "exception"),
    ("github_actions", "ERROR", "CI", "workflow_failure"),
]


@pytest.mark.parametrize("source,severity,service,event_type", SOURCES)
def test_valid_source_is_normalized_and_persisted(
    source: str, severity: str, service: str, event_type: str, created_log_ids: list[UUID],
) -> None:
    payload = load_fixture(source)
    response = client.post("/api/v1/logs", json=payload)
    assert response.status_code == 201, response.text
    body = response.json()
    created_log_ids.append(UUID(body["id"]))
    assert (body["source"], body["severity"], body["service"], body["event_type"]) == (source, severity, service, event_type)
    assert body["message"] == payload["raw_message"]
    assert body["raw_message"] == payload["raw_message"]
    assert isinstance(body["metadata"], dict)
    detail = client.get(f"/api/v1/logs/{body['id']}")
    assert detail.status_code == 200
    assert detail.json()["raw_message"] == payload["raw_message"]


@pytest.mark.parametrize("source,field,value", [
    ("nginx", "status_code", 99),
    ("kubernetes", "event_type", "Debug"),
    ("docker", "stream", "both"),
    ("application", "level", "PANIC"),
    ("github_actions", "job_status", "unknown"),
])
def test_invalid_source_specific_values_are_rejected(source: str, field: str, value: object) -> None:
    payload = load_fixture(source)
    payload[field] = value
    assert client.post("/api/v1/logs", json=payload).status_code == 422


@pytest.mark.parametrize("source,field", [
    ("nginx", "client_ip"), ("kubernetes", "pod_name"), ("docker", "container_id"),
    ("application", "service_name"), ("github_actions", "workflow_name"),
])
def test_missing_source_fields_are_rejected(source: str, field: str) -> None:
    payload = load_fixture(source)
    del payload[field]
    assert client.post("/api/v1/logs", json=payload).status_code == 422


def test_timestamp_requires_timezone() -> None:
    payload = load_fixture("application")
    payload["timestamp"] = "2026-10-09T10:00:00"
    assert client.post("/api/v1/logs", json=payload).status_code == 422


def test_blank_raw_message_is_rejected() -> None:
    payload = load_fixture("docker")
    payload["raw_message"] = "   "
    assert client.post("/api/v1/logs", json=payload).status_code == 422


def test_batch_ingestion_persists_all_sources(created_log_ids: list[UUID]) -> None:
    payloads = [load_fixture(source) for source, *_ in SOURCES]
    response = client.post("/api/v1/logs/batch", json=payloads)
    assert response.status_code == 201, response.text
    body = response.json()
    assert body["count"] == len(payloads) == 5
    created_log_ids.extend(UUID(item["id"]) for item in body["logs"])
    assert {item["source"] for item in body["logs"]} == {source for source, *_ in SOURCES}


def test_empty_batch_is_rejected() -> None:
    assert client.post("/api/v1/logs/batch", json=[]).status_code == 422


def test_batch_with_invalid_item_is_rejected_before_ingestion() -> None:
    valid = load_fixture("nginx")
    invalid = load_fixture("docker")
    invalid["stream"] = "both"
    assert client.post("/api/v1/logs/batch", json=[valid, invalid]).status_code == 422


def test_unknown_log_returns_404() -> None:
    response = client.get("/api/v1/logs/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404
