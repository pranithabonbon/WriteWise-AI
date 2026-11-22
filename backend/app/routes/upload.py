"""
File upload API.

Accepts one document, extracts its text, and can optionally run the
existing writing analysis on that text.
"""

from flask import Blueprint, current_app, jsonify, request
from werkzeug.exceptions import HTTPException

from app.services.analysis_service import AnalysisService
from app.services.file_extractor import (
    DEFAULT_MAX_BYTES,
    FileExtractionError,
    FileExtractor,
)

upload_bp = Blueprint("upload", __name__)

# Reused so tests can replace analyze() without starting a new service.
analysis_service = AnalysisService()

ANALYZE_TRUE_VALUES = {"1", "true", "yes", "on"}


@upload_bp.route("/upload", methods=["POST"])
def upload_file():
    """Validate an uploaded file, extract its text, and optionally analyze it."""

    try:
        extractor = FileExtractor(max_bytes=_max_upload_bytes())
        extracted = extractor.extract_upload(request.files.get("file"))
    except FileExtractionError as error:
        return jsonify({
            "success": False,
            "message": str(error),
        }), error.status_code
    except HTTPException:
        # Let Flask handle limits such as a request larger than 5 MB.
        raise
    except Exception as error:
        return jsonify({
            "success": False,
            "message": "File upload failed.",
            "error": str(error),
        }), 500

    response = {
        "success": True,
        "message": "File uploaded and text extracted successfully.",
        "file": {
            "filename": extracted["filename"],
            "file_type": extracted["file_type"],
            "character_count": extracted["character_count"],
            "word_count": extracted["word_count"],
        },
        "text": extracted["text"],
    }

    if not _analysis_requested():
        return jsonify(response), 200

    try:
        analysis = analysis_service.analyze(extracted["text"])
    except Exception as error:
        return jsonify({
            "success": False,
            "message": "Text was extracted, but analysis failed.",
            "error": str(error),
        }), 500

    if not analysis.get("success", False):
        return jsonify({
            "success": False,
            "message": analysis.get(
                "message",
                "Text was extracted, but analysis failed.",
            ),
            "file": response["file"],
            "text": extracted["text"],
        }), 400

    response["analysis"] = analysis
    response["message"] = (
        "File uploaded, text extracted, and analyzed successfully."
    )
    return jsonify(response), 200


def _max_upload_bytes():
    """Use the app limit so tests and deployment share one setting."""

    configured = current_app.config.get("MAX_CONTENT_LENGTH")
    if isinstance(configured, int) and configured > 0:
        return configured
    return DEFAULT_MAX_BYTES


def _analysis_requested():
    """True when the form field or query string asks for analysis."""

    raw_value = request.form.get("analyze", request.args.get("analyze", ""))
    return str(raw_value).strip().lower() in ANALYZE_TRUE_VALUES
