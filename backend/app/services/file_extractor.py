"""
Extract plain text from uploaded TXT, PDF, and DOCX files.

The filename extension is checked, then the file bytes are checked too.
A renamed or corrupted file is rejected even when the extension looks valid.
"""

import zipfile
from io import BytesIO

import pymupdf
from docx import Document
from docx.opc.exceptions import PackageNotFoundError


DEFAULT_MAX_BYTES = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    ".txt": "TXT",
    ".pdf": "PDF",
    ".docx": "DOCX",
}

# Tried in order. utf-8-sig also accepts plain UTF-8 and removes a BOM.
TEXT_ENCODINGS = ("utf-8-sig", "utf-8", "cp1252")


class FileExtractionError(Exception):
    """Base class for upload validation and text extraction errors."""

    status_code = 400


class MissingFileError(FileExtractionError):
    """Raised when the request does not include a file."""


class MissingFilenameError(FileExtractionError):
    """Raised when the uploaded file has no filename."""


class EmptyFileError(FileExtractionError):
    """Raised when a file is empty or has no extractable text."""


class FileTooLargeError(FileExtractionError):
    """Raised when a file is larger than the configured limit."""

    status_code = 413


class UnsupportedFileTypeError(FileExtractionError):
    """Raised when the file extension is not TXT, PDF, or DOCX."""

    status_code = 415


class InvalidFileError(FileExtractionError):
    """Raised when a file is corrupted or does not match its type."""


