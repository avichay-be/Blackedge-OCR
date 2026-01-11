"""
OCR with Images Handler.

This handler combines Mistral for text extraction and OpenAI vision for image/chart OCR.
Best for documents with charts, diagrams, or scanned images.
"""

import time
import logging
from typing import Optional, List, Dict, Any
import pdfplumber
from pdf2image import convert_from_path
import io

from src.services.workflows.base_handler import BaseWorkflowHandler
from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import WorkflowResult, ExtractedSection
from src.services.client_factory import get_client_factory
from src.core.error_handling import ExtractionError, APIClientError
from src.core.config import settings
from src.core.constants import CONTENT_SEPARATOR

logger = logging.getLogger(__name__)


class OcrImagesHandler(BaseWorkflowHandler):
    """Handler for OCR extraction with image processing.

    This workflow combines:
    1. Mistral for text-based content
    2. OpenAI GPT-4o Vision for images, charts, and diagrams

    Best for documents with:
        - Scanned pages (OCR needed)
        - Charts and diagrams
        - Images with text
        - Mixed text and visual content
    """

    def __init__(self):
        """Initialize OCR handler."""
        super().__init__(WorkflowType.OCR_WITH_IMAGES)

    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute OCR with images workflow.

        This workflow:
        1. Converts PDF pages to images
        2. Uses OpenAI GPT-4o Vision API for OCR
        3. Optionally uses Mistral for text refinement
        4. Optionally validates results

        Args:
            pdf_path: Path to PDF file
            query: User query providing context for extraction
            enable_validation: Whether to enable validation (overrides global setting)

        Returns:
            WorkflowResult with extracted content and metadata

        Raises:
            ExtractionError: If extraction fails
            APIClientError: If API calls fail
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
            # Get clients from factory
            factory = get_client_factory()
            openai_client = factory.openai
            mistral_client = factory.mistral

            # Step 1: Convert PDF pages to images and process with OpenAI Vision
            logger.info("Converting PDF pages to images for OCR processing")
            sections = []

            # Note: This requires pdf2image which is not implemented yet
            # For now, we'll use the OpenAI client's extract_page_content method
            # which expects page_data with 'image' key

            # TODO: Implement PDF to image conversion
            # For now, we'll use a hybrid approach:
            # 1. Extract text with pdfplumber (for text portions)
            # 2. Use OpenAI vision for image-heavy pages

            logger.warning(
                "OCR with images workflow requires PDF to image conversion (Phase 3 follow-up)"
            )

            # For now, use Mistral as fallback with a note in metadata
            factory = get_client_factory()
            mistral_client = factory.mistral

            logger.info(
                "Processing with Mistral (OCR workflow - full vision support pending)"
            )
            sections = await mistral_client.process_document(
                pdf_path=pdf_path, query=query
            )

            # Combine sections
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            # Build metadata
            metadata = {
                "workflow": self.workflow_type.value,
                "provider": "mistral",  # Using Mistral as fallback
                "pages": len(sections),
                "processing_time_seconds": time.time() - start_time,
                "validation_enabled": should_validate,
                "note": "Full OCR with vision not yet implemented - using Mistral fallback",
            }

            # Optional validation (Phase 5)
            validation_report = None
            if should_validate:
                logger.info("Validation requested but not implemented yet (Phase 5)")

            execution_time = time.time() - start_time
            self._log_complete(len(content), metadata, execution_time)

            return WorkflowResult(
                content=content,
                metadata=metadata,
                sections=sections,
                validation_report=validation_report,
            )

        except APIClientError as e:
            logger.error(f"OCR workflow API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"OCR workflow failed: {e}", exc_info=True)
            raise ExtractionError(f"Failed to process document with OCR workflow: {e}")
