"""Unit tests for AI improvement validation and provider error handling."""

import json
from types import SimpleNamespace
from unittest.mock import Mock

import anthropic
import pytest
from google import genai
from google.genai import errors as gemini_errors

from app.services.ai_improvement_service import (
    AIConfigurationError,
    AIImprovementService,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    InputValidationError,
    InvalidAIResponseError,
    AnthropicProvider,
    GeminiProvider,
    MAX_INPUT_CHARACTERS,
    SUGGESTION_CATEGORIES,
    create_ai_improvement_service,
)


def valid_result():
    return {
        "rewrite": "The team completed the report.",
        "grammar_explanations": [{
            "original_text": "The team complete the report.",
            "corrected_text": "The team completed the report.",
            "explanation": "Use the past tense for an action that is finished.",
            "correction_type": "mandatory",
        }],
        "suggestions": {category: [] for category in SUGGESTION_CATEGORIES},
    }


class FakeProvider:
    def __init__(self, result=None):
        self.result = result or valid_result()
        self.calls = []

    def generate_improvement(self, text, tone, context="General"):
        self.calls.append((text, tone, context))
        return self.result


def test_service_returns_validated_result_and_passes_tone():
    provider = FakeProvider()
    result = AIImprovementService(provider).improve("The team complete it.", "Academic")

    assert result == valid_result()
    assert provider.calls == [("The team complete it.", "Academic", "General")]


def test_service_passes_context_and_preserves_proper_names_and_numbers():
    provider = FakeProvider({**valid_result(), "rewrite": "Maya said the PostgreSQL API returned 200 results."})
    result = AIImprovementService(provider).improve(
        "Maya said the PostgreSQL API returns 200 results.", "Professional", "Academic"
    )
    assert result["rewrite"] == "Maya said the PostgreSQL API returned 200 results."
    assert provider.calls == [("Maya said the PostgreSQL API returns 200 results.", "Professional", "Academic")]


def test_service_rejects_rewrite_that_drops_protected_terms_or_numbers():
    provider = FakeProvider({**valid_result(), "rewrite": "The database returned many results."})
    with pytest.raises(InvalidAIResponseError, match="preserve important names"):
        AIImprovementService(provider).improve("Maya used PostgreSQL API v2 in 2026.")


def test_service_preserves_degree_cgpa_project_technical_terms_and_event_ids():
    original = (
        "Example Candidate completed a B.Tech in Computer Science with a CGPA of 7.42. "
        "The example project is a Microsoft Sentinel SOC Investigation Lab using KQL "
        "and Windows Event IDs 4624, 4625, and 4720."
    )
    rewrite = (
        "Example Candidate earned a B.Tech degree in Computer Science with a CGPA of 7.42. "
        "The project is a SOC Investigation Lab in Microsoft Sentinel using KQL "
        "and Windows Event IDs 4624, 4625, and 4720."
    )
    result = AIImprovementService(FakeProvider({
        **valid_result(), "rewrite": rewrite,
    })).improve(original)
    assert result["rewrite"] == rewrite


@pytest.mark.parametrize("rewrite", [
    "Example Candidate completed a B.Tech in Computer Science with a CGPA of 7.24.",
    "Example Candidate completed a B.Tech in Computer Science with a CGPA of 7.42. The example project uses KQL and Windows Event IDs 4624 and 4625.",
    "Example Candidate completed a B.Tech in Computer Science with a CGPA of 7.42. The lab uses KQL and Windows Event IDs 4624, 4625, and 4720.",
])
def test_service_rejects_changed_or_omitted_factual_details(rewrite):
    original = (
        "Example Candidate completed a B.Tech in Computer Science with a CGPA of 7.42. "
        "The example project is a Microsoft Sentinel SOC Investigation Lab using KQL "
        "and Windows Event IDs 4624, 4625, and 4720."
    )
    with pytest.raises(InvalidAIResponseError, match="important names, facts, or numbers"):
        AIImprovementService(FakeProvider({**valid_result(), "rewrite": rewrite})).improve(original)


