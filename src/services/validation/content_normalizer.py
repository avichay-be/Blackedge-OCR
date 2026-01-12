"""
Content Normalizer.

This module provides text normalization utilities for comparison and validation.
Normalizes text to remove formatting differences and extracts comparable features.
"""

import re
from typing import List, Dict, Set
import logging

logger = logging.getLogger(__name__)


class ContentNormalizer:
    """Normalize text content for comparison and validation.

    This class provides methods to:
    - Normalize text (whitespace, case, punctuation)
    - Extract numbers for numerical comparison
    - Extract key terms and phrases
    - Clean and prepare text for similarity analysis
    """

    @staticmethod
    def normalize_text(text: str, preserve_case: bool = False) -> str:
        """Normalize text for comparison.

        Performs the following normalizations:
        - Converts to lowercase (unless preserve_case=True)
        - Collapses multiple whitespace into single spaces
        - Removes leading/trailing whitespace
        - Normalizes line breaks

        Args:
            text: Input text to normalize
            preserve_case: If True, preserves original case

        Returns:
            Normalized text string

        Examples:
            >>> ContentNormalizer.normalize_text("  Hello   World  ")
            'hello world'
            >>> ContentNormalizer.normalize_text("Line1\\n\\n\\nLine2")
            'line1 line2'
        """
        if not text:
            return ""

        # Convert to lowercase unless preserving case
        if not preserve_case:
            text = text.lower()

        # Normalize line breaks to spaces
        text = text.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")

        # Collapse multiple whitespace into single space
        text = re.sub(r"\s+", " ", text)

        # Remove leading/trailing whitespace
        text = text.strip()

        return text

    @staticmethod
    def extract_numbers(text: str) -> List[float]:
        """Extract all numbers from text.

        Supports:
        - Integers: 123
        - Decimals: 123.45
        - Negative numbers: -123.45
        - Comma-separated thousands: 1,234.56
        - Percentages: 25% (returns 25.0)

        Args:
            text: Input text to extract numbers from

        Returns:
            List of extracted numbers as floats

        Examples:
            >>> ContentNormalizer.extract_numbers("Price: $1,234.56")
            [1234.56]
            >>> ContentNormalizer.extract_numbers("Scores: 85, 90, 95")
            [85.0, 90.0, 95.0]
        """
        if not text:
            return []

        numbers = []

        # Pattern matches:
        # - Optional negative sign
        # - Digits with optional comma separators
        # - Optional decimal point and decimal digits
        # - Optional percentage sign
        pattern = r"-?\d+(?:,\d{3})*(?:\.\d+)?%?"

        matches = re.findall(pattern, text)

        for match in matches:
            try:
                # Remove commas and percentage sign
                clean_num = match.replace(",", "").rstrip("%")
                numbers.append(float(clean_num))
            except ValueError:
                # Skip invalid numbers
                logger.debug(f"Could not parse number: {match}")
                continue

        return numbers

    @staticmethod
    def extract_key_terms(text: str, min_length: int = 3) -> Set[str]:
        """Extract key terms (words) from text.

        Args:
            text: Input text
            min_length: Minimum word length to include

        Returns:
            Set of unique key terms (normalized, lowercase)

        Examples:
            >>> ContentNormalizer.extract_key_terms("The quick brown fox")
            {'quick', 'brown', 'fox'}
        """
        if not text:
            return set()

        # Normalize text
        text = ContentNormalizer.normalize_text(text)

        # Extract words (alphanumeric sequences)
        words = re.findall(r"\b[a-z0-9]+\b", text)

        # Filter by minimum length and convert to set
        return {word for word in words if len(word) >= min_length}

    @staticmethod
    def calculate_word_frequency(text: str) -> Dict[str, int]:
        """Calculate word frequency distribution.

        Args:
            text: Input text

        Returns:
            Dictionary mapping words to their occurrence counts

        Examples:
            >>> ContentNormalizer.calculate_word_frequency("foo bar foo baz foo")
            {'foo': 3, 'bar': 1, 'baz': 1}
        """
        if not text:
            return {}

        # Extract key terms
        terms = ContentNormalizer.extract_key_terms(text)

        # Normalize text for counting
        normalized = ContentNormalizer.normalize_text(text)

        # Count occurrences
        frequency = {}
        for term in terms:
            # Use word boundaries to avoid partial matches
            pattern = rf"\b{re.escape(term)}\b"
            count = len(re.findall(pattern, normalized))
            frequency[term] = count

        return frequency

    @staticmethod
    def remove_page_breaks(text: str) -> str:
        """Remove page break markers from text.

        Args:
            text: Input text with page breaks

        Returns:
            Text without page break markers
        """
        if not text:
            return ""

        # Remove common page break markers
        text = text.replace("---PAGE-BREAK---", " ")
        text = text.replace("---PAGE BREAK---", " ")
        text = text.replace("[PAGE BREAK]", " ")

        # Collapse whitespace
        text = re.sub(r"\s+", " ", text)

        return text.strip()

    @staticmethod
    def normalize_for_comparison(text: str) -> str:
        """Fully normalize text for similarity comparison.

        Applies all normalizations:
        - Lowercase conversion
        - Whitespace normalization
        - Page break removal
        - Punctuation removal

        Args:
            text: Input text

        Returns:
            Fully normalized text suitable for comparison
        """
        if not text:
            return ""

        # Remove page breaks
        text = ContentNormalizer.remove_page_breaks(text)

        # Normalize case and whitespace
        text = ContentNormalizer.normalize_text(text)

        # Remove punctuation (keep alphanumeric and spaces)
        text = re.sub(r"[^a-z0-9\s]", " ", text)

        # Final whitespace collapse
        text = re.sub(r"\s+", " ", text)

        return text.strip()
