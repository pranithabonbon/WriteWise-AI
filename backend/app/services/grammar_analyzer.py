"""
Grammar and spelling analysis using LanguageTool.
"""

import language_tool_python


class GrammarAnalyzer:
    """Analyze grammar, spelling, punctuation, and writing mistakes."""

    def __init__(self, language="en-US"):
        self.language = language
        self.tool = language_tool_python.LanguageTool(language)

    def analyze(self, text):
        """
        Analyze text and return detected errors.

        Args:
            text (str): Input text to analyze.

        Returns:
            dict: Error details and summary.
        """

        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        if not text.strip():
            return {
                "error_count": 0,
                "errors": [],
                "message": "No text provided for analysis."
            }

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
            """Safely close the LanguageTool server."""
            try:
                self.tool.close()
            except (Exception, KeyboardInterrupt):
                pass