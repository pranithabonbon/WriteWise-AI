"""API for user initiated writing analysis history."""

from bson.errors import InvalidId
from flask import Blueprint, jsonify, request
from pymongo.errors import PyMongoError

from app.db import DatabaseNotConfigured
from app.models import saved_analysis
from app.utils.mongo import serialize

history_bp = Blueprint("history", __name__)
MAX_TEXT_LENGTH = 12000


def _valid_payload(data):
    if not isinstance(data, dict):
        return "Request body must contain a JSON object."
    text = data.get("text")
    analysis = data.get("analysis")
    if not isinstance(text, str) or not text.strip():
        return "Text must be a non-empty string."
    if len(text) > MAX_TEXT_LENGTH:
        return f"Text must be {MAX_TEXT_LENGTH} characters or fewer."
    if not isinstance(analysis, dict) or analysis.get("success") is not True:
        return "A successful analysis result is required."
    if not isinstance(analysis.get("score"), dict):
        return "Analysis score data is required."
    for key in ("grammar", "readability", "vocabulary", "sentence_complexity"):
        if not isinstance(analysis.get(key), dict):
            return f"Analysis {key} data is required."
    recommendations = data.get("recommendations", [])
    if not isinstance(recommendations, list) or any(not isinstance(item, dict) for item in recommendations):
        return "Recommendations must be a list of objects."
    return None


@history_bp.route("/history", methods=["POST"])
def create_saved_analysis():
    data = request.get_json(silent=True)
    problem = _valid_payload(data)
    if problem:
        return jsonify({"success": False, "message": problem}), 400
    analysis = dict(data["analysis"])
    analysis["recommendations"] = data.get("recommendations", [])
    try:
        record = saved_analysis.save_analysis(data["text"], analysis)
        return jsonify({"success": True, "analysis": serialize(record)}), 201
    except (DatabaseNotConfigured, PyMongoError):
        return jsonify({"success": False, "message": "Writing history is temporarily unavailable."}), 503


@history_bp.route("/history", methods=["GET"])
def get_saved_analyses():
    try:
        records = saved_analysis.list_analyses()
        return jsonify({"success": True, "analyses": serialize(records)}), 200
    except (DatabaseNotConfigured, PyMongoError):
        return jsonify({"success": False, "message": "Writing history is temporarily unavailable."}), 503


@history_bp.route("/history/<analysis_id>", methods=["GET"])
def get_saved_analysis(analysis_id):
    try:
        record = saved_analysis.get_analysis(analysis_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid analysis ID."}), 400
    except (DatabaseNotConfigured, PyMongoError):
        return jsonify({"success": False, "message": "Writing history is temporarily unavailable."}), 503
    if record is None:
        return jsonify({"success": False, "message": "Saved analysis not found."}), 404
    return jsonify({"success": True, "analysis": serialize(record)}), 200


@history_bp.route("/history/<analysis_id>", methods=["DELETE"])
def remove_saved_analysis(analysis_id):
    try:
        deleted = saved_analysis.delete_analysis(analysis_id)
    except ValueError:
        return jsonify({"success": False, "message": "Invalid analysis ID."}), 400
    except (DatabaseNotConfigured, PyMongoError):
        return jsonify({"success": False, "message": "Writing history is temporarily unavailable."}), 503
    if not deleted:
        return jsonify({"success": False, "message": "Saved analysis not found."}), 404
    return jsonify({"success": True, "message": "Saved analysis deleted."}), 200
