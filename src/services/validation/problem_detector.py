"""
Problem Detector.

This module provides detection of quality issues in extracted content.
Identifies potential problems such as low content density, missing data,
repeated characters, and other extraction anomalies.
"""

import re
import asyncio
from typing import List, Dict
import logging

from src.models.workflow_models import ExtractedSection

logger = logging.getLogger(__name__)


class ProblemDetector:
    """Detect quality problems in extracted content.

    This class analyzes extracted sections and identifies potential issues
    that may indicate poor extraction quality, requiring validation or re-extraction.
    """

    # Thresholds for problem detection
    MIN_CONTENT_LENGTH = 100  # Minimum characters per page
    MAX_REPEATED_CHAR_LENGTH = 10  # Maximum repeated characters
    MIN_WORD_COUNT = 20  # Minimum words per page
    MAX_GIBBERISH_RATIO = 0.3  # Maximum ratio of non-dictionary words

    def __init__(self):
        """Initialize problem detector."""
        logger.info("Initialized ProblemDetector")

    async def detect_problems_batch(
        self, sections: List[ExtractedSection]
    ) -> Dict[int, List[str]]:
        """Detect problems across multiple sections in parallel.

        Args:
            sections: List of extracted sections to analyze

        Returns:
            Dictionary mapping page numbers to lists of detected problems
            Only includes pages with detected problems

        Example:
            {
                1: ["low_content_density", "missing_numbers"],
                5: ["repeated_characters"]
            }
        """
        if not sections:
            return {}

        logger.info(f"Analyzing {len(sections)} sections for quality problems")

        # Process sections in parallel
        tasks = [self._detect_problems_for_section(section) for section in sections]
        results = await asyncio.gather(*tasks)

        # Build result dictionary (only include pages with problems)
        problems_by_page = {}
        for section, problems in zip(sections, results):
            if problems:
                problems_by_page[section.page_number] = problems

        logger.info(f"Found problems on {len(problems_by_page)} pages")
        return problems_by_page

    async def _detect_problems_for_section(
        self, section: ExtractedSection
    ) -> List[str]:
        """Detect problems in a single section.

        Args:
            section: Extracted section to analyze

        Returns:
            List of problem identifiers (empty if no problems)
        """
        problems = []
        content = section.content

        # Check 1: Empty or very short content
        if self._is_low_content_density(content):
            problems.append("low_content_density")

        # Check 2: Missing numbers in tabular data
        if self._has_missing_numbers(content):
            problems.append("missing_numbers")

        # Check 3: Repeated characters (extraction glitch)
        if self._has_repeated_characters(content):
            problems.append("repeated_characters")

        # Check 4: Very low word count
        if self._is_low_word_count(content):
            problems.append("low_word_count")

        # Check 5: High ratio of gibberish
        if self._has_high_gibberish(content):
            problems.append("high_gibberish")

        # Check 6: Suspicious special characters
        if self._has_suspicious_characters(content):
            problems.append("suspicious_characters")

        # Check 7: Incomplete table structures
        if self._has_incomplete_tables(content):
            problems.append("incomplete_tables")

        # Check 8: Excessive whitespace
        if self._has_excessive_whitespace(content):
            problems.append("excessive_whitespace")

        # Check 9: Encoding issues
        if self._has_encoding_issues(content):
            problems.append("encoding_issues")

        # Check 10: Missing punctuation (OCR error indicator)
        if self._has_missing_punctuation(content):
            problems.append("missing_punctuation")

        if problems:
            logger.debug(f"Page {section.page_number}: Detected problems: {problems}")

        return problems

    def _is_low_content_density(self, content: str) -> bool:
        """Check if content has very low density (too short).

        Args:
            content: Text content to check

        Returns:
            True if content is suspiciously short
        """
        clean_content = content.strip()
        return len(clean_content) < self.MIN_CONTENT_LENGTH

    def _has_missing_numbers(self, content: str) -> bool:
        """Check if content appears to be a table but lacks numbers.

        Args:
            content: Text content to check

        Returns:
            True if content has table markers but no numbers
        """
        # Check for table indicators
        has_table_markers = "|" in content or "TABLE" in content.upper()

        if not has_table_markers:
            return False

        # Check if numbers are present
        has_numbers = bool(re.search(r"\d", content))

        return not has_numbers

    def _has_repeated_characters(self, content: str) -> bool:
        """Check for excessively repeated characters (extraction glitch).

        Args:
            content: Text content to check

        Returns:
            True if excessive character repetition detected
        """
        # Pattern: same character repeated many times
        pattern = rf"(.)\1{{{self.MAX_REPEATED_CHAR_LENGTH},}}"
        return bool(re.search(pattern, content))

    def _is_low_word_count(self, content: str) -> bool:
        """Check if content has very few words.

        Args:
            content: Text content to check

        Returns:
            True if word count is suspiciously low
        """
        # Count words (sequences of alphanumeric characters)
        words = re.findall(r"\b\w+\b", content)
        return len(words) < self.MIN_WORD_COUNT

    def _has_high_gibberish(self, content: str) -> bool:
        """Check for high ratio of non-dictionary words (gibberish).

        Args:
            content: Text content to check

        Returns:
            True if gibberish ratio exceeds threshold
        """
        # Extract words
        words = re.findall(r"\b[a-zA-Z]{4,}\b", content)

        if len(words) < 10:
            # Not enough words to determine
            return False

        # Count words with unusual character patterns
        # (e.g., excessive consonants, no vowels)
        gibberish_count = 0
        for word in words:
            word_lower = word.lower()
            # Check for no vowels (except common abbreviations)
            if not re.search(r"[aeiou]", word_lower) and len(word) > 3:
                gibberish_count += 1
            # Check for excessive consonants in a row
            elif re.search(r"[bcdfghjklmnpqrstvwxyz]{5,}", word_lower):
                gibberish_count += 1

        gibberish_ratio = gibberish_count / len(words)
        return gibberish_ratio > self.MAX_GIBBERISH_RATIO

    def _has_suspicious_characters(self, content: str) -> bool:
        """Check for suspicious special characters (encoding issues).

        Args:
            content: Text content to check

        Returns:
            True if suspicious characters detected
        """
        # Look for common encoding error patterns
        suspicious_patterns = [
            r"[^\x00-\x7F]{5,}",  # Long sequences of non-ASCII
            r"�{2,}",  # Replacement characters
            r"[\x00-\x08\x0B\x0C\x0E-\x1F]",  # Control characters
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, content):
                return True

        return False

    def _has_incomplete_tables(self, content: str) -> bool:
        """Check for tables with incomplete structure.

        Args:
            content: Text content to check

        Returns:
            True if incomplete table structures detected
        """
        # Look for table markers
        if "TABLE" not in content.upper() and "|" not in content:
            return False

        # Check for tables with inconsistent column counts
        lines = content.split("\n")
        table_lines = [line for line in lines if "|" in line]

        if len(table_lines) < 2:
            return False

        # Count pipes in each line
        pipe_counts = [line.count("|") for line in table_lines]

        # Check for inconsistency
        if len(set(pipe_counts)) > 2:  # Allow some variation
            return True

        return False

    def _has_excessive_whitespace(self, content: str) -> bool:
        """Check for excessive whitespace patterns.

        Args:
            content: Text content to check

        Returns:
            True if excessive whitespace detected
        """
        # Check for very long runs of spaces
        if re.search(r" {20,}", content):
            return True

        # Check for excessive blank lines
        blank_line_count = content.count("\n\n\n")
        if blank_line_count > 5:
            return True

        return False

    def _has_encoding_issues(self, content: str) -> bool:
        """Check for encoding issues in content.

        Args:
            content: Text content to check

        Returns:
            True if encoding issues detected
        """
        # Common encoding error indicators
        encoding_errors = [
            "â€™",  # Smart quote encoding error
            "â€œ",  # Smart quote encoding error
            "â€",  # Smart quote encoding error
            "Ã©",  # Accented character error
            "Ã¨",  # Accented character error
        ]

        return any(error in content for error in encoding_errors)

    def _has_missing_punctuation(self, content: str) -> bool:
        """Check for missing punctuation (OCR error indicator).

        Args:
            content: Text content to check

        Returns:
            True if punctuation is suspiciously absent
        """
        # Count words and punctuation marks
        words = re.findall(r"\b\w+\b", content)
        punctuation = re.findall(r"[.,!?;:]", content)

        if len(words) < 50:
            # Not enough content to determine
            return False

        # Expect at least one punctuation mark per 30 words
        expected_punctuation = len(words) / 30
        return len(punctuation) < expected_punctuation