class FileExtractor:
    """Validate an uploaded file and return its text plus basic metadata."""

    def __init__(self, max_bytes=DEFAULT_MAX_BYTES):
        if not max_bytes or max_bytes <= 0:
            max_bytes = DEFAULT_MAX_BYTES
        self.max_bytes = max_bytes

    def extract_upload(self, uploaded_file):
        """
        Extract text from a Werkzeug FileStorage object.

        Args:
            uploaded_file: The file from request.files, or None.

        Returns:
            dict: Extraction result. See extract().
        """

        if uploaded_file is None:
            raise MissingFileError(
                "No file was uploaded. Send multipart/form-data "
                "with a file field named 'file'."
            )

        filename = getattr(uploaded_file, "filename", None)
        data = uploaded_file.read()
        if data is None:
            data = b""

        return self.extract(data, filename)

    def extract(self, data, filename):
        """
        Validate file bytes and extract plain text.

        Args:
            data (bytes): Raw file contents.
            filename (str): Original filename, used for the extension
                and for the metadata returned to the caller.

        Returns:
            dict: success, filename, file_type, text, character_count,
            and word_count.

        Raises:
            FileExtractionError: The file failed validation or extraction.
        """

        safe_name = self._clean_filename(filename)
        data = self._as_bytes(data)

        if len(data) == 0:
            raise EmptyFileError("The uploaded file is empty.")

        if len(data) > self.max_bytes:
            raise FileTooLargeError(self._too_large_message())

        extension = self._extension(safe_name)
        file_type = ALLOWED_EXTENSIONS.get(extension)
        if file_type is None:
            raise UnsupportedFileTypeError(
                "Unsupported file type. Upload a .txt, .pdf, or .docx file."
            )

        # Extension and contents must agree. This rejects renamed files
        # such as an executable saved with a .pdf name.
        self._validate_contents(data, extension)

        try:
            if extension == ".txt":
                text = self._extract_txt(data)
            elif extension == ".pdf":
                text = self._extract_pdf(data)
            else:
                text = self._extract_docx(data)
        except FileExtractionError:
            raise
        except Exception as exc:
            raise InvalidFileError(
                "The file is invalid or corrupted."
            ) from exc

        text = self._normalize_text(text)
        if not text:
            raise EmptyFileError(
                "The file does not contain any extractable text."
            )

        return {
            "success": True,
            "filename": safe_name,
            "file_type": file_type,
            "text": text,
            "character_count": len(text),
            "word_count": len(text.split()),
        }

    def _clean_filename(self, filename):
        if filename is None or not str(filename).strip():
            raise MissingFilenameError("A filename is required.")

        # Keep only the final path segment so a path cannot be stored.
        safe_name = str(filename).replace("\\", "/").split("/")[-1].strip()
        if not safe_name or safe_name in {".", ".."}:
            raise MissingFilenameError("A filename is required.")

        return safe_name

    def _as_bytes(self, data):
        if isinstance(data, str):
            return data.encode("utf-8")
        if isinstance(data, bytearray):
            return bytes(data)
        if not isinstance(data, bytes):
            raise InvalidFileError("The uploaded file could not be read.")
        return data

    def _extension(self, filename):
        if "." not in filename:
            return ""
        return "." + filename.lower().rsplit(".", 1)[1]

    def _too_large_message(self):
        if self.max_bytes % (1024 * 1024) == 0:
            size_mb = self.max_bytes // (1024 * 1024)
            return (
                f"File is too large. Maximum upload size is {size_mb} MB."
            )
        return "File is too large. Maximum upload size exceeded."

    def _validate_contents(self, data, extension):
        if extension == ".pdf":
            if not data.startswith(b"%PDF"):
                raise InvalidFileError(
                    "The file content does not match its extension."
                )
            return

        if extension == ".docx":
            if self._is_docx(data):
                return
            if data.startswith(b"PK"):
                raise InvalidFileError(
                    "The DOCX file is invalid or corrupted."
                )
            raise InvalidFileError(
                "The file content does not match its extension."
            )

        if (
            data.startswith(b"%PDF")
            or self._is_docx(data)
            or not self._is_text(data)
        ):
            raise InvalidFileError(
                "The file content does not match its extension."
            )

    def _is_docx(self, data):
        """True when the bytes are a Word document inside a zip package."""

        if not data.startswith(b"PK"):
            return False

        try:
            with zipfile.ZipFile(BytesIO(data)) as archive:
                names = set(archive.namelist())
        except zipfile.BadZipFile:
            return False

        return "word/document.xml" in names

    def _is_text(self, data):
        """True when the bytes decode as text rather than a binary format."""

        if b"\x00" in data and not self._has_utf16_bom(data):
            return False

        try:
            text = self._decode_text(data)
        except UnicodeDecodeError:
            return False

        if not text:
            return False

        printable = sum(
            1 for char in text
            if char in "\n\r\t" or char.isprintable()
        )
        return (printable / len(text)) >= 0.90

    def _has_utf16_bom(self, data):
        return data.startswith(b"\xff\xfe") or data.startswith(b"\xfe\xff")

    def _decode_text(self, data):
        if self._has_utf16_bom(data):
            return data.decode("utf-16")

        last_error = None
        for encoding in TEXT_ENCODINGS:
            try:
                return data.decode(encoding)
            except UnicodeDecodeError as exc:
                last_error = exc

        try:
            return data.decode("latin-1")
        except UnicodeDecodeError as exc:
            raise last_error or exc

    def _extract_txt(self, data):
        try:
            return self._decode_text(data)
        except UnicodeDecodeError as exc:
            raise InvalidFileError(
                "The text file encoding could not be read."
            ) from exc

    def _extract_pdf(self, data):
        try:
            document = pymupdf.open(stream=data, filetype="pdf")
        except Exception as exc:
            raise InvalidFileError(
                "The PDF file is invalid or corrupted."
            ) from exc

        try:
            if getattr(document, "needs_pass", False):
                raise InvalidFileError(
                    "The PDF is password protected and cannot be read."
                )

            pages = []
            for page in document:
                page_text = (page.get_text("text") or "").strip()
                if page_text:
                    pages.append(page_text)

            return "\n\n".join(pages)
        except FileExtractionError:
            raise
        except Exception as exc:
            raise InvalidFileError(
                "The PDF file is invalid or corrupted."
            ) from exc
        finally:
            document.close()

    def _extract_docx(self, data):
        try:
            document = Document(BytesIO(data))
        except (PackageNotFoundError, zipfile.BadZipFile, ValueError) as exc:
            raise InvalidFileError(
                "The DOCX file is invalid or corrupted."
            ) from exc

        parts = []

        for paragraph in document.paragraphs:
            paragraph_text = paragraph.text.strip()
            if paragraph_text:
                parts.append(paragraph_text)

        for table in document.tables:
            for row in table.rows:
                # Merged cells are repeated by python-docx. Keep each once.
                seen_cells = set()
                cell_values = []
                for cell in row.cells:
                    cell_id = id(cell._tc)
                    if cell_id in seen_cells:
                        continue
                    seen_cells.add(cell_id)

                    cell_text = cell.text.strip()
                    if cell_text:
                        cell_values.append(cell_text)

                if cell_values:
                    parts.append(" | ".join(cell_values))

        return "\n".join(parts)

    def _normalize_text(self, text):
        if not isinstance(text, str):
            text = "" if text is None else str(text)
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()
