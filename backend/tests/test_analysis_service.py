from unittest.mock import Mock

from app.services.analysis_service import AnalysisService


def test_analysis_service_passes_context_to_grammar_analyzer():
    service = AnalysisService()
    service.grammar_analyzer = Mock(return_value=None)
    service.grammar_analyzer.analyze.return_value = {
        "available": True, "error_count": 0, "possible_error_count": 0,
    }
    service.readability_analyzer = Mock()
    service.readability_analyzer.analyze.return_value = {
        "readability": {"flesch_reading_ease": 80},
    }
    service.vocabulary_analyzer = Mock()
    service.vocabulary_analyzer.analyze.return_value = {
        "vocabulary": {"vocabulary_score": 80, "type_token_ratio": 0.5, "repetition_patterns": {}},
    }
    service.sentence_analyzer = Mock()
    service.sentence_analyzer.analyze.return_value = {
        "sentence_complexity": {
            "complexity_score": 20, "average_sentence_length": 10,
            "long_sentence_count": 0, "complex_sentence_percentage": 0,
        },
    }

    service.analyze("A sample sentence.", context="Academic")

    service.grammar_analyzer.analyze.assert_called_once_with(
        "A sample sentence.", context="Academic"
    )
