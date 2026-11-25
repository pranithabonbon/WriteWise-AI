"""
Calculate an overall writing quality score.
"""


class WritingScoreCalculator:
    """Calculate a weighted writing score out of 100."""

    def calculate(
        self,
        grammar,
        readability,
        vocabulary,
        sentence_complexity,
        context="General",
    ):
        # -----------------------------
        # 1. Grammar score (40%)
        # -----------------------------
        grammar_available = grammar.get("available", True) is not False
        error_count = grammar.get("error_count", 0) or 0

        # Do not treat an unavailable grammar service as a perfect score.
        grammar_score = (
            max(0, 100 - (error_count * 5)) if grammar_available else None
        )

        # -----------------------------
        # 2. Readability score (25%)
        # -----------------------------
        flesch_score = readability.get(
            "flesch_reading_ease", 0
        )

        # Flesch score is usually between 0 and 100
        readability_score = max(
            0,
            min(100, flesch_score)
        )

        # -----------------------------
        # 3. Vocabulary score (20%)
        # -----------------------------
        vocabulary_score = vocabulary.get(
            "vocabulary_score", 0
        )

        # -----------------------------
        # 4. Sentence structure score (15%)
        # -----------------------------
        complexity_score = sentence_complexity.get(
            "complexity_score", 0
        )

        # Lower complexity is generally easier to read.
        # This is a heuristic, not a strict quality rule.
        sentence_score = max(
            0,
            100 - complexity_score
        )

        # -----------------------------
        # Weighted total
        # -----------------------------
        weighted_components = [
            (grammar_score, 0.40),
            (readability_score, 0.25),
            (vocabulary_score, 0.20),
            (sentence_score, 0.15),
        ]
        available_components = [
            (score, weight) for score, weight in weighted_components
            if score is not None
        ]
        available_weight = sum(weight for _, weight in available_components)
        component_weights = {
            "grammar": 0.40,
            "readability": 0.25,
            "vocabulary": 0.20,
            "sentence_structure": 0.15,
        }
        component_values = {
            "grammar": grammar_score,
            "readability": readability_score,
            "vocabulary": vocabulary_score,
            "sentence_structure": sentence_score,
        }
        context_limited = context in ("Professional", "Academic")
        overall_score = (
            None if context_limited else (
                sum(score * weight for score, weight in available_components)
                / available_weight if available_weight else 0
            )
        )

        if overall_score is not None:
            overall_score = round(max(0, min(100, overall_score)), 2)

        # -----------------------------
        # Grade
        # -----------------------------
        if context_limited:
            grade = "Not scored"
        elif overall_score >= 90:
            grade = "Excellent"
        elif overall_score >= 80:
            grade = "Very Good"
        elif overall_score >= 70:
            grade = "Good"
        elif overall_score >= 60:
            grade = "Average"
        else:
            grade = "Needs Improvement"

        return {
            "writing_score": overall_score,
            "grade": grade,
            "component_scores": {
                "grammar": round(grammar_score, 2) if grammar_score is not None else None,
                "readability": round(
                    readability_score, 2
                ),
                "vocabulary": round(
                    vocabulary_score, 2
                ),
                "sentence_structure": round(
                    sentence_score, 2
                )
            },
            "weights": {
                "grammar": 40,
                "readability": 25,
                "vocabulary": 20,
                "sentence_structure": 15
            },
            "effective_weights": {
                name: round(component_weights[name] / available_weight * 100, 2)
                if value is not None and available_weight
                else 0
                for name, value in component_values.items()
            },
            "message": (
                "No combined score is shown for professional or academic writing. Readability, vocabulary, and sentence metrics are estimates and may reflect necessary terminology or sentence structure."
                if context_limited else (
                    "Writing score calculated without grammar analysis because grammar checking is unavailable."
                    if not grammar_available else "Automated writing estimate calculated successfully; use it as guidance, not a definitive judgment."
                )
            ),
            "score_scope": "component_estimates_only" if context_limited else "combined_estimate",
        }
