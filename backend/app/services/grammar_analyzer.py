"""
Grammar and spelling analysis using LanguageTool.
"""

import threading
import language_tool_python


class GrammarAnalyzer:
    """Analyze grammar, spelling, punctuation, and writing mistakes."""

    # Shared LanguageTool instance across all analyzer objects
    _shared_tool = None
    _shared_language = None
    _initialization_lock = threading.Lock()

    def __init__(self, language="en-US"):
        self.language = language

        # Lazy initialization:
        # LanguageTool will NOT start when this object is created.
        # It starts only when actual text analysis is requested.
        self.tool = None

    @classmethod
    def _get_tool(cls, language):
        """Initialize LanguageTool only once and reuse it."""

        # Fast check: reuse existing instance
        if cls._shared_tool is not None:
            if cls._shared_language == language:
                return cls._shared_tool

        # Lock prevents multiple simultaneous initializations
        with cls._initialization_lock:

            # Check again after acquiring the lock
            if cls._shared_tool is not None:
                if cls._shared_language == language:
                    return cls._shared_tool

            # Initialize LanguageTool
            cls._shared_tool = language_tool_python.LanguageTool(language)
            cls._shared_language = language

            return cls._shared_tool

    def analyze(self, text):
        """
        Analyze text and return detected grammar errors.
        """

        # Validate input
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        # Handle empty text
        if not text.strip():
            return {
                "error_count": 0,
                "errors": [],
                "message": "No text provided for analysis."
            }

        # Lazy initialization
        # LanguageTool starts only when non-empty text is analyzed
        if self.tool is None:
            self.tool = self._get_tool(self.language)

        # Perform grammar analysis
        matches = self.tool.check(text)

        errors = []

        for match in matches:
            errors.append({
                "message": match.message,
                "rule_id": match.ruleId,
                "category": match.category,
                "error_type": match.ruleIssueType,
                "offset": match.offset,
                "length": match.errorLength,
                "context": match.context,
                "suggestions": match.replacements[:5]
            })

        # Return analysis results
        return {
            "error_count": len(errors),
            "errors": errors,
            "message": (
                "Grammar analysis completed successfully."
                if errors
                else "No grammar or spelling errors found."
            )
        }

    def close(self):
        """
        Do not close the shared LanguageTool instance after each request.

        The shared engine is reused for subsequent analysis requests.
        """
        pass

    @classmethod
    def shutdown(cls):
        """
        Explicitly shut down LanguageTool when the application stops.
        """

        with cls._initialization_lock:

            if cls._shared_tool is not None:
                try:
                    cls._shared_tool.close()
                except Exception:
                    pass

                cls._shared_tool = None
                cls._shared_language = None