"""
Vocabulary analysis using NLTK and Python.
"""

import re
from collections import Counter

from nltk.tokenize import word_tokenize


class VocabularyAnalyzer:
    """Analyze vocabulary diversity and word repetition."""

    STOP_WORDS = {
        "the", "a", "an", "is", "am", "are", "was", "were",
        "be", "been", "being", "to", "of", "and", "or", "in",
        "on", "at", "for", "with", "by", "from", "as", "it",
        "this", "that", "these", "those", "i", "you", "he",
        "she", "we", "they", "my", "your", "his", "her",
        "our", "their", "me", "him", "them", "do", "does",
        "did", "has", "have", "had", "can", "could", "will",
        "would", "should", "not", "but", "if", "so", "than",
        "then", "there", "here", "when", "where", "what",
        "who", "which", "while", "because", "about", "into",
        "up", "down", "out", "all", "some", "any", "no"
    }

    def analyze(self, text):
        """Analyze vocabulary in the provided text."""

        if not isinstance(text, str):
            raise TypeError("Text must be a string.")

        text = text.strip()

        if not text:
            return {
                "vocabulary": {},
                "message": "No text provided for vocabulary analysis."
            }

        # Tokenize text into words
        tokens = word_tokenize(text.lower())

        # Keep only alphabetic words
        words = [
            word for word in tokens
            if re.fullmatch(r"[a-z]+", word)
        ]

        if not words:
            return {
                "vocabulary": {},
                "message": "No words found for vocabulary analysis."
            }

        total_words = len(words)
        unique_words = set(words)
        unique_word_count = len(unique_words)

        # Type-Token Ratio
        ttr = unique_word_count / total_words

        # Word frequency
        frequency = Counter(words)

        # Repeated words excluding common words
        meaningful_words = [
            word for word in words
            if word not in self.STOP_WORDS
        ]

        meaningful_frequency = Counter(meaningful_words)

        repeated_words = {
            word: count
            for word, count in meaningful_frequency.items()
            if count > 1
        }

        # Most frequently used meaningful words
        most_common_words = meaningful_frequency.most_common(5)

        # Long words (7 or more letters)
        long_words = sorted({
            word for word in words
            if len(word) >= 7
        })

        # Vocabulary score
        vocabulary_score = min(round(ttr * 100, 2), 100)

        return {
            "vocabulary": {
                "total_words": total_words,
                "unique_words": unique_word_count,
                "type_token_ratio": round(ttr, 3),
                "vocabulary_score": vocabulary_score,
                "repeated_words": repeated_words,
                "most_common_words": [
                    {
                        "word": word,
                        "count": count
                    }
                    for word, count in most_common_words
                ],
                "long_words": long_words,
                "long_word_count": len(long_words)
            },
            "message": "Vocabulary analysis completed successfully."
        }