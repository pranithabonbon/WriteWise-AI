"""LanguageTool lifecycle tests; no Java process or download is started."""

from app.services.grammar_analyzer import GrammarAnalyzer
from app.services.writing_score_calculator import WritingScoreCalculator


def reset_shared_tool(monkeypatch):
    monkeypatch.setattr(GrammarAnalyzer, "_shared_tool", None)
    monkeypatch.setattr(GrammarAnalyzer, "_shared_language", None)


def test_language_tool_is_lazy_and_reused(monkeypatch):
    reset_shared_tool(monkeypatch)
    instances = []

    class FakeTool:
        def __init__(self, language):
            self.language = language
            self.check_count = 0
            instances.append(self)

        def check(self, text):
            self.check_count += 1
            return []

    monkeypatch.setattr("app.services.grammar_analyzer.language_tool_python.LanguageTool", FakeTool)
    first = GrammarAnalyzer()
    second = GrammarAnalyzer()

    assert instances == []
    assert first.analyze(" ")["error_count"] == 0
    assert instances == []

    assert first.analyze("A sentence.")["available"] is True
    assert second.analyze("Another sentence.")["available"] is True
    assert len(instances) == 1
    assert instances[0].check_count == 2


def test_language_tool_initialization_failure_is_retried(monkeypatch):
    reset_shared_tool(monkeypatch)
    calls = []

    class FakeTool:
        def check(self, _text):
            return []

    def initialize(_language):
        calls.append(1)
        if len(calls) == 1:
            raise RuntimeError("Java did not start")
        return FakeTool()

    monkeypatch.setattr("app.services.grammar_analyzer.language_tool_python.LanguageTool", initialize)
    analyzer = GrammarAnalyzer()

    unavailable = analyzer.analyze("A sentence.")
    recovered = analyzer.analyze("A later sentence.")

    assert unavailable["available"] is False
    assert unavailable["error_count"] is None
    assert recovered["available"] is True
    assert len(calls) == 2


def test_unavailable_grammar_does_not_break_other_analysis_scores():
    score = WritingScoreCalculator().calculate(
        grammar={"available": False, "error_count": None},
        readability={"flesch_reading_ease": 80},
        vocabulary={"vocabulary_score": 70},
        sentence_complexity={"complexity_score": 40},
    )

    assert score["component_scores"]["grammar"] is None
    assert score["writing_score"] == 71.67
    assert "without grammar analysis" in score["message"]
