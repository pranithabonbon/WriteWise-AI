import pytest

from app.models import analysis as analyses
from app.models import document as documents
from app.models import user as users

SCORES = {"grammar": 90, "readability": 70, "vocabulary": 60, "complexity": 80, "overall": 75}
METRICS = {"word_count": 5, "sentence_count": 1, "grammar_error_count": 0}


def make_doc(user_id=None, name="Essay"):
    return documents.create_document(name, "This is a short test.", "text", "academic", user_id)


def make_analysis(doc, user_id=None):
    return analyses.create_analysis(
        doc["_id"], doc["name"], "academic",
        rule_based={"grammar": {"errors": []}}, scores=SCORES, metrics=METRICS, user_id=user_id,
    )


# ---------- users ----------
def test_create_and_fetch_user(app):
    created = users.create_user("Ana@Example.com ", "hashed", "Ana")
    assert created["email"] == "ana@example.com"
    assert users.get_user_by_email("ANA@example.com")["_id"] == created["_id"]
    assert users.get_user_by_id(str(created["_id"]))["name"] == "Ana"


def test_duplicate_email_rejected(app):
    users.create_user("a@b.com", "hash")
    with pytest.raises(ValueError, match="already registered"):
        users.create_user("A@B.com", "hash")


# ---------- documents ----------
def test_create_document_counts_words(app):
    doc = make_doc()
    assert doc["word_count"] == 5
    assert documents.get_document(doc["_id"])["name"] == "Essay"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"text": "   "},
        {"text": "hello", "source_type": "exe"},
        {"text": "hello", "context": "casual"},
    ],
)
def test_invalid_document_rejected(app, kwargs):
    with pytest.raises(ValueError):
        documents.create_document("x", **kwargs)


def test_invalid_id_rejected(app):
    with pytest.raises(ValueError, match="Invalid id"):
        documents.get_document("not-an-id")


# ---------- analyses ----------
def test_analysis_roundtrip_and_llm_merge(app):
    doc = make_doc()
    a = make_analysis(doc)
    assert analyses.update_llm_results(a["_id"], {"rewrite": "Better text."}) is True
    stored = analyses.get_analysis(a["_id"])
    assert stored["llm"]["rewrite"] == "Better text."
    assert stored["rule_based"]["grammar"] == {"errors": []}  # untouched


def test_analysis_requires_all_scores(app):
    doc = make_doc()
    with pytest.raises(ValueError, match="missing"):
        analyses.create_analysis(doc["_id"], "x", "academic", {}, {"grammar": 1}, {})


def test_list_is_newest_first_and_light(app):
    doc = make_doc()
    first, second = make_analysis(doc), make_analysis(doc)
    listed = analyses.list_analyses()
    assert [item["_id"] for item in listed] == [second["_id"], first["_id"]]
    assert "rule_based" not in listed[0]


def test_users_cannot_see_each_others_data(app):
    doc = make_doc(user_id="u1")
    a = make_analysis(doc, user_id="u1")
    assert analyses.get_analysis(a["_id"], user_id="u2") is None
    assert analyses.delete_analysis(a["_id"], user_id="u2") is False
    assert analyses.get_analysis(a["_id"], user_id="u1") is not None


def test_delete_history_only_removes_own_data(app):
    mine, theirs = make_doc(user_id="u1"), make_doc(user_id="u2")
    make_analysis(mine, "u1")
    make_analysis(theirs, "u2")
    result = analyses.delete_history("u1")
    assert result == {"analyses_deleted": 1, "documents_deleted": 1}
    assert len(analyses.list_analyses("u2")) == 1