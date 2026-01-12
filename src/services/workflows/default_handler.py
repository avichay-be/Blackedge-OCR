"""
Default Workflow Handler.

This handler provides general-purpose extraction using Mistral AI via Azure OpenAI.
This is the default workflow when no specific workflow is requested.
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


class DefaultHandler(BaseWorkflowHandler):
    """Handler for general-purpose extraction using Mistral AI.

    This workflow uses the Mistral client (via Azure OpenAI) for text-based
    extraction with AI enhancement.

    Advantages:
        - Good balance of speed and quality
        - Cost-effective
        - Good for general documents
        - Handles most document types well

    Best for:
        - General text extraction
        - Mixed content documents
        - When no specific workflow is specified
    """

    def __init__(self):
        """Initialize default handler."""
        super().__init__(WorkflowType.MISTRAL)

    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute default Mistral extraction workflow.

        Args:
            pdf_path: Path to PDF file
            query: User query providing context for extraction
            enable_validation: Whether to enable validation (overrides global setting)

        Returns:
            WorkflowResult with extracted content and metadata

        Raises:
            ExtractionError: If extraction fails
            APIClientError: If Mistral API calls fail
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
            mistral_client = factory.mistral

            # Process document with Mistral
            logger.info("Processing document with Mistral client")
            sections = await mistral_client.process_document(
                pdf_path=pdf_path, query=query
            )

            # Combine sections
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            # Build metadata
            metadata = {
                "workflow": self.workflow_type.value,
                "provider": "mistral",
                "pages": len(sections),
                "processing_time_seconds": time.time() - start_time,
                "model": mistral_client.model,
                "validation_enabled": should_validate,
            }

            # Optional validation (Phase 5 - not implemented yet)
            validation_report = None
            if should_validate:
                logger.info("Validation requested but not implemented yet (Phase 5)")
                # TODO: Implement validation in Phase 5
                # from src.services.validation_service import ValidationService
                # validation_service = ValidationService(secondary_client=factory.openai)
                # validated = await validation_service.validate(content, pdf_path, query)
                # content = validated.content
                # validation_report = validated.report

            execution_time = time.time() - start_time
            self._log_complete(len(content), metadata, execution_time)

            return WorkflowResult(
                content=content,
                metadata=metadata,
                sections=sections,
                validation_report=validation_report,
            )

        except APIClientError as e:
            logger.error(f"Mistral API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Default workflow failed: {e}", exc_info=True)
            raise ExtractionError(f"Failed to process document with Mistral: {e}")
