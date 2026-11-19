"""Documents collection: the text a user submitted for analysis."""
from app.db import get_db
from app.utils.constants import CONTEXTS, SOURCE_TYPES
from app.utils.mongo import to_object_id, utcnow


def create_document(
    name: str,
    text: str,
    source_type: str = "text",
    context: str = "professional",
    user_id=None,
) -> dict:
    text = (text or "").strip()
    if not text:
        raise ValueError("Text cannot be empty")
    if source_type not in SOURCE_TYPES:
        raise ValueError(f"source_type must be one of {SOURCE_TYPES}")
    if context not in CONTEXTS:
        raise ValueError(f"context must be one of {CONTEXTS}")

    document = {
        "user_id": user_id,
        "name": (name or "").strip() or "Untitled document",
        "source_type": source_type,
        "context": context,
        "text": text,
        "word_count": len(text.split()),
        "created_at": utcnow(),
    }
    result = get_db().documents.insert_one(document)
    document["_id"] = result.inserted_id
    return document


def get_document(document_id, user_id=None) -> dict | None:
    return get_db().documents.find_one(
        {"_id": to_object_id(document_id), "user_id": user_id}
    )