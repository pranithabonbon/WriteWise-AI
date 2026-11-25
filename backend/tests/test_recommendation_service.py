from app.services.recommendation_service import build_recommendations


def result(context):
    return {
        "context": context,
        "grammar": {"available": True, "error_count": 0, "possible_error_count": 0},
        "readability": {"readability": {"flesch_reading_ease": 30}},
        "sentence_complexity": {"sentence_complexity": {
            "average_sentence_length": 35,
            "long_sentence_count": 3,
            "complex_sentence_percentage": 75,
        }},
        "vocabulary": {"vocabulary": {
            "type_token_ratio": 0.2,
            "repetition_patterns": {"authentication": {"count": 4, "sentences": [0, 1], "within_sentence": False}},
        }},
    }


def test_professional_technical_analysis_gets_contextual_guidance_without_simplification():
    recommendations = build_recommendations(result("Professional"))
    assert recommendations
    text = " ".join(item["text"] for item in recommendations).lower()
    assert "technical detail" in text or "technical and business terms" in text
    assert "simplif" not in text


def test_email_context_uses_qualified_readability_and_repetition_advice():
    recommendations = build_recommendations(result("Email"))
    headings = {item["heading"] for item in recommendations}
    assert {"Sentence length", "Repeated wording"} <= headings
    repeated = next(item["text"] for item in recommendations if item["heading"] == "Repeated wording")
    assert "in nearby sentences" in repeated
    assert "Repeating a key term can help" in repeated


def test_each_context_gets_relevant_distinct_recommendation_copy():
    results = {
        context: build_recommendations(result(context))
        for context in ("General", "Professional", "Academic", "Creative", "Email", "Casual")
    }
    for recommendations in results.values():
        assert {"Sentence length", "Sentence structure", "Repeated wording"} <= {
            item["heading"] for item in recommendations
        }
    copies = {
        context: tuple(item["text"] for item in recommendations)
        for context, recommendations in results.items()
    }
    assert len(set(copies.values())) == 6


def test_recommendations_do_not_suggest_formal_synonyms_or_simplifying_terms():
    recommendations = build_recommendations(result("Academic"))
    text = " ".join(item["text"] for item in recommendations).lower()
    assert "utilizing" not in text
    assert "simplify away meaningful distinctions" in text
    assert "replace 'using'" not in text
