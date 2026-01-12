"""
Validation Service.

This module orchestrates the validation process for extracted content.
Coordinates problem detection, similarity checking, and secondary extraction.
"""

import logging
from typing import List, Optional
import time

from src.models.workflow_models import ValidationResult, ExtractedSection
from src.services.validation.problem_detector import ProblemDetector
from src.services.validation.similarity_calculator import SimilarityCalculator
from src.services.validation.content_normalizer import ContentNormalizer
from src.services.clients.base_client import BaseDocumentClient
from src.core.config import settings
from src.core.constants import CONTENT_SEPARATOR

logger = logging.getLogger(__name__)


class ValidationService:
    """Orchestrate validation process for extracted content.

    This service provides two-stage validation:
    1. Problem Detection: Identifies quality issues in primary extraction
    2. Similarity Checking: Compares primary and secondary extractions

    If problems are detected or similarity is low, uses secondary extraction.
    """

    def __init__(
        self,
        secondary_client: BaseDocumentClient,
        similarity_method: str = "number_frequency",
        similarity_threshold: float = 0.85,
    ):
        """Initialize validation service.

        Args:
            secondary_client: Client to use for secondary extraction (e.g., OpenAI)
            similarity_method: Method for similarity calculation
            similarity_threshold: Minimum similarity score to accept primary extraction
        """
        self.secondary_client = secondary_client
        self.similarity_method = similarity_method
        self.similarity_threshold = similarity_threshold

        # Initialize validation components
        self.problem_detector = ProblemDetector()
        self.similarity_calculator = SimilarityCalculator()
        self.normalizer = ContentNormalizer()

        logger.info(
            f"Initialized ValidationService with {secondary_client.__class__.__name__} "
            f"(similarity_method={similarity_method}, "
            f"threshold={similarity_threshold})"
        )

    async def validate(
        self,
        primary_content: str,
        pdf_path: str,
        query: str = "",
        sections: Optional[List[ExtractedSection]] = None,
    ) -> ValidationResult:
        """Validate extracted content quality.

        Validation process:
        1. Detect problems in primary extraction (if sections provided)
        2. If problems found → use secondary extraction
        3. If no problems → perform secondary extraction for comparison
        4. Calculate similarity between primary and secondary
        5. If similarity low → use secondary extraction
        6. Otherwise → use primary extraction

        Args:
            primary_content: Content from primary extraction
            pdf_path: Path to PDF file (for secondary extraction if needed)
            query: User query (for context in secondary extraction)
            sections: Optional page-by-page sections from primary extraction

        Returns:
            ValidationResult with validated content and report
        """
        start_time = time.time()
        logger.info(f"Starting validation for {pdf_path}")

        # Stage 1: Problem Detection
        problems_by_page = {}
        if sections:
            logger.info("Analyzing content for quality problems...")
            problems_by_page = await self.problem_detector.detect_problems_batch(
                sections
            )

            if problems_by_page:
                problem_count = len(problems_by_page)
                problem_types = set()
                for problems in problems_by_page.values():
                    problem_types.update(problems)

                logger.warning(
                    f"Quality problems detected on {problem_count} pages: "
                    f"{list(problem_types)}"
                )

                # Use secondary extraction due to problems
                logger.info("Using secondary extraction due to quality problems")
                secondary_content = await self._extract_with_secondary(pdf_path, query)

                validation_time = time.time() - start_time
                return ValidationResult(
                    content=secondary_content,
                    used_secondary=True,
                    report={
                        "problems_by_page": problems_by_page,
                        "problem_count": problem_count,
                        "problem_types": list(problem_types),
                        "reason": "quality_issues",
                        "validation_time_seconds": validation_time,
                    },
                )

        # Stage 2: Similarity Checking
        logger.info("No quality problems detected, performing similarity check...")

        # Perform secondary extraction for comparison
        secondary_content = await self._extract_with_secondary(pdf_path, query)

        # Calculate similarity
        similarity = self.similarity_calculator.calculate_similarity(
            primary_content, secondary_content, method=self.similarity_method
        )

        logger.info(
            f"Similarity score: {similarity:.3f} "
            f"(threshold: {self.similarity_threshold})"
        )

        validation_time = time.time() - start_time

        # Stage 3: Decision
        if similarity < self.similarity_threshold:
            logger.warning(
                f"Similarity ({similarity:.3f}) below threshold "
                f"({self.similarity_threshold}), using secondary extraction"
            )

            return ValidationResult(
                content=secondary_content,
                used_secondary=True,
                report={
                    "similarity": similarity,
                    "threshold": self.similarity_threshold,
                    "reason": "low_similarity",
                    "method": self.similarity_method,
                    "validation_time_seconds": validation_time,
                },
            )

        # Primary extraction is good
        logger.info(
            f"Validation passed, using primary extraction "
            f"(similarity: {similarity:.3f})"
        )

        return ValidationResult(
            content=primary_content,
            used_secondary=False,
            report={
                "similarity": similarity,
                "threshold": self.similarity_threshold,
                "method": self.similarity_method,
                "validation_time_seconds": validation_time,
            },
        )

    async def _extract_with_secondary(self, pdf_path: str, query: str) -> str:
        """Perform secondary extraction using the configured client.

        Args:
            pdf_path: Path to PDF file
            query: User query for context

        Returns:
            Extracted content as string
        """
        logger.info(
            f"Performing secondary extraction with {self.secondary_client.__class__.__name__}"
        )

        try:
            sections = await self.secondary_client.process_document(pdf_path, query)
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            logger.info(
                f"Secondary extraction complete: {len(content)} chars, "
                f"{len(sections)} pages"
            )

            return content

        except Exception as e:
            logger.error(f"Secondary extraction failed: {e}", exc_info=True)
            raise

    async def validate_with_detailed_report(
        self,
        primary_content: str,
        pdf_path: str,
        query: str = "",
        sections: Optional[List[ExtractedSection]] = None,
    ) -> ValidationResult:
        """Validate with comprehensive similarity report.

        Similar to validate() but includes detailed similarity metrics
        using all available methods.

        Args:
            primary_content: Content from primary extraction
            pdf_path: Path to PDF file
            query: User query
            sections: Optional sections from primary extraction

        Returns:
            ValidationResult with detailed similarity report
        """
        # Perform standard validation
        result = await self.validate(primary_content, pdf_path, query, sections)

        # If secondary extraction was performed, add detailed similarity report
        if result.used_secondary and "similarity" in result.report:
            logger.info("Generating detailed similarity report...")

            secondary_content = result.content

            # Calculate similarity using all methods
            similarity_report = self.similarity_calculator.calculate_similarity_report(
                primary_content, secondary_content
            )

            # Add to report
            result.report["detailed_similarity"] = similarity_report

        return result


# Singleton accessor (optional, for convenience)
_validation_service_instance: Optional[ValidationService] = None


def get_validation_service(
    secondary_client: Optional[BaseDocumentClient] = None,
) -> ValidationService:
    """Get validation service instance.

    Args:
        secondary_client: Client for secondary extraction (required on first call)

    Returns:
        ValidationService instance

    Raises:
        ValueError: If secondary_client not provided on first call
    """
    global _validation_service_instance

    if _validation_service_instance is None:
        if secondary_client is None:
            raise ValueError(
                "secondary_client must be provided on first call to get_validation_service"
            )

        # Use settings for configuration
        similarity_method = getattr(
            settings, "VALIDATION_SIMILARITY_METHOD", "number_frequency"
        )
        similarity_threshold = getattr(
            settings, "VALIDATION_SIMILARITY_THRESHOLD", 0.85
        )

        _validation_service_instance = ValidationService(
            secondary_client=secondary_client,
            similarity_method=similarity_method,
            similarity_threshold=similarity_threshold,
        )

    return _validation_service_instance
