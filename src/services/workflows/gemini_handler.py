"""
Gemini Workflow Handler.

This handler uses Google Gemini for high-quality extraction.
Best for when extraction quality is the top priority.
"""

import time
import logging
from typing import Optional

from src.services.workflows.base_handler import BaseWorkflowHandler
from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import WorkflowResult
from src.services.client_factory import get_client_factory
from src.core.error_handling import ExtractionError, APIClientError
from src.core.config import settings
from src.core.constants import CONTENT_SEPARATOR

logger = logging.getLogger(__name__)


class GeminiHandler(BaseWorkflowHandler):
    """Handler for high-quality extraction using Google Gemini.

    This workflow uses Google's Gemini model for extraction,
    prioritizing quality over speed.

    Advantages:
        - High-quality extraction
        - Good understanding of context
        - Handles complex queries well
        - Alternative to Mistral/OpenAI

    Best for:
        - When quality is the top priority
        - Complex documents requiring deep understanding
        - When other providers are unavailable
        - Alternative model for validation
    """

    def __init__(self):
        """Initialize Gemini handler."""
        super().__init__(WorkflowType.GEMINI)

    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute Gemini extraction workflow.

        Args:
            pdf_path: Path to PDF file
            query: User query providing context for extraction
            enable_validation: Whether to enable validation (overrides global setting)

        Returns:
            WorkflowResult with extracted content and metadata

        Raises:
            ExtractionError: If extraction fails
            APIClientError: If Gemini API calls fail
        """
        start_time = time.time()
        self._log_start(pdf_path, query)

        # Determine if validation should be enabled
        should_validate = (
            enable_validation
            if enable_validation is not None
            else settings.ENABLE_CROSS_VALIDATION
        )

        try:
            # Get client from factory
            factory = get_client_factory()
            gemini_client = factory.gemini

            # Process document with Gemini
            logger.info("Processing document with Gemini client")
            sections = await gemini_client.process_document(
                pdf_path=pdf_path, query=query
            )

            # Combine sections
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            # Build metadata
            metadata = {
                "workflow": self.workflow_type.value,
                "provider": "gemini",
                "pages": len(sections),
                "processing_time_seconds": time.time() - start_time,
                "model": gemini_client.model,
                "validation_enabled": should_validate,
            }

            # Optional validation (Phase 5 - not implemented yet)
            validation_report = None
            if should_validate:
                logger.info("Validation requested but not implemented yet (Phase 5)")
                # TODO: Implement validation in Phase 5

            execution_time = time.time() - start_time
            self._log_complete(len(content), metadata, execution_time)

            return WorkflowResult(
                content=content,
                metadata=metadata,
                sections=sections,
                validation_report=validation_report,
            )

        except APIClientError as e:
            logger.error(f"Gemini API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Gemini workflow failed: {e}", exc_info=True)
            raise ExtractionError(f"Failed to process document with Gemini: {e}")
