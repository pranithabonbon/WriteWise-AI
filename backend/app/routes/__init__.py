"""Application factory: builds and configures the Flask app."""
from flask import Flask, jsonify
from flask_cors import CORS

from app.db import init_db
from config import Config


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Database client (does not connect until first use)
    init_db(app)

    # Only the listed frontend origins may call /api/* from a browser
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})
    # ... rest unchanged