from app import create_app
from config import TestConfig
import pytest
import mongomock


def test_health_returns_ok(client):
    response = client.get("/api/health")
    data = response.get_json()

    assert response.status_code == 200
    assert data["status"] == "ok"
    assert data["database"] == "connected"
    assert data["service"] == "WriteWise AI API"


def test_health_does_not_initialize_language_tool(client, monkeypatch):
    calls = []

    def unexpected_initialization(_language):
        calls.append(True)
        raise AssertionError("Health checks must not start LanguageTool")

    monkeypatch.setattr(
        "app.services.grammar_analyzer.language_tool_python.LanguageTool",
        unexpected_initialization,
    )

    response = client.get("/api/health")

    assert response.status_code == 200
    assert calls == []


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


def test_production_config_rejects_unsafe_cors_and_missing_secrets():
    class ProductionConfig(TestConfig):
        APP_ENV = "production"
        SECRET_KEY = "a" * 48
        CORS_ORIGINS = ["https://writewise.example"]
        MONGODB_URI = "mongodb://localhost:27017/writewise_test"
        LLM_PROVIDER = "gemini"
        GEMINI_API_KEY = "configured"
        LLM_MODEL = "configured-model"
        MONGO_CLIENT = mongomock.MongoClient()

    BadSecret = type("BadSecret", (ProductionConfig,), {"SECRET_KEY": "short"})
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        create_app(BadSecret)

    WildcardCors = type("WildcardCors", (ProductionConfig,), {"CORS_ORIGINS": ["*"]})
    with pytest.raises(RuntimeError, match="CORS_ORIGINS"):
        create_app(WildcardCors)

    MissingAtlas = type("MissingAtlas", (ProductionConfig,), {"MONGODB_URI": ""})
    with pytest.raises(RuntimeError, match="MONGODB_URI"):
        create_app(MissingAtlas)

    MissingGemini = type("MissingGemini", (ProductionConfig,), {"GEMINI_API_KEY": ""})
    with pytest.raises(RuntimeError, match="AI provider"):
        create_app(MissingGemini)


def test_production_config_accepts_exact_https_origin_and_required_services():
    class ProductionConfig(TestConfig):
        APP_ENV = "production"
        SECRET_KEY = "a" * 48
        CORS_ORIGINS = ["https://writewise.example"]
        MONGODB_URI = "mongodb://localhost:27017/writewise_test"
        LLM_PROVIDER = "gemini"
        GEMINI_API_KEY = "configured"
        LLM_MODEL = "configured-model"
        MONGO_CLIENT = mongomock.MongoClient()

    app = create_app(ProductionConfig)
    assert app.config["APP_ENV"] == "production"
