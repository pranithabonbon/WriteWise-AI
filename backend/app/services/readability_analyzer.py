"""
Readability analysis using TextStat.
"""

import textstat


class ReadabilityAnalyzer:
    """Calculate readability and text complexity metrics."""

    def analyze(self, text):
        """
        Analyze readability of input text.

        Args:
            text (str): Text to analyze.

        Returns:
            dict: Readability metrics.
        """

        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        text = text.strip()

        if not text:
            return {
                "readability": {},
                "message": "No text provided for readability analysis."
            }

        word_count = textstat.lexicon_count(text)
        sentence_count = textstat.sentence_count(text)

        if word_count == 0 or sentence_count == 0:
            return {
                "readability": {},
                "message": "Not enough text to calculate readability."
            }

        flesch_reading_ease = textstat.flesch_reading_ease(text)
        flesch_kincaid_grade = textstat.flesch_kincaid_grade(text)
        automated_readability_index = textstat.automated_readability_index(text)
        coleman_liau_index = textstat.coleman_liau_index(text)
        average_sentence_length = word_count / sentence_count
        average_word_length = textstat.avg_letter_per_word(text)

        return {
            "readability": {
                "flesch_reading_ease": round(flesch_reading_ease, 2),
                "flesch_kincaid_grade": round(flesch_kincaid_grade, 2),
                "automated_readability_index": round(
                    automated_readability_index, 2
                ),
                "coleman_liau_index": round(coleman_liau_index, 2),
                "average_sentence_length": round(
                    average_sentence_length, 2
                ),
                "average_word_length": round(average_word_length, 2),
                "word_count": word_count,
                "sentence_count": sentence_count
            },
            "message": "Readability analysis completed successfully."
        }