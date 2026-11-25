"""Grammar and spelling analysis using a persistent LanguageTool install."""

import logging
import os
import threading
from pathlib import Path

# Reuse a known local cache when it exists. Clean hosts (including Render) can
# otherwise let language_tool_python download its pinned-by-package default
# into LTP_PATH; setting LTP_JAR_DIR_PATH to a nonexistent local path disables
# that downloader and makes grammar checking unavailable permanently.
_default_cache = Path.home() / ".cache" / "language_tool_python"
_cache_root = Path(os.environ.get("LTP_PATH", _default_cache)).expanduser()
_configured_install = os.environ.get("WRITEWISE_LANGUAGETOOL_JAR_DIR")
_preferred_install = Path(
    _configured_install or _cache_root / "LanguageTool-6.9-SNAPSHOT"
).expanduser()
if _configured_install:
    _cached_install = _preferred_install
elif _preferred_install.is_dir():
    _cached_install = _preferred_install
else:
    _cached_install = next(iter(sorted(
        (path for path in _cache_root.glob("LanguageTool-*") if path.is_dir()),
        reverse=True,
    )), None)
os.environ.setdefault("LTP_PATH", str(_cache_root))
if _cached_install is not None:
    os.environ.setdefault("LTP_JAR_DIR_PATH", str(_cached_install))

import language_tool_python

logger = logging.getLogger(__name__)
TECHNICAL_TERMS = {
    "anthropic", "api", "cuda", "docker", "flask", "gemini", "graphql",
    "http", "https", "javascript", "jwt", "kafka", "kubernetes",
    "languagetool", "mongodb", "nltk", "nginx", "oauth", "pymongo",
    "pymupdf", "postgresql", "python", "react", "redis", "rest", "sqlite",
    "textstat", "typescript", "vite", "writewise",
}


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

            jar_dir = os.environ.get("LTP_JAR_DIR_PATH")
            if jar_dir and not Path(jar_dir).is_dir():
                raise FileNotFoundError(f"LanguageTool cache directory was not found: {jar_dir}")
            # Without an explicit cache, language_tool_python downloads into
            # LTP_PATH. Production images warm that cache during the build.
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

    def analyze(self, text, context="General"):
        """Return grammar findings independent of context, or an unavailable result.

        LanguageTool's grammar and spelling classifications describe rule matches,
        not writing style. Context is accepted for a consistent analyzer interface;
        context-specific style guidance is produced by the recommendation service.
        """
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        if not text.strip():
            return {
                "available": True,
                "error_count": 0,
                "possible_error_count": 0,
                "style_suggestion_count": 0,
                "ignored_name_or_term_count": 0,
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
                    "possible_error_count": 0,
                    "style_suggestion_count": 0,
                    "ignored_name_or_term_count": 0,
                    "errors": [],
                    "message": (
                        "Grammar checking is unavailable right now. "
                        "Other writing analysis results are still available."
                    ),
                }

        errors = []
        ignored_name_or_term_count = 0
        for match in matches:
            issue_type = str(getattr(match, "ruleIssueType", "") or "").lower()
            raw_category = getattr(match, "category", "")
            category = getattr(raw_category, "name", raw_category)
            if issue_type == "style" or str(category).lower() == "style":
                classification = "style_suggestion"
            elif issue_type == "grammar":
                classification = "grammar_error"
            else:
                # Spelling, typography, and unknown rules need human review;
                # LanguageTool alone cannot reliably distinguish names/terms.
                classification = "possible_error"

            offset = int(getattr(match, "offset", 0) or 0)
            length = int(getattr(match, "errorLength", 0) or 0)
            excerpt = text[offset:offset + length]
            if (issue_type in ("misspelling", "typographical")
                    and self._likely_name_or_technical_term(text, offset, excerpt)):
                ignored_name_or_term_count += 1
                continue
            errors.append({
                "message": match.message,
                "rule_id": match.ruleId,
                "category": str(category),
                "error_type": issue_type,
                "classification": classification,
                "confidence": "review" if classification == "possible_error" else "rule-based",
                "offset": offset,
                "length": length,
                "context": match.context,
                "suggestions": match.replacements[:5],
                "matched_text": excerpt,
            })

        definite_count = sum(item["classification"] == "grammar_error" for item in errors)
        possible_count = sum(item["classification"] == "possible_error" for item in errors)
        style_count = sum(item["classification"] == "style_suggestion" for item in errors)
        return {
            "available": True,
            "error_count": definite_count,
            "possible_error_count": possible_count,
            "style_suggestion_count": style_count,
            "ignored_name_or_term_count": ignored_name_or_term_count,
            "errors": errors,
            "message": f"Grammar check found {definite_count} likely grammar error(s), {possible_count} item(s) to review, and {style_count} style suggestion(s).",
        }

    @staticmethod
    def _likely_name_or_technical_term(text, offset, excerpt):
        token = excerpt.strip(".,:;!?()[]{}\"'“”‘’")
        if not token:
            return False
        if token.lower() in TECHNICAL_TERMS:
            return True
        if any(character.isdigit() for character in token) or token.isupper() or ("-" in token and any(character.isupper() for character in token)):
            return True
        # A title-cased word mid-sentence is more likely a name than a typo.
        prefix = text[:offset].rstrip()
        begins_sentence = not prefix or prefix[-1] in ".!?\n"
        return bool(not begins_sentence and token[:1].isupper() and token[1:].islower())

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
