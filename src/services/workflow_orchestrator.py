"""
Workflow Orchestrator.

This module provides the central orchestration for workflow execution.
It routes queries to appropriate handlers and manages the extraction process.
"""

import logging
from typing import Optional

from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import WorkflowResult
from src.services.workflow_router import get_workflow_type
from src.services.workflows.base_handler import BaseWorkflowHandler
from src.services.workflows.text_extraction_handler import TextExtractionHandler
from src.services.workflows.default_handler import DefaultHandler
from src.services.workflows.azure_di_handler import AzureDIHandler
from src.services.workflows.ocr_images_handler import OcrImagesHandler
from src.services.workflows.gemini_handler import GeminiHandler
from src.core.error_handling import ExtractionError

logger = logging.getLogger(__name__)


class WorkflowOrchestrator:
    """Orchestrates workflow execution by routing to appropriate handlers.

    This class is responsible for:
    1. Determining which workflow to use (via router or explicit selection)
    2. Getting the appropriate handler instance
    3. Executing the workflow
    4. Returning the results

    The orchestrator follows the singleton pattern to ensure
    consistent handler instances across the application.
    """

    _instance: Optional["WorkflowOrchestrator"] = None

    def __new__(cls):
        """Singleton pattern implementation."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        """Initialize orchestrator with workflow handlers."""
        if self._initialized:
            return

        logger.info("Initializing WorkflowOrchestrator")

        # Initialize all workflow handlers
        self.workflow_handlers: dict[WorkflowType, BaseWorkflowHandler] = {
            WorkflowType.TEXT_EXTRACTION: TextExtractionHandler(),
            WorkflowType.MISTRAL: DefaultHandler(),
            WorkflowType.AZURE_DOCUMENT_INTELLIGENCE: AzureDIHandler(),
            WorkflowType.OCR_WITH_IMAGES: OcrImagesHandler(),
            WorkflowType.GEMINI: GeminiHandler(),
        }

        self._initialized = True
        logger.info(
            f"WorkflowOrchestrator initialized with {len(self.workflow_handlers)} handlers"
        )

    async def execute_workflow(
        self,
        pdf_path: str,
        query: str = "",
        enable_validation: Optional[bool] = None,
        explicit_workflow: Optional[str] = None,
    ) -> WorkflowResult:
        """Execute the appropriate workflow for a PDF document.

        This is the main entry point for document processing. It:
        1. Determines which workflow to use (via router or explicit selection)
        2. Gets the appropriate handler
        3. Executes the workflow
        4. Returns the results

        Args:
            pdf_path: Path to the PDF file to process
            query: User query providing context for extraction (optional)
            enable_validation: Whether to enable validation (overrides global setting)
            explicit_workflow: Explicit workflow name to use (overrides routing)

        Returns:
            WorkflowResult containing:
                - content: Extracted text content
                - metadata: Information about extraction process
                - sections: Optional page-by-page sections
                - validation_report: Optional validation results

        Raises:
            ExtractionError: If workflow execution fails
            ValueError: If explicit_workflow is invalid
            FileNotFoundError: If PDF file doesn't exist

        Examples:
            >>> orchestrator = get_workflow_orchestrator()
            >>> result = await orchestrator.execute_workflow(
            ...     pdf_path="/path/to/file.pdf",
            ...     query="extract all tables",
            ...     enable_validation=False
            ... )
            >>> print(result.content)
            >>> print(result.metadata["workflow"])
        """
        # Step 1: Determine workflow type
        workflow_type = get_workflow_type(query, explicit_workflow)

        # Step 2: Get handler
        handler = self.workflow_handlers.get(workflow_type)
        if not handler:
            raise ExtractionError(
                f"No handler found for workflow: {workflow_type.value}"
            )

        # Step 3: Execute workflow
        logger.info(
            f"Executing workflow: {workflow_type.value} | "
            f"PDF: {pdf_path} | "
            f"Validation: {enable_validation}"
        )

        try:
            result = await handler.execute(
                pdf_path=pdf_path,
                query=query,
                enable_validation=enable_validation,
            )

            logger.info(
                f"Workflow completed successfully: {workflow_type.value} | "
                f"Content length: {len(result.content)} chars | "
                f"Pages: {result.metadata.get('pages', 'N/A')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Workflow execution failed: {workflow_type.value} | Error: {e}",
                exc_info=True,
            )
            raise ExtractionError(
                f"Failed to execute {workflow_type.value} workflow: {e}"
            )

    def get_handler(self, workflow_type: WorkflowType) -> BaseWorkflowHandler:
        """Get a specific workflow handler.

        Args:
            workflow_type: The type of workflow handler to retrieve

        Returns:
            BaseWorkflowHandler instance

        Raises:
            ValueError: If workflow type is not found
        """
        handler = self.workflow_handlers.get(workflow_type)
        if not handler:
            raise ValueError(
                f"Unknown workflow type: {workflow_type.value}. "
                f"Available: {[wf.value for wf in self.workflow_handlers.keys()]}"
            )
        return handler

    def list_workflows(self) -> list[str]:
        """List all available workflow types.

        Returns:
            List of workflow type names
        """
        return [workflow_type.value for workflow_type in self.workflow_handlers.keys()]


# Singleton accessor function
_orchestrator_instance: Optional[WorkflowOrchestrator] = None


def get_workflow_orchestrator() -> WorkflowOrchestrator:
    """Get the singleton WorkflowOrchestrator instance.

    Returns:
        WorkflowOrchestrator instance

    Examples:
        >>> orchestrator = get_workflow_orchestrator()
        >>> result = await orchestrator.execute_workflow(
        ...     pdf_path="file.pdf",
        ...     query="extract tables"
        ... )
    """
    global _orchestrator_instance
    if _orchestrator_instance is None:
        _orchestrator_instance = WorkflowOrchestrator()
    return _orchestrator_instance
