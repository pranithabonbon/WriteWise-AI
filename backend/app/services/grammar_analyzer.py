"""Grammar and spelling analysis using a persistent LanguageTool install."""

import logging
import os
import threading
from pathlib import Path

# language_tool_python 2.9.5 defaults to downloading the 6.8-SNAPSHOT build.
# Point it directly at the existing 6.9-SNAPSHOT cache so its updater cannot
# download another build on startup or on the first analysis request.
_cached_install = Path(
    os.environ.get(
        "WRITEWISE_LANGUAGETOOL_JAR_DIR",
        Path.home() / ".cache" / "language_tool_python" / "LanguageTool-6.9-SNAPSHOT",
    )
).expanduser()
os.environ.setdefault("LTP_PATH", str(_cached_install.parent))
os.environ.setdefault("LTP_JAR_DIR_PATH", str(_cached_install))

import language_tool_python

logger = logging.getLogger(__name__)


class GrammarAnalyzer:
    """Analyze grammar, spelling, punctuation, and writing mistakes."""

    _shared_tool = None
    _shared_language = None
    _initialization_lock = threading.Lock()
    _check_lock = threading.Lock()

    def __init__(self, language="en-US"):
        self.language = language
        # LanguageTool stays uninitialized until analyze() receives text.

    @classmethod
    def _get_tool(cls, language):
        """Initialize LanguageTool once, reusing it for later requests."""
        if cls._shared_tool is not None and cls._shared_language == language:
            return cls._shared_tool

        with cls._initialization_lock:
            if cls._shared_tool is not None and cls._shared_language == language:
                return cls._shared_tool

            jar_dir = Path(os.environ["LTP_JAR_DIR_PATH"])
            if not jar_dir.is_dir():
                raise FileNotFoundError(f"LanguageTool cache directory was not found: {jar_dir}")

            # LTP_JAR_DIR_PATH makes language_tool_python skip its downloader.
            tool = language_tool_python.LanguageTool(language)
            cls._shared_tool = tool
            cls._shared_language = language
            return tool

    @classmethod
    def _discard_tool(cls, tool):
        """Clear a failed server so the next request can retry initialization."""
        with cls._initialization_lock:
            if cls._shared_tool is tool:
                cls._shared_tool = None
                cls._shared_language = None
                try:
                    tool.close()
                except Exception:
                    logger.debug("Error closing failed LanguageTool instance", exc_info=True)

    def analyze(self, text):
        """Return grammar findings, or an unavailable result without failing analysis."""
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        if not text.strip():
            return {
                "available": True,
                "error_count": 0,
                "errors": [],
                "message": "No text provided for analysis.",
            }

        # Serializing checks keeps the embedded server safe for concurrent API
        # requests and prevents one failed request from closing another's tool.
        with self._check_lock:
            tool = None
            try:
                tool = self._get_tool(self.language)
                matches = tool.check(text)
            except Exception as error:
                if tool is not None:
                    self._discard_tool(tool)
                logger.warning("LanguageTool grammar check unavailable: %s", error)
                return {
                    "available": False,
                    "error_count": None,
                    "errors": [],
                    "message": (
                        "Grammar checking is unavailable right now. "
                        "Other writing analysis results are still available."
                    ),
                }

        errors = [
            {
                "message": match.message,
                "rule_id": match.ruleId,
                "category": match.category,
                "error_type": match.ruleIssueType,
                "offset": match.offset,
                "length": match.errorLength,
                "context": match.context,
                "suggestions": match.replacements[:5],
            }
            for match in matches
        ]
        return {
            "available": True,
            "error_count": len(errors),
            "errors": errors,
            "message": (
                "Grammar analysis completed successfully."
                if errors
                else "No grammar or spelling errors found."
            ),
        }

    def close(self):
        """Keep the shared LanguageTool process alive between analyses."""

    @classmethod
    def shutdown(cls):
        """Explicitly shut down LanguageTool when the application stops."""
        with cls._check_lock:
            with cls._initialization_lock:
                if cls._shared_tool is not None:
                    try:
                        cls._shared_tool.close()
                    except Exception:
                        logger.debug("Error closing LanguageTool", exc_info=True)
                    cls._shared_tool = None
                    cls._shared_language = None
