"""
Tests for TXT, PDF, and DOCX text extraction.
"""

from io import BytesIO
import zipfile

import pymupdf
import pytest
from docx import Document

from app.services.file_extractor import (
    EmptyFileError,
    FileExtractor,
    FileTooLargeError,
    InvalidFileError,
    MissingFilenameError,
    UnsupportedFileTypeError,
)


def make_pdf_bytes():
    """Build a two-page PDF in memory."""

    document = pymupdf.open()
    first_page = document.new_page()
    first_page.insert_text((72, 72), "Hello from page one.")
    second_page = document.new_page()
    second_page.insert_text((72, 72), "Second page text.")
    data = document.tobytes()
    document.close()
    return data


def make_docx_bytes():
    """Build a DOCX with one paragraph and one table."""

    document = Document()
    document.add_paragraph("Introduction paragraph")
    table = document.add_table(rows=1, cols=2)
    table.rows[0].cells[0].text = "Term"
    table.rows[0].cells[1].text = "Definition"

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_extract_txt():
    extractor = FileExtractor()
    text = "Hello from a text file."

    result = extractor.extract(text.encode("utf-8"), "notes.txt")

    assert result["success"] is True
    assert result["filename"] == "notes.txt"
    assert result["file_type"] == "TXT"
    assert result["text"] == text
    assert result["character_count"] == len(text)
    assert result["word_count"] == 5


def test_extract_txt_with_windows_encoding():
    """Bytes that are not valid UTF-8 should still be read."""

    text = "The café is open."
    result = FileExtractor().extract(text.encode("cp1252"), "cafe.TXT")

    assert result["file_type"] == "TXT"
    assert result["filename"] == "cafe.TXT"
    assert "café" in result["text"]
    assert result["word_count"] == 4


def test_extract_pdf_all_pages():
    result = FileExtractor().extract(make_pdf_bytes(), "essay.pdf")

    assert result["success"] is True
    assert result["file_type"] == "PDF"
    assert "Hello from page one." in result["text"]
    assert "Second page text." in result["text"]
    assert result["word_count"] == len(result["text"].split())
    assert result["character_count"] == len(result["text"])


def test_extract_docx_paragraphs_and_tables():
    result = FileExtractor().extract(make_docx_bytes(), "essay.docx")

    assert result["success"] is True
    assert result["file_type"] == "DOCX"
    assert "Introduction paragraph" in result["text"]
    assert "Term" in result["text"]
    assert "Definition" in result["text"]
    assert result["word_count"] >= 4


def test_extract_uses_filename_basename_only():
    result = FileExtractor().extract(
        b"Short note.",
        "C:\\Users\\writer\\..\\notes.txt",
    )

    assert result["filename"] == "notes.txt"
    assert result["text"] == "Short note."


def test_reject_corrupt_pdf():
    with pytest.raises(InvalidFileError, match="invalid or corrupted"):
        FileExtractor().extract(b"%PDF-1.4\nthis is not a real pdf", "bad.pdf")


def test_reject_corrupt_docx():
    buffer = BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("hello.txt", "this is not a word document")

    with pytest.raises(InvalidFileError, match="invalid or corrupted"):
        FileExtractor().extract(buffer.getvalue(), "bad.docx")


def test_reject_extension_that_does_not_match_content():
    with pytest.raises(InvalidFileError, match="does not match"):
        FileExtractor().extract(b"This is plain text.", "report.pdf")


def test_reject_empty_file():
    with pytest.raises(EmptyFileError, match="empty"):
        FileExtractor().extract(b"", "empty.txt")


def test_reject_whitespace_only_file():
    with pytest.raises(EmptyFileError, match="extractable text"):
        FileExtractor().extract(b"  \n\t  ", "blank.txt")


def test_reject_unsupported_extension():
    with pytest.raises(UnsupportedFileTypeError, match="Unsupported"):
        FileExtractor().extract(b"hello", "program.exe")


def test_reject_missing_filename():
    class FakeUpload:
        filename = "   "

        def read(self):
            return b"hello"

    with pytest.raises(MissingFilenameError, match="filename"):
        FileExtractor().extract_upload(FakeUpload())


def test_reject_oversized_file():
    extractor = FileExtractor(max_bytes=8)

    with pytest.raises(FileTooLargeError, match="too large"):
        extractor.extract(b"hello world", "note.txt")


def test_accepts_file_at_exact_size_limit():
    data = b"hello world"
    result = FileExtractor(max_bytes=len(data)).extract(data, "note.txt")

    assert result["text"] == "hello world"
