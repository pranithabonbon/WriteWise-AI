"""MongoDB connection layer (PyMongo).

One MongoClient is created per app and reused. PyMongo connects lazily, so
creating the client never blocks; the first real operation (or ping) connects.
"""
import certifi
from flask import current_app
from pymongo import ASCENDING, DESCENDING, MongoClient
from pymongo.errors import PyMongoError

CLIENT_KEY = "mongo_client"


class DatabaseNotConfigured(RuntimeError):
    """Raised when a database operation is attempted without MONGODB_URI."""


def init_db(app):
    """Create the Mongo client and attach it to the Flask app."""
    client = app.config.get("MONGO_CLIENT")  # tests inject an in-memory client here

    if client is None and app.config.get("MONGODB_URI"):
        uri = app.config["MONGODB_URI"]
        options = {"serverSelectionTimeoutMS": app.config["MONGODB_TIMEOUT_MS"]}
        if uri.startswith("mongodb+srv://"):
            # Atlas uses TLS; certifi supplies trusted CA certificates on every OS
            options["tlsCAFile"] = certifi.where()
        client = MongoClient(uri, **options)

    app.extensions[CLIENT_KEY] = client


def get_db():
    """Return the application's database. Use inside a request or app context."""
    client = current_app.extensions.get(CLIENT_KEY)
    if client is None:
        raise DatabaseNotConfigured("MONGODB_URI is not set. Add it to backend/.env.")
    return client[current_app.config["MONGODB_DB_NAME"]]


def ping_database() -> str:
    """Return 'connected', 'unreachable' or 'not_configured'."""
    client = current_app.extensions.get(CLIENT_KEY)
    if client is None:
        return "not_configured"
    try:
        client.admin.command("ping")
        return "connected"
    except PyMongoError:
        return "unreachable"


def ensure_indexes(db):
    """Create indexes (safe to run repeatedly)."""
    # One account per email address
    db.users.create_index([("email", ASCENDING)], unique=True, name="uniq_email")

    # "Show my newest documents / analyses first"
    db.documents.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_recent"
    )
    db.analyses.create_index(
        [("user_id", ASCENDING), ("created_at", DESCENDING)], name="user_recent"
    )
    # Find all analyses of a given document
    db.analyses.create_index([("document_id", ASCENDING)], name="by_document")
    db.writing_history.create_index(
        [("created_at", DESCENDING)], name="history_recent"
    )
