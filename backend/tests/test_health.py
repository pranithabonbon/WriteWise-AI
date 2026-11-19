from app import create_app
from config import TestConfig


def test_health_returns_ok(client):
    response = client.get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["service"] == "WriteWise AI API"


def test_health_reports_database_not_configured():
    class NoDbConfig(TestConfig):
        MONGODB_URI = ""

    data = create_app(NoDbConfig).test_client().get("/api/health").get_json()
    assert data["status"] == "ok"
    assert data["database"] == "not_configured"


def test_unknown_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")

    assert response.status_code == 404
    assert response.get_json() == {"error": "Resource not found"}