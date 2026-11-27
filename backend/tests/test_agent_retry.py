from unittest.mock import Mock

import pytest
from google.genai import errors

from app.services.ai_agent_service import (
    AIProviderUnavailableError,
    generate_with_retry,
)
from app.services.ai_improvement_service import AIProviderError


def api_error(status):
    return errors.APIError(status, {"error": {"message": "provider details"}})


def test_generate_with_retry_uses_two_exponential_backoff_retries():
    client = Mock()
    expected = object()
    client.models.generate_content.side_effect = [api_error(503), api_error(429), expected]
    delays = []

    result = generate_with_retry(
        client, "configured-model", [], {}, sleep=delays.append
    )

    assert result is expected
    assert client.models.generate_content.call_count == 3
    assert delays == [0.5, 1.0]


def test_generate_with_retry_does_not_retry_permanent_api_errors():
    client = Mock()
    client.models.generate_content.side_effect = api_error(401)
    delays = []

    with pytest.raises(AIProviderError, match="API key"):
        generate_with_retry(client, "configured-model", [], {}, sleep=delays.append)

    assert client.models.generate_content.call_count == 1
    assert delays == []


def test_generate_with_retry_returns_unavailable_after_retry_limit():
    client = Mock()
    client.models.generate_content.side_effect = api_error(503)
    delays = []

    with pytest.raises(AIProviderUnavailableError, match="temporarily unavailable"):
        generate_with_retry(client, "configured-model", [], {}, sleep=delays.append)

    assert client.models.generate_content.call_count == 3
    assert delays == [0.5, 1.0]


def test_agent_api_returns_clear_sanitized_provider_failure(client, monkeypatch):
    from app.routes import agent as agent_route

    class FailingAgent:
        def __init__(self, _config):
            pass

        def analyze(self, *_args):
            raise AIProviderUnavailableError("secret provider detail")

    monkeypatch.setattr(agent_route, "AIWritingAgent", FailingAgent)
    response = client.post("/api/agent/analyze", json={
        "text": "Writing sample.", "goal": "Improve clarity"
    })

    assert response.status_code == 503
    assert response.json["success"] is False
    assert "temporarily unavailable" in response.json["message"]
    assert "secret provider detail" not in response.text