def test_already_good_text_can_be_returned_unchanged():
    original = "The application processes data efficiently."
    result = AIImprovementService(FakeProvider({
        **valid_result(), "rewrite": original, "grammar_explanations": [],
    })).improve(original)
    assert result["rewrite"] == original


@pytest.mark.parametrize("text", ["", "  \n", None])
def test_service_rejects_empty_or_non_string_text_before_provider(text):
    provider = FakeProvider()
    with pytest.raises(InputValidationError):
        AIImprovementService(provider).improve(text)
    assert provider.calls == []


def test_service_rejects_too_long_text_before_provider():
    provider = FakeProvider()
    with pytest.raises(InputValidationError, match="characters or fewer"):
        AIImprovementService(provider).improve("x" * (MAX_INPUT_CHARACTERS + 1))
    assert provider.calls == []


@pytest.mark.parametrize("tone", ["casual", "Friendly ", "", None])
def test_service_rejects_unsupported_tones_before_provider(tone):
    provider = FakeProvider()
    with pytest.raises(InputValidationError, match="Tone must be"):
        AIImprovementService(provider).improve("Some writing.", tone)
    assert provider.calls == []


@pytest.mark.parametrize(
    "mutate",
    [
        lambda result: result.update(rewrite="  "),
        lambda result: result.update(grammar_explanations=[{"original_text": "x"}]),
        lambda result: result["suggestions"].pop("Vocabulary"),
        lambda result: result["suggestions"].update({"Readability": "too broad"}),
        lambda result: result.update(unexpected="provider detail"),
    ],
)
def test_service_rejects_malformed_provider_output(mutate):
    result = valid_result()
    mutate(result)
    with pytest.raises(InvalidAIResponseError):
        AIImprovementService(FakeProvider(result)).improve("Some writing.")


def test_provider_uses_timeout_and_forced_structured_tool(monkeypatch):
    message = SimpleNamespace(content=[SimpleNamespace(
        type="tool_use", name=AnthropicProvider.TOOL_NAME, input=valid_result()
    )])
    client = Mock()
    client.messages.create.return_value = message
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=client))

    provider = AnthropicProvider("test-key", "test-model", 7)
    assert provider.generate_improvement("Some writing.", "Formal") == valid_result()
    anthropic.Anthropic.assert_called_once_with(
        api_key="test-key", timeout=7, max_retries=0
    )
    kwargs = client.messages.create.call_args.kwargs
    assert "If the original is already clear and correct, return it unchanged" in kwargs["system"]
    assert kwargs["tool_choice"] == {
        "type": "tool", "name": AnthropicProvider.TOOL_NAME
    }
    assert kwargs["tools"][0]["input_schema"]["required"] == [
        "rewrite", "grammar_explanations", "suggestions"
    ]


@pytest.mark.parametrize(
    "provider_error,expected",
    [
        (anthropic.APITimeoutError(request=Mock()), AIProviderTimeoutError),
        (anthropic.RateLimitError("rate limited", response=Mock(), body={}), AIProviderRateLimitError),
        (anthropic.APIError("provider detail", request=Mock(), body={}), AIProviderError),
    ],
)
def test_provider_maps_errors_without_exposing_details(monkeypatch, provider_error, expected):
    client = Mock()
    client.messages.create.side_effect = provider_error
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=client))
    provider = AnthropicProvider("test-key", "test-model", 1)

    with pytest.raises(expected) as caught:
        provider.generate_improvement("Some writing.", "Formal")
    assert "provider detail" not in str(caught.value)


