"""Application factory: builds and configures the Flask app."""

from flask import Flask, jsonify
from flask_cors import CORS
from urllib.parse import urlsplit

from config import Config
from app.db import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    _validate_production_config(app.config)

    init_db(app)

    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"]
            }
        }
    )

    from app.routes.health import health_bp
    from app.routes.analyze import analyze_bp
    from app.routes.upload import upload_bp
    from app.routes.improve import improve_bp
    from app.routes.history import history_bp
    from app.routes.agent import agent_bp

    app.register_blueprint(health_bp, url_prefix="/api")
    app.register_blueprint(analyze_bp, url_prefix="/api")
    app.register_blueprint(upload_bp, url_prefix="/api")
    app.register_blueprint(improve_bp, url_prefix="/api")
    app.register_blueprint(history_bp, url_prefix="/api")
    app.register_blueprint(agent_bp, url_prefix="/api")

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Resource not found"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Method not allowed"}), 405

    @app.errorhandler(413)
    def too_large(_error):
        max_mb = app.config.get("MAX_UPLOAD_MB", 5)
        return jsonify({
            "success": False,
            "error": "File is too large",
            "message": f"File is too large. Maximum upload size is {max_mb} MB.",
        }), 413

    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({"error": "Internal server error"}), 500

    return app


def _validate_production_config(config):
    """Fail fast on unsafe or incomplete production configuration."""
    if config.get("APP_ENV") != "production":
        return

    secret = config.get("SECRET_KEY")
    if not isinstance(secret, str) or len(secret) < 32 or secret == "dev-only-secret":
        raise RuntimeError("Production requires a random SECRET_KEY of at least 32 characters.")
    if config.get("DEBUG"):
        raise RuntimeError("FLASK_DEBUG must be disabled in production.")

    origins = config.get("CORS_ORIGINS") or []
    if not origins or any(
        not isinstance(origin, str)
        or origin == "*"
        or urlsplit(origin).scheme != "https"
        or not urlsplit(origin).netloc
        or urlsplit(origin).path not in ("", "/")
        for origin in origins
    ):
        raise RuntimeError("Production CORS_ORIGINS must contain exact HTTPS frontend origins.")

    uri = config.get("MONGODB_URI", "")
    if not isinstance(uri, str) or not uri.startswith(("mongodb://", "mongodb+srv://")):
        raise RuntimeError("Production requires a valid MONGODB_URI.")

    provider = str(config.get("LLM_PROVIDER", "")).strip().lower()
    key_name = "GEMINI_API_KEY" if provider == "gemini" else "ANTHROPIC_API_KEY"
    if provider not in ("gemini", "anthropic") or not str(config.get(key_name, "")).strip() or not str(config.get("LLM_MODEL", "")).strip():
        raise RuntimeError("Production requires a configured AI provider key and model.")


