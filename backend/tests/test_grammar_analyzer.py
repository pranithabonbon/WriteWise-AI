"""LanguageTool lifecycle tests; no Java process or download is started."""

from app.services.grammar_analyzer import GrammarAnalyzer
from app.services.writing_score_calculator import WritingScoreCalculator
from types import SimpleNamespace


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


def test_missing_explicit_cache_allows_language_tool_downloader(monkeypatch):
    reset_shared_tool(monkeypatch)
    monkeypatch.delenv("LTP_JAR_DIR_PATH", raising=False)
    instances = []

    class FakeTool:
        def __init__(self, language):
            instances.append(language)

        def check(self, _text):
            return []

    monkeypatch.setattr("app.services.grammar_analyzer.language_tool_python.LanguageTool", FakeTool)
    assert GrammarAnalyzer().analyze("A sentence.")["available"] is True
    assert instances == ["en-US"]


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


def test_spelling_names_and_technical_terms_are_review_items_not_definite_errors(monkeypatch):
    reset_shared_tool(monkeypatch)
    matches = [
        SimpleNamespace(message="Possible spelling mistake", ruleId="MORFOLOGIK_RULE_EN_US", category="Typos", ruleIssueType="misspelling", offset=0, errorLength=10, context="Kubernetes", replacements=["Kubernates"]),
        SimpleNamespace(message="Possible spelling mistake", ruleId="MORFOLOGIK_RULE_EN_US", category="Typos", ruleIssueType="misspelling", offset=11, errorLength=10, context="PostgreSQL", replacements=["Postgre SQL"]),
        SimpleNamespace(message="Possible spelling mistake", ruleId="MORFOLOGIK_RULE_EN_US", category="Typos", ruleIssueType="misspelling", offset=22, errorLength=3, context="teh", replacements=["the"]),
        SimpleNamespace(message="Verb agreement", ruleId="AGREEMENT", category="Grammar", ruleIssueType="grammar", offset=26, errorLength=2, context="is", replacements=["are"]),
        SimpleNamespace(message="Consider concise wording", ruleId="STYLE_RULE", category="Style", ruleIssueType="style", offset=0, errorLength=10, context="Kubernetes", replacements=[]),
    ]

    class FakeTool:
        def check(self, _text):
            return matches

    monkeypatch.setattr(GrammarAnalyzer, "_shared_tool", FakeTool())
    monkeypatch.setattr(GrammarAnalyzer, "_shared_language", "en-US")
    result = GrammarAnalyzer().analyze("Kubernetes PostgreSQL teh is", context="Professional")

    assert result["error_count"] == 1
    assert result["possible_error_count"] == 1
    assert result["style_suggestion_count"] == 1
    assert result["ignored_name_or_term_count"] == 2
    assert [item["classification"] for item in result["errors"]] == [
        "possible_error", "grammar_error", "style_suggestion"
    ]


def test_grammar_classification_is_context_independent(monkeypatch):
    reset_shared_tool(monkeypatch)
    match = SimpleNamespace(
        message="Verb agreement", ruleId="AGREEMENT", category="Grammar",
        ruleIssueType="grammar", offset=4, errorLength=2,
        context="She go", replacements=["goes"],
    )

    class FakeTool:
        def check(self, _text):
            return [match]

    monkeypatch.setattr(GrammarAnalyzer, "_shared_tool", FakeTool())
    monkeypatch.setattr(GrammarAnalyzer, "_shared_language", "en-US")
    analyzer = GrammarAnalyzer()
    general = analyzer.analyze("She go", context="General")
    academic = analyzer.analyze("She go", context="Academic")

    assert general["errors"] == academic["errors"]
    assert general["error_count"] == academic["error_count"] == 1


def test_professional_and_academic_scores_do_not_combine_readability_or_complexity():
    calculator = WritingScoreCalculator()
    inputs = {
        "grammar": {"available": True, "error_count": 1},
        "readability": {"flesch_reading_ease": 10},
        "vocabulary": {"vocabulary_score": 20},
        "sentence_complexity": {"complexity_score": 90},
    }
    for context in ("Professional", "Academic"):
        score = calculator.calculate(**inputs, context=context)
        assert score["writing_score"] is None
        assert score["grade"] == "Not scored"
        assert score["score_scope"] == "component_estimates_only"
