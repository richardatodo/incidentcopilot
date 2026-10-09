from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)



def test_list_incidents_returns_empty_collection(client):
    response = client.get("/api/v1/incidents")

    assert response.status_code == 200
    assert response.json() == []


def test_list_logs_returns_empty_collection(client):
    response = client.get("/api/v1/logs")

    assert response.status_code == 200
    assert response.json() == []
