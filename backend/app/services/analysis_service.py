"""
Central service that combines all writing analyzers.
"""

from app.services.grammar_analyzer import GrammarAnalyzer
from app.services.readability_analyzer import ReadabilityAnalyzer
from app.services.vocabulary_analyzer import VocabularyAnalyzer
from app.services.sentence_complexity_analyzer import (
    SentenceComplexityAnalyzer
)
from app.services.writing_score_calculator import (
    WritingScoreCalculator
)
from app.services.recommendation_service import build_recommendations
from app.utils.writing_contexts import WRITING_CONTEXTS


class AnalysisService:
    """Run all writing analysis components together."""

    def __init__(self):
        # Initialize analyzers once when AnalysisService is created
        self.grammar_analyzer = GrammarAnalyzer()
        self.readability_analyzer = ReadabilityAnalyzer()
        self.vocabulary_analyzer = VocabularyAnalyzer()
        self.sentence_analyzer = SentenceComplexityAnalyzer()
        self.score_calculator = WritingScoreCalculator()

    def analyze(self, text, context="General"):
        """Analyze text and return a complete report."""

        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        if not text.strip():
            return {
                "success": False,
                "message": "Please provide text to analyze."
            }

        if context not in WRITING_CONTEXTS:
            raise ValueError("Unsupported writing context.")

        # 1. Grammar analysis
        grammar_result = self.grammar_analyzer.analyze(text, context=context)

        # 2. Readability analysis
        readability_result = self.readability_analyzer.analyze(text)

        # 3. Vocabulary analysis
        vocabulary_result = self.vocabulary_analyzer.analyze(text)

        # 4. Sentence complexity analysis
        sentence_result = self.sentence_analyzer.analyze(text)

        # Extract the nested results
        readability_metrics = readability_result.get(
            "readability", {}
        )

        vocabulary_metrics = vocabulary_result.get(
            "vocabulary", {}
        )

        sentence_metrics = sentence_result.get(
            "sentence_complexity", {}
        )

        # 5. Calculate overall writing score
        score_result = self.score_calculator.calculate(
            grammar=grammar_result,
            readability=readability_metrics,
            vocabulary=vocabulary_metrics,
            sentence_complexity=sentence_metrics,
            context=context,
        )

        # 6. Combine everything
        result = {
            "success": True,
            "context": context,
            "message": "Writing analysis completed successfully.",
            "grammar": grammar_result,
            "readability": readability_result,
            "vocabulary": vocabulary_result,
            "sentence_complexity": sentence_result,
            "score": score_result
        }
        result["recommendations"] = build_recommendations(result)
        return result
