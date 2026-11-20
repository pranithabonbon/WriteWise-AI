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
        sentence_complexity
    ):
        # -----------------------------
        # 1. Grammar score (40%)
        # -----------------------------
        error_count = grammar.get("error_count", 0)

        # Deduct 5 points per detected error
        grammar_score = max(0, 100 - (error_count * 5))

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
        overall_score = (
            grammar_score * 0.40
            + readability_score * 0.25
            + vocabulary_score * 0.20
            + sentence_score * 0.15
        )

        overall_score = round(
            max(0, min(100, overall_score)), 2
        )

        # -----------------------------
        # Grade
        # -----------------------------
        if overall_score >= 90:
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
                "grammar": round(grammar_score, 2),
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
            "message": "Writing score calculated successfully."
        }