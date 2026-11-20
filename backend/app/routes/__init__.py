"""
Application factory: builds and configures the Flask app.
"""

from flask import Flask, jsonify
from flask_cors import CORS

from config import Config
from app.db import init_db


def create_app(config_class=Config):
    app = Flask(__name__)

    # Load application configuration
    app.config.from_object(config_class)

    # Initialize MongoDB
    init_db(app)

    # Configure CORS for frontend requests
    CORS(
        app,
        resources={
            r"/api/*": {
                "origins": app.config["CORS_ORIGINS"]
            }
        }
    )

    # Register route blueprints
    from app.routes.health import health_bp
    from app.routes.analyze import analyze_bp

    app.register_blueprint(
        health_bp,
        url_prefix="/api"
    )

    app.register_blueprint(
        analyze_bp,
        url_prefix="/api"
    )

    # Handle 404 errors
    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({
            "success": False,
            "error": "Resource not found"
        }), 404

    # Handle 405 errors
    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({
            "success": False,
            "error": "Method not allowed"
        }), 405

    # Handle 413 errors
    @app.errorhandler(413)
    def too_large(_error):
        return jsonify({
            "success": False,
            "error": "File is too large"
        }), 413

    # Handle 500 errors
    @app.errorhandler(500)
    def server_error(_error):
        return jsonify({
            "success": False,
            "error": "Internal server error"
        }), 500

    return app