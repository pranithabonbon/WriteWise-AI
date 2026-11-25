"""
Tests for the file upload API.
"""

from io import BytesIO
import zipfile

import pymupdf
from docx import Document


def make_pdf_bytes():
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "Upload sample paragraph.")
    data = document.tobytes()
    document.close()
    return data


def make_docx_bytes():
    document = Document()
    document.add_paragraph("Uploaded introduction.")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Topic"
    table.rows[0].cells[1].text = "Clarity"
    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def upload(client, data, filename, extra_form=None, query=""):
    form = {
        "file": (BytesIO(data), filename),
    }
    if extra_form:
        form.update(extra_form)

    return client.post(
        "/api/upload" + query,
        data=form,
        content_type="multipart/form-data",
    )


def test_upload_txt_success(client):
    text = "This is a sample text for upload."
    response = upload(client, text.encode("utf-8"), "example.txt")

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["message"] == "File uploaded and text extracted successfully."
    assert data["text"] == text
    assert data["file"] == {
        "filename": "example.txt",
        "file_type": "TXT",
        "character_count": len(text),
        "word_count": 7,
    }
    assert "analysis" not in data


def test_upload_pdf_success(client):
    response = upload(client, make_pdf_bytes(), "example.pdf")

    assert response.status_code == 200
    data = response.get_json()

    assert data["success"] is True
    assert data["file"]["filename"] == "example.pdf"
    assert data["file"]["file_type"] == "PDF"
    assert "Upload sample paragraph." in data["text"]
    assert data["file"]["word_count"] == len(data["text"].split())


def test_upload_docx_success(client):
    response = upload(client, make_docx_bytes(), "example.docx")

    assert response.status_code == 200
    data = response.get_json()

    assert data["file"]["file_type"] == "DOCX"
    assert "Uploaded introduction." in data["text"]
    assert "Topic" in data["text"]
    assert "Clarity" in data["text"]


def test_upload_missing_file(client):
    response = client.post(
        "/api/upload",
        data={},
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "file" in data["message"].lower()


def test_upload_empty_file(client):
    response = upload(client, b"", "empty.txt")

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "empty" in data["message"].lower()


def test_upload_unsupported_extension(client):
    response = upload(client, b"not a document", "script.exe")

    assert response.status_code == 415
    data = response.get_json()
    assert data["success"] is False
    assert "Unsupported" in data["message"]


def test_upload_corrupt_pdf(client):
    response = upload(client, b"%PDF-1.4\nbad", "broken.pdf")

    assert response.status_code == 400
    data = response.get_json()
    assert data["success"] is False
    assert "invalid or corrupted" in data["message"]


def test_upload_rejects_mismatched_content(client):
    response = upload(client, b"Plain text only.", "report.docx")

    assert response.status_code == 400
    assert response.get_json()["success"] is False


def test_upload_oversized_file(client, app):
    app.config["MAX_CONTENT_LENGTH"] = 32

    response = upload(client, b"A" * 200, "big.txt")

    assert response.status_code == 413
    data = response.get_json()
    assert data["success"] is False
    assert "too large" in data["message"].lower()


def test_upload_can_analyze_with_existing_service(client, monkeypatch):
    """The optional flag must call AnalysisService with the extracted text."""

    captured = {}

    def fake_analyze(text):
        captured["text"] = text
        return {
            "success": True,
            "message": "Writing analysis completed successfully.",
            "score": {
                "writing_score": 88.0,
                "grade": "Very Good",
            },
        }

    from app.routes import upload as upload_route

    monkeypatch.setattr(upload_route.analysis_service, "analyze", fake_analyze)

    text = "This paragraph is ready for analysis."
    response = upload(
        client,
        text.encode("utf-8"),
        "notes.txt",
        extra_form={"analyze": "true"},
    )

    assert response.status_code == 200
    data = response.get_json()

    assert captured["text"] == text
    assert data["success"] is True
    assert data["message"] == (
        "File uploaded, text extracted, and analyzed successfully."
    )
    assert data["analysis"]["score"]["writing_score"] == 88.0
    assert data["text"] == text


def test_upload_analysis_query_runs_nlp_pipeline(client, monkeypatch):
    """
    Analysis should use the real AnalysisService pipeline.

    Grammar is stubbed so the test does not start LanguageTool.
    Readability, vocabulary, sentence complexity, and scoring still run.
    """

    class DummyGrammarAnalyzer:
        def __init__(self, language="en-US"):
            self.language = language

        def analyze(self, text, context="General"):
            return {
                "error_count": 0,
                "errors": [],
                "message": "No grammar or spelling errors found.",
            }

        def close(self):
            return None

    from app.routes import upload as upload_route

    monkeypatch.setattr(
        upload_route.analysis_service.grammar_analyzer,
        "analyze",
        DummyGrammarAnalyzer().analyze,
    )

    text = (
        "Clear writing helps readers understand a new idea. "
        "Short sentences keep the argument easy to follow."
    )
    response = upload(
        client,
        text.encode("utf-8"),
        "analysis.txt",
        query="?analyze=true",
    )

    assert response.status_code == 200
    data = response.get_json()
    analysis = data["analysis"]

    assert analysis["success"] is True
    assert analysis["grammar"]["error_count"] == 0
    assert analysis["readability"]["readability"]["word_count"] > 0
    assert analysis["vocabulary"]["vocabulary"]["total_words"] > 0
    assert analysis["sentence_complexity"]["sentence_complexity"]["sentence_count"] == 2
    assert "writing_score" in analysis["score"]


def test_upload_corrupt_docx_returns_validation_error(client):
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("readme.txt", "not a document")

    response = upload(client, buffer.getvalue(), "broken.docx")

    assert response.status_code == 400
    assert response.get_json()["success"] is False
