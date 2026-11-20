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


class AnalysisService:
    """Run all writing analysis components together."""

    def __init__(self):
        self.readability_analyzer = ReadabilityAnalyzer()
        self.vocabulary_analyzer = VocabularyAnalyzer()
        self.sentence_analyzer = SentenceComplexityAnalyzer()
        self.score_calculator = WritingScoreCalculator()

    def analyze(self, text):
        """Analyze text and return a complete report."""

        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        if not text.strip():
            return {
                "success": False,
                "message": "Please provide text to analyze."
            }

        # 1. Grammar analysis
        grammar_analyzer = GrammarAnalyzer()

        try:
            grammar_result = grammar_analyzer.analyze(text)
        finally:
            try:
                grammar_analyzer.close()
            except BaseException:
                pass

        # 2. Readability analysis
        readability_result = (
            self.readability_analyzer.analyze(text)
        )

        # 3. Vocabulary analysis
        vocabulary_result = (
            self.vocabulary_analyzer.analyze(text)
        )

        # 4. Sentence complexity analysis
        sentence_result = (
            self.sentence_analyzer.analyze(text)
        )

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
            sentence_complexity=sentence_metrics
        )

        # 6. Combine everything
        return {
            "success": True,
            "message": "Writing analysis completed successfully.",
            "grammar": grammar_result,
            "readability": readability_result,
            "vocabulary": vocabulary_result,
            "sentence_complexity": sentence_result,
            "score": score_result
        }