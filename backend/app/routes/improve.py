"""AI writing improvement API."""

from flask import Blueprint, current_app, jsonify, request

from app.services.ai_improvement_service import (
    AIConfigurationError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    AIImprovementError,
    InputValidationError,
    InvalidAIResponseError,
    create_ai_improvement_service,
    validate_improvement_input,
)
from app.utils.writing_contexts import WRITING_CONTEXTS

improve_bp = Blueprint("improve", __name__)


@improve_bp.post("/improve")
def improve_text():
    """Return a transient rewrite and writing feedback; nothing is saved."""

    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Request body must be a JSON object.", 400)

    text = data.get("text")
    tone = data.get("tone", "Professional")
    context = data.get("context", "General")

    # Validate before building a client, so empty/invalid input never reaches the provider.
    try:
        validate_improvement_input(text, tone, context)
    except InputValidationError as error:
        return _error(str(error), 400)

    try:
        service = create_ai_improvement_service(current_app.config)
        result = service.improve(text, tone, context)
        return jsonify({
            "success": True,
            "tone": tone,
            "context": context,
            **result,
        }), 200
    except InputValidationError as error:
        return _error(str(error), 400)
    except AIConfigurationError:
        return _error("AI improvement is not configured on this server.", 503)
    except AIProviderTimeoutError:
        return _error("The AI request timed out. Please try again.", 504)
    except AIProviderRateLimitError:
        return _error("The AI service is busy. Please try again shortly.", 429)
    except (AIProviderError, InvalidAIResponseError):
        return _error("The AI service could not complete the request. Please try again.", 502)
    except AIImprovementError:
        return _error("The AI service could not complete the request. Please try again.", 502)
    except Exception:
        # Keep SDK, transport, provider, and internal exception details server-side.
        current_app.logger.exception("Unexpected AI improvement failure")
        return _error("The AI service could not complete the request. Please try again.", 502)


def _error(message: str, status: int):
    return jsonify({"success": False, "message": message}), status
