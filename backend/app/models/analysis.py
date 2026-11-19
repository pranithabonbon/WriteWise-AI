"""Analyses collection: results of analyzing one document.

Rule-based NLP output and LLM output are stored in separate fields so the UI
can always label which is which.
"""
from app.db import get_db
from app.utils.constants import CONTEXTS
from app.utils.mongo import to_object_id, utcnow

SCORE_KEYS = ("grammar", "readability", "vocabulary", "complexity", "overall")


def create_analysis(
    document_id,
    document_name: str,
    context: str,
    rule_based: dict,
    scores: dict,
    metrics: dict,
    llm: dict | None = None,
    user_id=None,
) -> dict:
    if context not in CONTEXTS:
        raise ValueError(f"context must be one of {CONTEXTS}")
    missing = [key for key in SCORE_KEYS if key not in scores]
    if missing:
        raise ValueError(f"scores is missing: {', '.join(missing)}")

    analysis = {
        "user_id": user_id,
        "document_id": to_object_id(document_id),
        "document_name": document_name,  # copied so the history list needs no join
        "context": context,
        "metrics": metrics,  # word_count, sentence_count, grammar_error_count
        "scores": scores,  # each 0-100
        "rule_based": rule_based,  # grammar, readability, vocabulary, complexity details
        "llm": llm or {},  # tone assessment, rewrites, explanations
        "created_at": utcnow(),
    }
    result = get_db().analyses.insert_one(analysis)
    analysis["_id"] = result.inserted_id
    return analysis


def get_analysis(analysis_id, user_id=None) -> dict | None:
    return get_db().analyses.find_one(
        {"_id": to_object_id(analysis_id), "user_id": user_id}
    )


def list_analyses(user_id=None, limit: int = 20, skip: int = 0) -> list[dict]:
    """Newest first. Returns light summaries only (no heavy detail fields)."""
    limit = max(1, min(int(limit), 100))
    skip = max(0, int(skip))
    cursor = (
        get_db()
        .analyses.find(
            {"user_id": user_id},
            {
                "document_id": 1,
                "document_name": 1,
                "context": 1,
                "metrics": 1,
                "scores": 1,
                "created_at": 1,
            },
        )
        .sort([("created_at", -1), ("_id", -1)])  # _id breaks same-millisecond ties
        .skip(skip)
        .limit(limit)
    )
    return list(cursor)


def update_llm_results(analysis_id, llm_updates: dict, user_id=None) -> bool:
    """Merge new LLM output (e.g. a rewrite) into an existing analysis."""
    changes = {f"llm.{key}": value for key, value in llm_updates.items()}
    result = get_db().analyses.update_one(
        {"_id": to_object_id(analysis_id), "user_id": user_id}, {"$set": changes}
    )
    return result.matched_count == 1


def delete_analysis(analysis_id, user_id=None) -> bool:
    result = get_db().analyses.delete_one(
        {"_id": to_object_id(analysis_id), "user_id": user_id}
    )
    return result.deleted_count == 1


def delete_history(user_id=None) -> dict:
    """Delete every analysis and document that belongs to this user."""
    db = get_db()
    analyses = db.analyses.delete_many({"user_id": user_id}).deleted_count
    documents = db.documents.delete_many({"user_id": user_id}).deleted_count
    return {"analyses_deleted": analyses, "documents_deleted": documents}