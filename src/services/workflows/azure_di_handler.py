"""
Azure Document Intelligence Handler.

This handler uses Azure Document Intelligence (formerly Form Recognizer) for
extraction. Best for complex tables, forms, and structured documents.
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


class AzureDIHandler(BaseWorkflowHandler):
    """Handler for Azure Document Intelligence extraction.

    This workflow uses Azure Document Intelligence for intelligent
    document analysis, with a focus on tables, forms, and layouts.

    Advantages:
        - Excellent table extraction
        - Great for forms and structured documents
        - Layout-aware extraction
        - Good OCR capabilities
        - Handles complex documents

    Best for:
        - Documents with many tables
        - Forms and invoices
        - Structured documents
        - When layout preservation is important
    """

    def __init__(self):
        """Initialize Azure DI handler."""
        super().__init__(WorkflowType.AZURE_DOCUMENT_INTELLIGENCE)

    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute Azure DI extraction workflow.

        Args:
            pdf_path: Path to PDF file
            query: User query providing context for extraction
            enable_validation: Whether to enable validation (overrides global setting)

        Returns:
            WorkflowResult with extracted content and metadata

        Raises:
            ExtractionError: If extraction fails
            APIClientError: If Azure DI API calls fail
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
            azure_client = factory.azure_di

            # Process document with Azure DI
            logger.info("Processing document with Azure Document Intelligence")
            sections = await azure_client.process_document(
                pdf_path=pdf_path, query=query
            )

            # Combine sections
            content = CONTENT_SEPARATOR.join([section.content for section in sections])

            # Extract table statistics from metadata
            total_tables = sum(
                section.metadata.get("table_count", 0) for section in sections
            )

            # Build metadata
            metadata = {
                "workflow": self.workflow_type.value,
                "provider": "azure_di",
                "pages": len(sections),
                "processing_time_seconds": time.time() - start_time,
                "total_tables": total_tables,
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
            logger.error(f"Azure DI API error: {e}", exc_info=True)
            raise
        except Exception as e:
            logger.error(f"Azure DI workflow failed: {e}", exc_info=True)
            raise ExtractionError(
                f"Failed to process document with Azure Document Intelligence: {e}"
            )
