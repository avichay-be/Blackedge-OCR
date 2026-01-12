"""
Base Workflow Handler.

This module defines the abstract base class for all workflow handlers.
Each handler implements a specific extraction strategy (e.g., Mistral, Azure DI, Gemini).
"""

from abc import ABC, abstractmethod
from typing import Optional
import logging

from src.models.workflow_models import WorkflowResult
from src.workflows.workflow_types import WorkflowType

logger = logging.getLogger(__name__)


class BaseWorkflowHandler(ABC):
    """Abstract base class for workflow handlers.

    All workflow handlers must implement the execute() method which processes
    a PDF document according to a specific extraction strategy.

    Attributes:
        workflow_type: The type of workflow this handler implements
    """

    def __init__(self, workflow_type: WorkflowType):
        """Initialize handler with workflow type.

        Args:
            workflow_type: The type of workflow this handler implements
        """
        self.workflow_type = workflow_type
        logger.info(f"Initialized {self.__class__.__name__} for {workflow_type.value}")

    @abstractmethod
    async def execute(
        self,
        pdf_path: str,
        query: str,
        enable_validation: Optional[bool] = None,
    ) -> WorkflowResult:
        """Execute the workflow to extract content from a PDF.

        This is the main method that must be implemented by all concrete handlers.
        It should:
        1. Read/process the PDF file
        2. Extract content using the appropriate AI provider(s)
        3. Optionally validate the extracted content
        4. Return a WorkflowResult with the extracted content and metadata

        Args:
            pdf_path: Path to the PDF file to process
            query: User query providing context for extraction
            enable_validation: Whether to enable validation (overrides global setting)

        Returns:
            WorkflowResult containing:
                - content: The extracted text content
                - metadata: Information about the extraction process
                - sections: Optional list of page-by-page sections
                - validation_report: Optional validation results

        Raises:
            ExtractionError: If extraction fails
            APIClientError: If API calls fail
            FileNotFoundError: If PDF file doesn't exist
        """
        pass

    def _log_start(self, pdf_path: str, query: str) -> None:
        """Log workflow start.

        Args:
            pdf_path: Path to PDF being processed
            query: User query
        """
        logger.info(
            f"Starting {self.workflow_type.value} workflow | "
            f"PDF: {pdf_path} | Query: {query[:100]}..."
        )

    def _log_complete(
        self, content_length: int, metadata: dict, execution_time: float
    ) -> None:
        """Log workflow completion.

        Args:
            content_length: Length of extracted content
            metadata: Workflow metadata
            execution_time: Total execution time in seconds
        """
        logger.info(
            f"Completed {self.workflow_type.value} workflow | "
            f"Content length: {content_length} chars | "
            f"Time: {execution_time:.2f}s | "
            f"Metadata: {metadata}"
        )

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if exc_type:
            logger.error(
                f"Error in {self.workflow_type.value} workflow: {exc_val}",
                exc_info=(exc_type, exc_val, exc_tb),
            )
