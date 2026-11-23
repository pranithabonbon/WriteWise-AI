"""Tests for explicitly saved writing analysis history."""

from pymongo.errors import PyMongoError


SAMPLE_ANALYSIS = {
    "success": True,
    "score": {"writing_score": 82.5, "grade": "Very Good"},
    "grammar": {"available": True, "error_count": 1, "errors": [{"offset": 0}]},
    "readability": {"readability": {"flesch_reading_ease": 64.2}},
    "vocabulary": {"vocabulary": {"total_words": 5}},
    "sentence_complexity": {"sentence_complexity": {"sentence_count": 1}},
}


def save(client, text="A sample sentence."):
    return client.post("/api/history", json={
        "text": text,
        "analysis": SAMPLE_ANALYSIS,
        "recommendations": [{"heading": "Grammar", "text": "Review one issue."}],
    })


def test_save_analysis_returns_stored_snapshot(client):
    response = save(client)
    assert response.status_code == 201
    result = response.get_json()["analysis"]
    assert result["text"] == "A sample sentence."
    assert result["analysis"]["score"]["writing_score"] == 82.5
    assert result["analysis"]["recommendations"][0]["heading"] == "Grammar"
    assert result["created_at"]
    assert len(result["_id"]) == 24


def test_retrieve_history_is_newest_first_and_uses_summary(client):
    older = save(client).get_json()["analysis"]
    newer = save(client, "A newer sentence.").get_json()["analysis"]
    response = client.get("/api/history")
    assert response.status_code == 200
    records = response.get_json()["analyses"]
    assert [item["_id"] for item in records] == [newer["_id"], older["_id"]]
    assert records[0]["analysis"]["score"]["writing_score"] == 82.5
    assert "vocabulary" not in records[0]["analysis"]


def test_retrieve_one_saved_analysis(client):
    created = save(client).get_json()["analysis"]
    response = client.get(f"/api/history/{created['_id']}")
    assert response.status_code == 200
    assert response.get_json()["analysis"]["text"] == "A sample sentence."
    assert response.get_json()["analysis"]["analysis"]["sentence_complexity"] == SAMPLE_ANALYSIS["sentence_complexity"]


def test_delete_saved_analysis(client):
    created = save(client).get_json()["analysis"]
    response = client.delete(f"/api/history/{created['_id']}")
    assert response.status_code == 200
    assert client.get(f"/api/history/{created['_id']}").status_code == 404


def test_reject_invalid_save_input(client):
    for payload in (
        None,
        {"text": "  ", "analysis": SAMPLE_ANALYSIS},
        {"text": "ok", "analysis": {"success": True}},
        {"text": "x" * 12001, "analysis": SAMPLE_ANALYSIS},
        {"text": "ok", "analysis": SAMPLE_ANALYSIS, "recommendations": "bad"},
    ):
        response = client.post("/api/history", json=payload)
        assert response.status_code == 400


def test_invalid_and_missing_ids(client):
    assert client.get("/api/history/not-an-object-id").status_code == 400
    assert client.delete("/api/history/not-an-object-id").status_code == 400
    missing_id = "000000000000000000000001"
    assert client.get(f"/api/history/{missing_id}").status_code == 404
    assert client.delete(f"/api/history/{missing_id}").status_code == 404


def test_database_errors_return_service_unavailable(client, monkeypatch):
    from app.models import saved_analysis

    def fail():
        raise PyMongoError("database unavailable")

    monkeypatch.setattr(saved_analysis, "get_db", fail)
    assert save(client).status_code == 503
    assert client.get("/api/history").status_code == 503
    assert client.get("/api/history/000000000000000000000001").status_code == 503
    assert client.delete("/api/history/000000000000000000000001").status_code == 503
