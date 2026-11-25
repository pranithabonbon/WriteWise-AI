"""Central configuration. Every setting comes from environment variables."""
import os

from dotenv import load_dotenv

# Reads backend/.env (if present) into os.environ
load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


class Config:
    APP_ENV = os.getenv("APP_ENV", "development").strip().lower()
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret")
    DEBUG = os.getenv("FLASK_DEBUG", "0") == "1"
    PORT = int(os.getenv("PORT", "5001"))
    CORS_ORIGINS = _split_csv(os.getenv(
        "CORS_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173",
    ))

    # Used in later phases
    MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "5"))
    # Include a small multipart envelope allowance; FileExtractor enforces the
    # exact file limit after Werkzeug has parsed the request.
    MAX_CONTENT_LENGTH = MAX_UPLOAD_MB * 1024 * 1024 + 64 * 1024
    MONGODB_URI = os.getenv("MONGODB_URI", "")
    MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME", "writewise_ai")
    MONGODB_TIMEOUT_MS = int(os.getenv("MONGODB_TIMEOUT_MS", "5000"))
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "anthropic")
    LLM_MODEL = os.getenv("LLM_MODEL", "")
    LLM_TIMEOUT_SECONDS = int(os.getenv("LLM_TIMEOUT_SECONDS", "30"))


class TestConfig(Config):
    TESTING = True
    DEBUG = False