def test_provider_logs_safe_anthropic_error_diagnostics(monkeypatch, caplog):
    secret = "test-anthropic-key-placeholder"
    error = anthropic.APIStatusError(
        "invalid request",
        response=Mock(status_code=404, headers={"request-id": "req_test"}),
        body={"error": {"type": "not_found_error", "message": "model not found " + secret}},
    )
    client = Mock()
    client.messages.create.side_effect = error
    monkeypatch.setattr(anthropic, "Anthropic", Mock(return_value=client))
    provider = AnthropicProvider(secret, "invalid-model", 1)

    with caplog.at_level("WARNING", logger="app.services.ai_improvement_service"):
        with pytest.raises(AIProviderError):
            provider.generate_improvement("Some writing.", "Formal")

    assert "status=404" in caplog.text
    assert "not_found_error" in caplog.text
    assert "model not found" in caplog.text
    assert "req_test" in caplog.text
    assert secret not in caplog.text


def test_gemini_provider_uses_sdk_json_schema_and_timeout(monkeypatch):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(
        text=json.dumps(valid_result())
    )
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))

    provider = GeminiProvider("test-key", "gemini-3.5-flash-lite", 7)
    assert provider.generate_improvement("Some writing.", "Friendly") == valid_result()
    genai.Client.assert_called_once()
    client_config = genai.Client.call_args.kwargs
    assert client_config["api_key"] == "test-key"
    assert client_config["http_options"].timeout == 7000
    assert client_config["http_options"].retry_options.attempts == 1
    assert client_config["http_options"].client_args == {"trust_env": False}
    kwargs = client.models.generate_content.call_args.kwargs
    assert kwargs["model"] == "gemini-3.5-flash-lite"
    assert "Friendly tone" in kwargs["contents"]
    assert "If the original is already clear and correct, return it unchanged" in kwargs["contents"]
    assert kwargs["config"].response_mime_type == "application/json"
    assert kwargs["config"].response_schema["required"] == [
        "rewrite", "grammar_explanations", "suggestions"
    ]


def test_gemini_provider_trims_deployment_values(monkeypatch):
    client = Mock()
    client.models.generate_content.return_value = SimpleNamespace(text=json.dumps(valid_result()))
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))

    GeminiProvider("  test-key\n", " gemini-3.5-flash-lite ", 5)

    assert genai.Client.call_args.kwargs["api_key"] == "test-key"
    assert genai.Client.call_args.kwargs["http_options"]


def test_gemini_provider_retries_local_protocol_error(monkeypatch):
    import httpx
    from app.services import ai_improvement_service as service_module

    client = Mock()
    client.models.generate_content.side_effect = [
        httpx.LocalProtocolError("transient protocol state"),
        SimpleNamespace(text=json.dumps(valid_result())),
    ]
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))
    delays = []
    monkeypatch.setattr(service_module.time, "sleep", delays.append)

    result = GeminiProvider("test-key", "gemini-3.5-flash-lite", 5).generate_improvement(
        "Some writing.", "Formal"
    )

    assert result == valid_result()
    assert client.models.generate_content.call_count == 2
    assert delays == [0.5]


def test_gemini_provider_retries_transient_api_error(monkeypatch):
    from app.services import ai_improvement_service as service_module

    client = Mock()
    client.models.generate_content.side_effect = [
        gemini_errors.APIError(503, {"error": {"message": "temporary overload"}}),
        SimpleNamespace(text=json.dumps(valid_result())),
    ]
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))
    delays = []
    monkeypatch.setattr(service_module.time, "sleep", delays.append)

    result = GeminiProvider("test-key", "gemini-3.5-flash-lite", 5).generate_improvement(
        "Some writing.", "Formal"
    )

    assert result == valid_result()
    assert client.models.generate_content.call_count == 2
    assert delays == [0.5]


def test_gemini_exception_diagnostic_redacts_key_and_submitted_text(caplog):
    import h11
    from app.services.ai_improvement_service import log_gemini_exception

    key = "private-test-api-key"
    user_text = "private submitted sentence"
    try:
        raise h11.LocalProtocolError(
            f"Invalid header x-goog-api-key: {key}; body={user_text}"
        )
    except h11.LocalProtocolError as error:
        with caplog.at_level("ERROR", logger="app.services.ai_improvement_service"):
            log_gemini_exception(error, key, user_text)

    assert "h11" in caplog.text
    assert "LocalProtocolError" in caplog.text
    assert "traceback_frames" in caplog.text
    assert "private-test-api-key" not in caplog.text
    assert user_text not in caplog.text


