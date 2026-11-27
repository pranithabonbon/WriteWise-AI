"""AI writing agent API."""

from flask import Blueprint, current_app, jsonify, request

from app.services.ai_agent_service import (
    AIWritingAgent, AIProviderUnavailableError, MAX_TOOL_ROUNDS,
)
from app.services.ai_improvement_service import (
    AIConfigurationError, AIProviderError, AIProviderRateLimitError,
    AIProviderTimeoutError, AIImprovementError, InputValidationError,
)

agent_bp = Blueprint("agent", __name__)


@agent_bp.post("/agent/analyze")
def analyze_with_agent():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return _error("Request body must be a JSON object.", 400)
    text, goal = data.get("text"), data.get("goal")
    tone = data.get("tone", "Professional")
    try:
        # Validate before creating the Gemini client.
        from app.services.ai_improvement_service import validate_improvement_input
        validate_improvement_input(text, tone, "General")
        if not isinstance(goal, str) or not goal.strip() or len(goal) > 500:
            raise ValueError("Goal must be a non-empty string of at most 500 characters.")
        result = AIWritingAgent(current_app.config).analyze(text, goal, tone)
        return jsonify({"success": True, "max_tool_rounds": MAX_TOOL_ROUNDS, **result}), 200
    except InputValidationError as error:
        return _error(str(error), 400)
    except ValueError as error:
        return _error(str(error), 400)
    except AIConfigurationError:
        return _error("Gemini is not configured on this server.", 503)
    except AIProviderTimeoutError:
        return _error("The AI request timed out. Please try again.", 504)
    except AIProviderRateLimitError:
        return _error("The AI service is busy. Please try again shortly.", 429)
    except AIProviderUnavailableError:
        return _error(
            "Gemini is temporarily unavailable after several attempts. Please try again shortly.",
            503,
        )
    except AIProviderError:
        return _error(
            "Gemini could not process the request. Check the server API key and model configuration.",
            502,
        )
    except AIImprovementError:
        current_app.logger.exception("AI writing agent failed")
        return _error("The AI agent could not complete the request. Please try again.", 502)
    except Exception:
        current_app.logger.exception("Unexpected AI writing agent failure")
        return _error("The AI agent could not complete the request. Please try again.", 502)


def _error(message, status):
    return jsonify({"success": False, "message": message}), status
