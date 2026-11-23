"""Persistence helpers for explicitly saved writing analyses."""

from app.db import get_db
from app.utils.mongo import to_object_id, utcnow


def save_analysis(text: str, analysis: dict) -> dict:
    document = {
        "text": text,
        "analysis": analysis,
        "created_at": utcnow(),
    }
    result = get_db().writing_history.insert_one(document)
    document["_id"] = result.inserted_id
    return document


def list_analyses():
    return list(
        get_db().writing_history.find(
            {}, {"text": 1, "analysis.score": 1, "analysis.grammar": 1,
                "analysis.readability": 1, "created_at": 1}
        ).sort([("created_at", -1), ("_id", -1)])
    )


def get_analysis(analysis_id: str):
    return get_db().writing_history.find_one({"_id": to_object_id(analysis_id)})


def delete_analysis(analysis_id: str) -> bool:
    result = get_db().writing_history.delete_one({"_id": to_object_id(analysis_id)})
    return result.deleted_count == 1
