"""
Sentence complexity analysis.
"""

import re


class SentenceComplexityAnalyzer:
    """Analyze sentence length and structural complexity."""

    COMPLEX_WORDS = {
        "because", "although", "though", "unless", "whereas",
        "while", "since", "which", "that", "who", "whom",
        "whose", "if", "when", "after", "before", "whenever",
        "wherever", "until"
    }

    def analyze(self, text):
        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        text = text.strip()

        if not text:
            return {
                "sentence_complexity": {},
                "message": "No text provided for analysis."
            }

        # Split text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)

        sentences = [
            sentence.strip()
            for sentence in sentences
            if sentence.strip()
        ]

        if not sentences:
            return {
                "sentence_complexity": {},
                "message": "No sentences found."
            }

        # Count words in each sentence
        sentence_lengths = []

        for sentence in sentences:
            words = re.findall(r"\b[a-zA-Z]+\b", sentence)
            sentence_lengths.append(len(words))

        total_sentences = len(sentences)
        total_words = sum(sentence_lengths)

        average_sentence_length = (
            total_words / total_sentences
        )

        long_sentences = [
            sentence
            for sentence, length in zip(
                sentences, sentence_lengths
            )
            if length > 20
        ]

        short_sentences = [
            sentence
            for sentence, length in zip(
                sentences, sentence_lengths
            )
            if length < 6
        ]

        # Detect complex sentence connectors
        complex_sentence_count = 0
        detected_complex_words = set()

        for sentence in sentences:
            words = set(
                re.findall(r"\b[a-zA-Z]+\b", sentence.lower())
            )

            found_words = words.intersection(
                self.COMPLEX_WORDS
            )

            if found_words:
                complex_sentence_count += 1
                detected_complex_words.update(found_words)

        long_sentence_percentage = (
            len(long_sentences) / total_sentences * 100
        )

        complex_sentence_percentage = (
            complex_sentence_count / total_sentences * 100
        )

        # Simple heuristic complexity score
        complexity_score = min(
            100,
            round(
                (average_sentence_length * 2)
                + (long_sentence_percentage * 0.5)
                + (complex_sentence_percentage * 0.3),
                2
            )
        )

        return {
            "sentence_complexity": {
                "sentence_count": total_sentences,
                "total_words": total_words,
                "average_sentence_length": round(
                    average_sentence_length, 2
                ),
                "long_sentence_count": len(long_sentences),
                "short_sentence_count": len(short_sentences),
                "long_sentence_percentage": round(
                    long_sentence_percentage, 2
                ),
                "complex_sentence_count": complex_sentence_count,
                "complex_sentence_percentage": round(
                    complex_sentence_percentage, 2
                ),
                "detected_complex_words": sorted(
                    detected_complex_words
                ),
                "complexity_score": complexity_score,
                "long_sentences": long_sentences,
                "short_sentences": short_sentences
            },
            "message": (
                "Sentence complexity analysis completed successfully."
            )
        }