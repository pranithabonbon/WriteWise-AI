"""
Tests for the writing analysis API.
"""

def test_analyze_valid_text(client, monkeypatch):
    """Valid text should return successful analysis results."""

    fake_result = {
        "success": True,
        "message": "Writing analysis completed successfully.",
        "grammar": {
            "error_count": 1,
            "errors": []
        },
        "readability": {
            "readability": {
                "word_count": 10
            }
        },
        "vocabulary": {
            "vocabulary": {
                "total_words": 10,
                "unique_words": 8
            }
        },
        "sentence_complexity": {
            "sentence_complexity": {
                "sentence_count": 2
            }
        },
        "score": {
            "writing_score": 85.0,
            "grade": "Very Good"
        }
    }

    from app.routes import analyze

    monkeypatch.setattr(
        analyze.analysis_service,
        "analyze",
        lambda text, context="General": {**fake_result, "context": context}
    )

    response = client.post(
        "/api/analyze",
        json={
            "text": "This is a sample text for analysis."
        }
    )

    assert response.status_code == 200

    data = response.get_json()

    assert data["success"] is True
    assert "grammar" in data
    assert "readability" in data
    assert "vocabulary" in data
    assert "sentence_complexity" in data
    assert "score" in data
    assert data["context"] == "General"


def test_analyze_accepts_writing_context(client, monkeypatch):
    from app.routes import analyze

    monkeypatch.setattr(analyze.analysis_service, "analyze", lambda text, context="General": {"success": True, "context": context})
    response = client.post("/api/analyze", json={"text": "The proposal explains the research.", "context": "Academic"})
    assert response.status_code == 200
    assert response.get_json()["context"] == "Academic"


def test_analyze_rejects_unknown_context(client):
    response = client.post("/api/analyze", json={"text": "Some writing.", "context": "Legal"})
    assert response.status_code == 400


def test_analyze_empty_text(client):
    """Empty text should return a 400 error."""

    response = client.post(
        "/api/analyze",
        json={
            "text": ""
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Please provide text to analyze."


def test_analyze_whitespace_text(client):
    """Text containing only whitespace should return a 400 error."""

    response = client.post(
        "/api/analyze",
        json={
            "text": "   \n\t   "
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Please provide text to analyze."


def test_analyze_missing_text(client):
    """Missing text field should return a 400 error."""

    response = client.post(
        "/api/analyze",
        json={}
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Please provide text to analyze."


def test_analyze_non_string_text(client):
    """Non-string text should return a 400 error."""

    response = client.post(
        "/api/analyze",
        json={
            "text": 12345
        }
    )

    assert response.status_code == 400

    data = response.get_json()

    assert data["success"] is False
    assert data["message"] == "Text must be a string."


def test_analyze_invalid_json(client):
    """Invalid JSON should return a 400 error."""

    response = client.post(
        "/api/analyze",
        data="{invalid json",
        content_type="application/json"
    )

    assert response.status_code == 400
