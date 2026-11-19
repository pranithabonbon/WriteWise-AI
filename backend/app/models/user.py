"""Users collection. Stores only what authentication needs."""
from pymongo.errors import DuplicateKeyError

from app.db import get_db
from app.utils.mongo import to_object_id, utcnow


def create_user(email: str, password_hash: str, name: str = "") -> dict:
    """Insert a user. `password_hash` must already be hashed - never pass a plain password."""
    email = (email or "").strip().lower()
    if not email or "@" not in email:
        raise ValueError("A valid email is required")
    if not password_hash:
        raise ValueError("password_hash is required")

    user = {
        "email": email,
        "name": (name or "").strip(),
        "password_hash": password_hash,
        "created_at": utcnow(),
    }
    try:
        result = get_db().users.insert_one(user)
    except DuplicateKeyError as exc:
        raise ValueError("Email already registered") from exc
    user["_id"] = result.inserted_id
    return user


def get_user_by_email(email: str) -> dict | None:
    return get_db().users.find_one({"email": (email or "").strip().lower()})


def get_user_by_id(user_id) -> dict | None:
    return get_db().users.find_one({"_id": to_object_id(user_id)})