"""Health-check endpoint used to confirm the API (and database) are running."""
from datetime import datetime, timezone

from flask import Blueprint, jsonify

from app.db import ping_database

health_bp = Blueprint("health", __name__)


@health_bp.get("/health")
def health_check():
    return jsonify(
        {
            "status": "ok",  # the API itself is up
            "database": ping_database(),  # connected | unreachable | not_configured
            "service": "WriteWise AI API",
            "version": "0.2.0",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )