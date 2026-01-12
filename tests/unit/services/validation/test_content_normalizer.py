"""
Unit tests for ContentNormalizer.

Tests text normalization and feature extraction.
"""

import pytest

from src.services.validation.content_normalizer import ContentNormalizer


class TestContentNormalizer:
    """Test cases for ContentNormalizer."""

    def test_normalize_text_basic(self):
        """Test basic text normalization."""
        text = "  Hello   World  "
        result = ContentNormalizer.normalize_text(text)
        assert result == "hello world"

    def test_normalize_text_line_breaks(self):
        """Test normalization of line breaks."""
        text = "Line1\n\n\nLine2\r\nLine3"
        result = ContentNormalizer.normalize_text(text)
        assert result == "line1 line2 line3"

    def test_normalize_text_preserve_case(self):
        """Test preserving case when requested."""
        text = "Hello World"
        result = ContentNormalizer.normalize_text(text, preserve_case=True)
        assert result == "Hello World"

    def test_normalize_text_empty(self):
        """Test normalization of empty string."""
        assert ContentNormalizer.normalize_text("") == ""
        assert ContentNormalizer.normalize_text(None) == ""

    def test_extract_numbers_integers(self):
        """Test extracting integer numbers."""
        text = "The scores are 85, 90, and 95"
        numbers = ContentNormalizer.extract_numbers(text)
        assert numbers == [85.0, 90.0, 95.0]

    def test_extract_numbers_decimals(self):
        """Test extracting decimal numbers."""
        text = "Price: $123.45 and $67.89"
        numbers = ContentNormalizer.extract_numbers(text)
        assert 123.45 in numbers
        assert 67.89 in numbers

    def test_extract_numbers_with_commas(self):
        """Test extracting numbers with comma separators."""
        text = "Total: 1,234,567.89"
        numbers = ContentNormalizer.extract_numbers(text)
        assert 1234567.89 in numbers

    def test_extract_numbers_negative(self):
        """Test extracting negative numbers."""
        text = "Temperature: -15 degrees"
        numbers = ContentNormalizer.extract_numbers(text)
        assert -15.0 in numbers

    def test_extract_numbers_percentages(self):
        """Test extracting percentages."""
        text = "Growth rate: 25%"
        numbers = ContentNormalizer.extract_numbers(text)
        assert 25.0 in numbers

    def test_extract_numbers_empty(self):
        """Test extracting from empty string."""
        assert ContentNormalizer.extract_numbers("") == []
        assert ContentNormalizer.extract_numbers(None) == []

    def test_extract_key_terms_basic(self):
        """Test extracting key terms."""
        text = "The quick brown fox jumps over the lazy dog"
        terms = ContentNormalizer.extract_key_terms(text)
        assert "quick" in terms
        assert "brown" in terms
        assert "fox" in terms
        assert "the" in terms  # 3 chars, meets min_length=3
        # Words shorter than 3 chars would be excluded

    def test_extract_key_terms_min_length(self):
        """Test key terms with custom minimum length."""
        text = "The quick brown fox"
        terms = ContentNormalizer.extract_key_terms(text, min_length=5)
        assert "quick" in terms
        assert "brown" in terms
        assert "fox" not in terms  # Too short (< 5 chars)

    def test_extract_key_terms_empty(self):
        """Test extracting from empty string."""
        assert ContentNormalizer.extract_key_terms("") == set()

    def test_calculate_word_frequency(self):
        """Test calculating word frequency."""
        text = "foo bar foo baz foo bar"
        freq = ContentNormalizer.calculate_word_frequency(text)
        assert freq["foo"] == 3
        assert freq["bar"] == 2
        assert freq["baz"] == 1

    def test_calculate_word_frequency_empty(self):
        """Test frequency calculation on empty string."""
        assert ContentNormalizer.calculate_word_frequency("") == {}

    def test_remove_page_breaks(self):
        """Test removing page break markers."""
        text = "Page 1 content---PAGE-BREAK---Page 2 content"
        result = ContentNormalizer.remove_page_breaks(text)
        assert "---PAGE-BREAK---" not in result
        assert "Page 1 content" in result
        assert "Page 2 content" in result

    def test_remove_page_breaks_variants(self):
        """Test removing different page break variants."""
        text = "A---PAGE-BREAK---B---PAGE BREAK---C[PAGE BREAK]D"
        result = ContentNormalizer.remove_page_breaks(text)
        assert "---PAGE-BREAK---" not in result
        assert "---PAGE BREAK---" not in result
        assert "[PAGE BREAK]" not in result

    def test_normalize_for_comparison(self):
        """Test full normalization for comparison."""
        text = "Hello, World!  ---PAGE-BREAK---  How are you?"
        result = ContentNormalizer.normalize_for_comparison(text)
        # Should be lowercase, no punctuation, no page breaks
        assert result == "hello world how are you"

    def test_normalize_for_comparison_removes_punctuation(self):
        """Test that comparison normalization removes punctuation."""
        text = "Price: $1,234.56 (discounted!)"
        result = ContentNormalizer.normalize_for_comparison(text)
        # Should keep numbers and alphanumeric, remove punctuation
        assert "!" not in result
        assert "$" not in result
        assert "(" not in result
        assert ")" not in result
