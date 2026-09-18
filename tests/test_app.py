import sys

sys.path.insert(0, "app")

from app import app


def test_home():
    client = app.test_client()

    response = client.get("/")

    assert response.status_code == 200
    assert response.json["status"] == "running"


def test_health():
    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"

def test_health_failure_mode(monkeypatch):
    monkeypatch.setenv("FORCE_HEALTH_FAILURE", "true")

    client = app.test_client()

    response = client.get("/health")

    assert response.status_code == 500
    assert response.json["status"] == "unhealthy"
