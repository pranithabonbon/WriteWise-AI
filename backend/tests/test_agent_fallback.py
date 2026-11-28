from unittest.mock import Mock

import pytest
from google.genai import errors

from app.services.ai_agent_service import (
    AIProviderUnavailableError,
    AIProviderTimeoutErrorWithStatus,
    generate_with_fallback,
    generate_with_retry,
)
from app.services.ai_improvement_service import AIProviderError


def error(status):
    return errors.APIError(status, {"error": {"message": "private provider response"}})


def test_fallback_primary_model_succeeds_without_using_fallback():
    client = Mock()
    expected = object()
    client.models.generate_content.return_value = expected

    result = generate_with_fallback(
        client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
    )

    assert result is expected
    client.models.generate_content.assert_called_once_with(
        model="primary-configured", contents=[], config={}
    )


def test_fallback_model_is_used_after_primary_temporary_failures():
    client = Mock()
    models = []

    def generate_content(*, model, **_kwargs):
        models.append(model)
        if model == "primary-configured":
            raise error(503)
        return "fallback response"

    client.models.generate_content.side_effect = generate_content
    result = generate_with_fallback(
        client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
    )

    assert result == "fallback response"
    assert models == ["primary-configured"] * 3 + ["fallback-configured"]


def test_fallback_model_is_used_after_primary_transport_failures():
    import httpx

    client = Mock()
    models = []

    def generate_content(*, model, **_kwargs):
        models.append(model)
        if model == "primary-configured":
            raise httpx.LocalProtocolError("transient protocol state")
        return "fallback response"

    client.models.generate_content.side_effect = generate_content
    result = generate_with_fallback(
        client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
    )

    assert result == "fallback response"
    assert models == ["primary-configured"] * 3 + ["fallback-configured"]


def test_fallback_both_models_fail_after_retry_limit(caplog):
    client = Mock()
    models = []

    def generate_content(*, model, **_kwargs):
        models.append(model)
        raise error(503)

    client.models.generate_content.side_effect = generate_content
    with caplog.at_level("WARNING", logger="app.services.ai_agent_service"):
        with pytest.raises(AIProviderUnavailableError):
            generate_with_fallback(
                client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
            )

    assert models == ["primary-configured"] * 3 + ["fallback-configured"] * 3
    assert "model=primary-configured, status=503" in caplog.text
    assert "model=fallback-configured, status=503" in caplog.text
    assert "private provider response" not in caplog.text


def test_permanent_primary_error_does_not_try_fallback():
    client = Mock()
    client.models.generate_content.side_effect = error(401)

    with pytest.raises(AIProviderError):
        generate_with_fallback(
            client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
        )

    client.models.generate_content.assert_called_once()


def test_missing_fallback_preserves_primary_failure_behavior():
    client = Mock()
    client.models.generate_content.side_effect = error(503)

    with pytest.raises(AIProviderUnavailableError):
        generate_with_fallback(
            client, "primary-configured", None, [], {}, sleep=lambda _: None
        )

    assert client.models.generate_content.call_count == 3
    assert {call.kwargs["model"] for call in client.models.generate_content.call_args_list} == {
        "primary-configured"
    }


def test_504_retries_with_existing_bounded_policy_then_succeeds():
    client = Mock()
    expected = object()
    client.models.generate_content.side_effect = [error(504), error(504), expected]
    delays = []

    assert generate_with_retry(
        client, "configured-model", [], {}, sleep=delays.append
    ) is expected
    assert client.models.generate_content.call_count == 3
    assert delays == [0.5, 1.0]


def test_fallback_succeeds_after_primary_504_retries():
    client = Mock()
    models = []

    def generate_content(*, model, **_kwargs):
        models.append(model)
        if model == "primary-configured":
            raise error(504)
        return "fallback response"

    client.models.generate_content.side_effect = generate_content
    result = generate_with_fallback(
        client, "primary-configured", "fallback-configured", [], {}, sleep=lambda _: None
    )

    assert result == "fallback response"
    assert models == ["primary-configured"] * 3 + ["fallback-configured"]


def test_both_models_timing_out_returns_safe_timeout(client, monkeypatch):
    from app.routes import agent as agent_route

    class TimingOutAgent:
        def __init__(self, _config):
            self.client = Mock()
            self.client.models.generate_content.side_effect = error(504)

        def analyze(self, *_args):
            return generate_with_fallback(
                self.client,
                "primary-configured",
                "fallback-configured",
                [],
                {},
                sleep=lambda _: None,
            )

    monkeypatch.setattr(agent_route, "AIWritingAgent", TimingOutAgent)
    agent = TimingOutAgent(None)
    monkeypatch.setattr(agent_route, "AIWritingAgent", lambda _config: agent)
    response = client.post("/api/agent/analyze", json={
        "text": "Some writing.", "goal": "Improve clarity"
    })

    assert response.status_code == 504
    assert response.json["success"] is False
    assert response.json["message"] == "The AI request timed out. Please try again."
    assert "provider" not in response.text.lower()
    assert agent.client.models.generate_content.call_count == 6

