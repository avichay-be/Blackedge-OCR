"""
Similarity Calculator.

This module provides methods to calculate similarity between two text extractions.
Supports multiple similarity methods optimized for different content types.
"""

import re
from typing import List, Dict, Tuple
from collections import Counter
import logging

from src.services.validation.content_normalizer import ContentNormalizer

logger = logging.getLogger(__name__)


class SimilarityCalculator:
    """Calculate similarity scores between two text documents.

    Provides multiple similarity calculation methods:
    - number_frequency: Compares numerical content (best for tables/data)
    - word_overlap: Compares word overlap (best for text documents)
    - cosine: Cosine similarity of word vectors
    - levenshtein: Character-level edit distance (expensive)
    """

    def __init__(self):
        """Initialize similarity calculator."""
        self.normalizer = ContentNormalizer()
        logger.info("Initialized SimilarityCalculator")

    def calculate_similarity(
        self, text1: str, text2: str, method: str = "number_frequency"
    ) -> float:
        """Calculate similarity score between two texts.

        Args:
            text1: First text document
            text2: Second text document
            method: Similarity method to use:
                - "number_frequency": Compare number distributions (default)
                - "word_overlap": Compare word overlap
                - "cosine": Cosine similarity of word frequencies
                - "levenshtein": Character-level edit distance

        Returns:
            Similarity score between 0.0 (completely different) and 1.0 (identical)

        Raises:
            ValueError: If method is not recognized
        """
        method = method.lower()

        if method == "number_frequency":
            return self._number_frequency_similarity(text1, text2)
        elif method == "word_overlap":
            return self._word_overlap_similarity(text1, text2)
        elif method == "cosine":
            return self._cosine_similarity(text1, text2)
        elif method == "levenshtein":
            return self._levenshtein_similarity(text1, text2)
        else:
            raise ValueError(
                f"Unknown similarity method: {method}. "
                f"Valid options: number_frequency, word_overlap, cosine, levenshtein"
            )

    def _number_frequency_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on number frequency distribution.

        This method is optimized for documents with numerical data (tables, reports).
        It compares the frequency distribution of numbers using cosine similarity.

        Args:
            text1: First text document
            text2: Second text document

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Extract numbers from both texts
        numbers1 = self.normalizer.extract_numbers(text1)
        numbers2 = self.normalizer.extract_numbers(text2)

        # Handle edge cases
        if not numbers1 and not numbers2:
            logger.debug("Both texts have no numbers, returning 1.0")
            return 1.0  # Both empty

        if not numbers1 or not numbers2:
            logger.debug("One text has no numbers, returning 0.0")
            return 0.0  # One empty

        # Calculate frequency distributions
        freq1 = Counter(numbers1)
        freq2 = Counter(numbers2)

        # Calculate cosine similarity
        similarity = self._cosine_similarity_from_counters(freq1, freq2)

        logger.debug(
            f"Number frequency similarity: {similarity:.3f} "
            f"({len(numbers1)} vs {len(numbers2)} numbers)"
        )

        return similarity

    def _word_overlap_similarity(self, text1: str, text2: str) -> float:
        """Calculate similarity based on word overlap (Jaccard similarity).

        This method compares the set of unique words in each document.

        Args:
            text1: First text document
            text2: Second text document

        Returns:
            Similarity score between 0.0 and 1.0 (Jaccard index)
        """
        # Extract key terms from both texts
        terms1 = self.normalizer.extract_key_terms(text1)
        terms2 = self.normalizer.extract_key_terms(text2)

        # Handle edge cases
        if not terms1 and not terms2:
            return 1.0  # Both empty

        if not terms1 or not terms2:
            return 0.0  # One empty

        # Calculate Jaccard similarity
        intersection = len(terms1 & terms2)
        union = len(terms1 | terms2)

        similarity = intersection / union if union > 0 else 0.0

        logger.debug(
            f"Word overlap similarity: {similarity:.3f} "
            f"({len(terms1)} vs {len(terms2)} unique terms)"
        )

        return similarity

    def _cosine_similarity(self, text1: str, text2: str) -> float:
        """Calculate cosine similarity of word frequency vectors.

        This method represents each document as a vector of word frequencies
        and calculates the cosine of the angle between them.

        Args:
            text1: First text document
            text2: Second text document

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Get word frequencies
        freq1 = self.normalizer.calculate_word_frequency(text1)
        freq2 = self.normalizer.calculate_word_frequency(text2)

        # Handle edge cases
        if not freq1 and not freq2:
            return 1.0

        if not freq1 or not freq2:
            return 0.0

        # Calculate cosine similarity
        similarity = self._cosine_similarity_from_dicts(freq1, freq2)

        logger.debug(
            f"Cosine similarity: {similarity:.3f} "
            f"({len(freq1)} vs {len(freq2)} unique words)"
        )

        return similarity

    def _levenshtein_similarity(self, text1: str, text2: str) -> float:
        """Calculate normalized Levenshtein (edit distance) similarity.

        This method calculates character-level edit distance.
        WARNING: Expensive for long texts, use with caution.

        Args:
            text1: First text document
            text2: Second text document

        Returns:
            Similarity score between 0.0 and 1.0
        """
        # Normalize texts for comparison
        text1 = self.normalizer.normalize_for_comparison(text1)
        text2 = self.normalizer.normalize_for_comparison(text2)

        # Truncate very long texts (performance optimization)
        MAX_LENGTH = 10000
        if len(text1) > MAX_LENGTH:
            text1 = text1[:MAX_LENGTH]
            logger.warning(f"Text1 truncated to {MAX_LENGTH} characters")

        if len(text2) > MAX_LENGTH:
            text2 = text2[:MAX_LENGTH]
            logger.warning(f"Text2 truncated to {MAX_LENGTH} characters")

        # Handle edge cases
        if text1 == text2:
            return 1.0

        if not text1 or not text2:
            return 0.0

        # Calculate Levenshtein distance
        distance = self._levenshtein_distance(text1, text2)

        # Normalize to 0-1 range
        max_length = max(len(text1), len(text2))
        similarity = 1.0 - (distance / max_length)

        logger.debug(
            f"Levenshtein similarity: {similarity:.3f} "
            f"(distance: {distance}, max length: {max_length})"
        )

        return similarity

    def _cosine_similarity_from_counters(
        self, counter1: Counter, counter2: Counter
    ) -> float:
        """Calculate cosine similarity from two Counter objects.

        Args:
            counter1: First frequency counter
            counter2: Second frequency counter

        Returns:
            Cosine similarity score
        """
        # Get all unique keys
        all_keys = set(counter1.keys()) | set(counter2.keys())

        if not all_keys:
            return 0.0

        # Build vectors
        vec1 = [counter1.get(key, 0) for key in all_keys]
        vec2 = [counter2.get(key, 0) for key in all_keys]

        # Calculate dot product and magnitudes
        dot_product = sum(a * b for a, b in zip(vec1, vec2))
        magnitude1 = sum(a * a for a in vec1) ** 0.5
        magnitude2 = sum(b * b for b in vec2) ** 0.5

        # Calculate cosine similarity
        if magnitude1 * magnitude2 == 0:
            return 0.0

        return dot_product / (magnitude1 * magnitude2)

    def _cosine_similarity_from_dicts(
        self, dict1: Dict[str, int], dict2: Dict[str, int]
    ) -> float:
        """Calculate cosine similarity from two frequency dictionaries.

        Args:
            dict1: First frequency dictionary
            dict2: Second frequency dictionary

        Returns:
            Cosine similarity score
        """
        counter1 = Counter(dict1)
        counter2 = Counter(dict2)
        return self._cosine_similarity_from_counters(counter1, counter2)

    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate Levenshtein distance between two strings.

        Uses dynamic programming with space optimization.

        Args:
            s1: First string
            s2: Second string

        Returns:
            Edit distance
        """
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)

        if len(s2) == 0:
            return len(s1)

        # Use only two rows instead of full matrix (space optimization)
        previous_row = range(len(s2) + 1)

        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                # Cost of insertion, deletion, or substitution
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row

        return previous_row[-1]

    def calculate_similarity_report(self, text1: str, text2: str) -> Dict[str, float]:
        """Calculate similarity using all methods and return a report.

        Args:
            text1: First text document
            text2: Second text document

        Returns:
            Dictionary with similarity scores for all methods
        """
        report = {
            "number_frequency": self._number_frequency_similarity(text1, text2),
            "word_overlap": self._word_overlap_similarity(text1, text2),
            "cosine": self._cosine_similarity(text1, text2),
        }

        # Only calculate Levenshtein for short texts (expensive)
        if len(text1) < 5000 and len(text2) < 5000:
            report["levenshtein"] = self._levenshtein_similarity(text1, text2)
        else:
            report["levenshtein"] = None  # Skipped for performance

        logger.info(f"Similarity report: {report}")
        return report
