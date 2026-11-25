"""Route tests for the transient AI improvement endpoint."""

from unittest.mock import Mock

import pytest

from app.services.ai_improvement_service import (
    AIConfigurationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    InputValidationError,
    InvalidAIResponseError,
    SUGGESTION_CATEGORIES,
)


def sample_result():
    return {
        "rewrite": "The team completed the report.",
        "grammar_explanations": [{
            "original_text": "The team complete the report.",
            "corrected_text": "The team completed the report.",
            "explanation": "Use the past tense for a finished action.",
        }],
        "suggestions": {category: [] for category in SUGGESTION_CATEGORIES},
    }


class FakeImprovementService:
    def __init__(self, result=None, error=None):
        self.result = result or sample_result()
        self.error = error
        self.calls = []

    def improve(self, text, tone, context="General"):
        self.calls.append((text, tone, context))
        if self.error:
            raise self.error
        return self.result


def test_improve_returns_structured_response_without_saving(client, monkeypatch):
    from app.routes import improve

    service = FakeImprovementService()
    monkeypatch.setattr(improve, "create_ai_improvement_service", lambda config: service)

    response = client.post("/api/improve", json={"text": "The team complete it.", "tone": "Academic"})

    assert response.status_code == 200
    assert response.get_json() == {"success": True, "tone": "Academic", "context": "General", **sample_result()}
    assert service.calls == [("The team complete it.", "Academic", "General")]


@pytest.mark.parametrize(
    "body,status,message",
    [
        (None, 400, "Request body must be a JSON object."),
        ({"text": "  "}, 400, "Please provide text to improve."),
        ({"text": 123}, 400, "Text must be a string."),
        ({"text": "hello", "tone": "casual"}, 400, "Tone must be"),
        ({"text": "hello", "context": "Legal"}, 400, "Context must be"),
        ({"text": "x" * 12_001}, 400, "characters or fewer"),
    ],
)
def test_improve_rejects_invalid_input_without_creating_provider(client, monkeypatch, body, status, message):
    from app.routes import improve

    factory = Mock(side_effect=AssertionError("provider must not be constructed"))
    monkeypatch.setattr(improve, "create_ai_improvement_service", factory)
    response = client.post("/api/improve", json=body)

    assert response.status_code == status
    assert message in response.get_json()["message"]
    factory.assert_not_called()


@pytest.mark.parametrize(
    "error,status,message,secret",
    [
        (AIConfigurationError("secret config detail"), 503, "not configured", "secret config detail"),
        (AIProviderTimeoutError("secret timeout detail"), 504, "timed out", "secret timeout detail"),
        (AIProviderRateLimitError("secret rate detail"), 429, "busy", "secret rate detail"),
        (AIProviderError("secret provider detail"), 502, "could not complete", "secret provider detail"),
        (InvalidAIResponseError("secret model content"), 502, "could not complete", "secret model content"),
    ],
)
def test_improve_maps_expected_failures_to_safe_messages(client, monkeypatch, error, status, message, secret):
    from app.routes import improve

    service = FakeImprovementService(error=error)
    monkeypatch.setattr(improve, "create_ai_improvement_service", lambda config: service)
    response = client.post("/api/improve", json={"text": "Some writing."})

    assert response.status_code == status
    body = response.get_json()
    assert message in body["message"]
    assert secret not in response.get_data(as_text=True)
    assert "success" in body and body["success"] is False


def test_improve_hides_unexpected_exception_details(client, monkeypatch):
    from app.routes import improve

    service = FakeImprovementService(error=RuntimeError("secret traceback detail"))
    monkeypatch.setattr(improve, "create_ai_improvement_service", lambda config: service)
    response = client.post("/api/improve", json={"text": "Some writing."})

    assert response.status_code == 502
    assert "secret traceback detail" not in response.get_data(as_text=True)
