"""
Writing analysis API routes.
"""

from flask import Blueprint, request, jsonify

from app.services.analysis_service import AnalysisService

analyze_bp = Blueprint("analyze", __name__)

analysis_service = AnalysisService()


@analyze_bp.route("/analyze", methods=["POST"])
def analyze_text():
    try:
        data = request.get_json(silent=True)

        if data is None:
            return jsonify({
                "success": False,
                "message": "Request body must contain JSON."
            }), 400

        text = data.get("text", "")

        if not isinstance(text, str):
            return jsonify({
                "success": False,
                "message": "Text must be a string."
            }), 400

        if not text.strip():
            return jsonify({
                "success": False,
                "message": "Please provide text to analyze."
            }), 400

        result = analysis_service.analyze(text)

        return jsonify(result), 200

    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Analysis failed.",
            "error": str(e)
        }), 500
    