def test_gemini_provider_diagnoses_h11_protocol_exception_safely(monkeypatch, caplog):
    import h11

    key = "test-secret-api-key"
    user_text = "sample private writing"
    client = Mock()
    client.models.generate_content.side_effect = h11.LocalProtocolError(
        f"invalid protocol header x-goog-api-key: {key}; {user_text}"
    )
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))
    provider = GeminiProvider(key, "test-model", 2)

    with caplog.at_level("ERROR", logger="app.services.ai_improvement_service"):
        with pytest.raises(AIProviderError):
            provider.generate_improvement(user_text, "Professional")

    assert "error_module=h11" in caplog.text or "error_module=h11." in caplog.text
    assert "traceback_frames" in caplog.text
    assert key not in caplog.text
    assert user_text not in caplog.text


@pytest.mark.parametrize(
    "code,expected",
    [
        (429, AIProviderRateLimitError),
        (504, AIProviderTimeoutError),
        (401, AIProviderError),
    ],
)
def test_gemini_provider_maps_api_errors_safely(monkeypatch, caplog, code, expected):
    secret = "test-google-key-placeholder"
    error = gemini_errors.APIError(
        code,
        {"error": {"message": "provider detail " + secret}},
    )
    client = Mock()
    client.models.generate_content.side_effect = error
    monkeypatch.setattr(genai, "Client", Mock(return_value=client))
    provider = GeminiProvider(secret, "gemini-3.5-flash-lite", 5)

    with caplog.at_level("WARNING", logger="app.services.ai_improvement_service"):
        with pytest.raises(expected):
            provider.generate_improvement("Some writing.", "Formal")

    assert f"status={code}" in caplog.text
    assert "provider detail" in caplog.text
    assert secret not in caplog.text


@pytest.mark.parametrize(
    "provider_name,key_name,provider_class",
    [
        ("anthropic", "ANTHROPIC_API_KEY", AnthropicProvider),
        ("gemini", "GEMINI_API_KEY", GeminiProvider),
    ],
)
def test_service_factory_selects_configured_provider(
    monkeypatch, provider_name, key_name, provider_class
):
    from app.services import ai_improvement_service as service_module

    provider = Mock()
    factory = Mock(return_value=provider)
    monkeypatch.setattr(service_module, provider_class.__name__, factory)
    service = create_ai_improvement_service({
        "LLM_PROVIDER": provider_name,
        key_name: "test-key",
        "LLM_MODEL": "gemini-3.5-flash-lite" if provider_name == "gemini" else "test-model",
        "LLM_TIMEOUT_SECONDS": 30,
    })

    assert service.provider is provider
    factory.assert_called_once_with(
        "test-key",
        "gemini-3.5-flash-lite" if provider_name == "gemini" else "test-model",
        30,
    )


def test_service_factory_requires_secret_and_model():
    with pytest.raises(AIConfigurationError):
        create_ai_improvement_service({"LLM_MODEL": "model"})
    with pytest.raises(AIConfigurationError):
        create_ai_improvement_service({"ANTHROPIC_API_KEY": "key"})


def test_service_factory_rejects_unknown_provider_and_invalid_timeout():
    with pytest.raises(AIConfigurationError):
        create_ai_improvement_service({
            "LLM_PROVIDER": "unknown",
            "ANTHROPIC_API_KEY": "key",
            "LLM_MODEL": "model",
        })
    with pytest.raises(AIConfigurationError):
        create_ai_improvement_service({
            "ANTHROPIC_API_KEY": "key",
            "LLM_MODEL": "model",
            "LLM_TIMEOUT_SECONDS": 0,
        })
