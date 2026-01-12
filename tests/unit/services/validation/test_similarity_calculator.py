"""
Unit tests for SimilarityCalculator.

Tests similarity calculation methods.
"""

import pytest

from src.services.validation.similarity_calculator import SimilarityCalculator


class TestSimilarityCalculator:
    """Test cases for SimilarityCalculator."""

    def setup_method(self):
        """Set up test fixtures."""
        self.calculator = SimilarityCalculator()

    def test_number_frequency_similarity_identical(self):
        """Test number frequency similarity for identical texts."""
        text1 = "The values are 10, 20, 30"
        text2 = "The values are 10, 20, 30"
        similarity = self.calculator._number_frequency_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)

    def test_number_frequency_similarity_different(self):
        """Test number frequency similarity for different texts."""
        text1 = "The values are 10, 20, 30"
        text2 = "The values are 40, 50, 60"
        similarity = self.calculator._number_frequency_similarity(text1, text2)
        assert similarity == 0.0

    def test_number_frequency_similarity_partial(self):
        """Test number frequency similarity for partially overlapping texts."""
        text1 = "The values are 10, 20, 30"
        text2 = "The values are 10, 20, 40"
        similarity = self.calculator._number_frequency_similarity(text1, text2)
        assert 0.0 < similarity < 1.0

    def test_number_frequency_similarity_both_empty(self):
        """Test number frequency similarity when both texts have no numbers."""
        text1 = "No numbers here"
        text2 = "Also no numbers"
        similarity = self.calculator._number_frequency_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)  # Both empty

    def test_number_frequency_similarity_one_empty(self):
        """Test number frequency similarity when one text has no numbers."""
        text1 = "Values: 10, 20, 30"
        text2 = "No numbers here"
        similarity = self.calculator._number_frequency_similarity(text1, text2)
        assert similarity == 0.0

    def test_word_overlap_similarity_identical(self):
        """Test word overlap similarity for identical texts."""
        text1 = "The quick brown fox"
        text2 = "The quick brown fox"
        similarity = self.calculator._word_overlap_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)

    def test_word_overlap_similarity_no_overlap(self):
        """Test word overlap similarity for texts with no overlap."""
        text1 = "The quick brown fox"
        text2 = "A lazy sleeping dog"
        similarity = self.calculator._word_overlap_similarity(text1, text2)
        assert similarity == 0.0

    def test_word_overlap_similarity_partial(self):
        """Test word overlap similarity for partial overlap."""
        text1 = "The quick brown fox"
        text2 = "The lazy brown dog"
        similarity = self.calculator._word_overlap_similarity(text1, text2)
        # "the" and "brown" overlap
        assert 0.0 < similarity < 1.0

    def test_cosine_similarity_identical(self):
        """Test cosine similarity for identical texts."""
        text1 = "Hello world hello"
        text2 = "Hello world hello"
        similarity = self.calculator._cosine_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_no_overlap(self):
        """Test cosine similarity for texts with no overlap."""
        text1 = "Hello world"
        text2 = "Goodbye universe"
        similarity = self.calculator._cosine_similarity(text1, text2)
        assert similarity == 0.0

    def test_levenshtein_distance_identical(self):
        """Test Levenshtein distance for identical strings."""
        s1 = "hello"
        s2 = "hello"
        distance = self.calculator._levenshtein_distance(s1, s2)
        assert distance == 0

    def test_levenshtein_distance_one_edit(self):
        """Test Levenshtein distance with one character difference."""
        s1 = "hello"
        s2 = "hallo"
        distance = self.calculator._levenshtein_distance(s1, s2)
        assert distance == 1

    def test_levenshtein_distance_empty(self):
        """Test Levenshtein distance with empty string."""
        s1 = "hello"
        s2 = ""
        distance = self.calculator._levenshtein_distance(s1, s2)
        assert distance == 5

    def test_levenshtein_similarity_identical(self):
        """Test Levenshtein similarity for identical texts."""
        text1 = "hello world"
        text2 = "hello world"
        similarity = self.calculator._levenshtein_similarity(text1, text2)
        assert similarity == pytest.approx(1.0)

    def test_levenshtein_similarity_different(self):
        """Test Levenshtein similarity for very different texts."""
        text1 = "aaaa"
        text2 = "bbbb"
        similarity = self.calculator._levenshtein_similarity(text1, text2)
        assert similarity == 0.0

    def test_calculate_similarity_method_number_frequency(self):
        """Test calculate_similarity with number_frequency method."""
        text1 = "Values: 10, 20, 30"
        text2 = "Values: 10, 20, 30"
        similarity = self.calculator.calculate_similarity(
            text1, text2, method="number_frequency"
        )
        assert similarity == pytest.approx(1.0)

    def test_calculate_similarity_method_word_overlap(self):
        """Test calculate_similarity with word_overlap method."""
        text1 = "hello world"
        text2 = "hello world"
        similarity = self.calculator.calculate_similarity(
            text1, text2, method="word_overlap"
        )
        assert similarity == pytest.approx(1.0)

    def test_calculate_similarity_method_cosine(self):
        """Test calculate_similarity with cosine method."""
        text1 = "hello world"
        text2 = "hello world"
        similarity = self.calculator.calculate_similarity(text1, text2, method="cosine")
        assert similarity == pytest.approx(1.0)

    def test_calculate_similarity_method_levenshtein(self):
        """Test calculate_similarity with levenshtein method."""
        text1 = "hello"
        text2 = "hello"
        similarity = self.calculator.calculate_similarity(
            text1, text2, method="levenshtein"
        )
        assert similarity == pytest.approx(1.0)

    def test_calculate_similarity_invalid_method(self):
        """Test calculate_similarity with invalid method."""
        with pytest.raises(ValueError, match="Unknown similarity method"):
            self.calculator.calculate_similarity(
                "text1", "text2", method="invalid_method"
            )

    def test_calculate_similarity_report(self):
        """Test calculating similarity report with all methods."""
        text1 = "Values: 10, 20, 30. Hello world."
        text2 = "Values: 10, 20, 30. Hello world."
        report = self.calculator.calculate_similarity_report(text1, text2)

        assert "number_frequency" in report
        assert "word_overlap" in report
        assert "cosine" in report
        assert "levenshtein" in report

        # All should be 1.0 for identical texts
        assert report["number_frequency"] == pytest.approx(1.0)
        assert report["word_overlap"] == pytest.approx(1.0)
        assert report["cosine"] == pytest.approx(1.0)
        assert report["levenshtein"] == pytest.approx(1.0)

    def test_calculate_similarity_report_long_text(self):
        """Test similarity report skips Levenshtein for long texts."""
        text1 = "a" * 10000
        text2 = "b" * 10000
        report = self.calculator.calculate_similarity_report(text1, text2)

        assert report["levenshtein"] is None  # Skipped for performance

    def test_cosine_similarity_from_counters(self):
        """Test cosine similarity calculation from counters."""
        from collections import Counter

        counter1 = Counter({"a": 2, "b": 1})
        counter2 = Counter({"a": 2, "b": 1})
        similarity = self.calculator._cosine_similarity_from_counters(
            counter1, counter2
        )
        assert similarity == pytest.approx(1.0)

    def test_cosine_similarity_from_counters_no_overlap(self):
        """Test cosine similarity from counters with no overlap."""
        from collections import Counter

        counter1 = Counter({"a": 1, "b": 1})
        counter2 = Counter({"c": 1, "d": 1})
        similarity = self.calculator._cosine_similarity_from_counters(
            counter1, counter2
        )
        assert similarity == 0.0
