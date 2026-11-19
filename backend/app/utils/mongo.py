"""Small helpers for working with MongoDB documents."""
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def to_object_id(value) -> ObjectId:
    """Convert a string (or ObjectId) to ObjectId. Raises ValueError if invalid."""
    if isinstance(value, ObjectId):
        return value
    try:
        return ObjectId(str(value))
    except (InvalidId, TypeError) as exc:
        raise ValueError("Invalid id") from exc


def serialize(value):
    """Make a MongoDB document JSON-safe (ObjectId -> str, datetime -> ISO string)."""
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        if value.tzinfo is None:  # PyMongo returns naive UTC datetimes by default
            value = value.replace(tzinfo=timezone.utc)
        return value.isoformat()
    if isinstance(value, dict):
        return {key: serialize(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [serialize(item) for item in value]
    return value