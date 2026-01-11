"""
Base client interface for document processing.

This module defines the abstract base class that all AI provider clients
must implement, ensuring a consistent interface across different providers.

Example:
    class MyClient(BaseDocumentClient):
        def _validate_credentials(self):
            if not self.api_key:
                raise ConfigurationError("API key required")

        async def extract_page_content(self, page_data, query):
            # Implementation
            pass
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.core.logging import get_logger
from src.models.workflow_models import ExtractedSection

logger = get_logger(__name__)


class BaseDocumentClient(ABC):
    """
    Abstract base class for document processing clients.

    All AI provider clients (Mistral, OpenAI, Gemini, Azure DI) must inherit
    from this class and implement the required abstract methods.

    Attributes:
        timeout (float): Request timeout in seconds
        provider_name (str): Name of the provider (e.g., "mistral", "openai")

    Example:
        class MistralClient(BaseDocumentClient):
            def __init__(self, api_key: str):
                self.api_key = api_key
                super().__init__(timeout=120.0, provider_name="mistral")
    """

    def __init__(self, timeout: float = 120.0, provider_name: str = "unknown"):
        """
        Initialize base document client.

        Args:
            timeout: Request timeout in seconds
            provider_name: Name of the provider for logging

        Raises:
            ConfigurationError: If credentials validation fails
        """
        self.timeout = timeout
        self.provider_name = provider_name

        logger.info(
            f"{provider_name.title()} client initializing",
            extra={"provider": provider_name, "timeout": timeout},
        )

        # Validate credentials - must be implemented by subclass
        self._validate_credentials()

        logger.info(
            f"{provider_name.title()} client initialized successfully",
            extra={"provider": provider_name},
        )

    @abstractmethod
    def _validate_credentials(self):
        """
        Validate API credentials.

        Each client must implement this method to check that required
        credentials (API keys, endpoints, etc.) are present and valid.

        Raises:
            ConfigurationError: If credentials are missing or invalid
        """
        pass

    @abstractmethod
    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """
        Extract content from a single page.

        Args:
            page_data: Dictionary containing page information
                      (e.g., {"text": str, "image": bytes, "number": int})
            query: User query describing what to extract
            page_number: Page number for tracking

        Returns:
            ExtractedSection: Extracted content with metadata

        Raises:
            APIClientError: If extraction fails
        """
        pass

    @abstractmethod
    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """
        Process entire document and extract content.

        Args:
            pdf_path: Path to PDF file
            query: User query describing what to extract
            chunk_size: Number of pages to process in each chunk

        Returns:
            List[ExtractedSection]: List of extracted sections, one per page

        Raises:
            APIClientError: If processing fails
            FileProcessingError: If PDF cannot be read
        """
        pass

    @abstractmethod
    async def health_check(self) -> Dict[str, Any]:
        """
        Check if the client can connect to the API.

        Returns:
            Dict with health status:
                {
                    "status": "healthy" | "unhealthy",
                    "provider": str,
                    "latency_ms": float,
                    "error": str (if unhealthy)
                }
        """
        pass

    async def __aenter__(self):
        """
        Async context manager entry.

        Returns:
            BaseDocumentClient: The client instance
        """
        logger.debug(
            f"{self.provider_name.title()} client context entered",
            extra={"provider": self.provider_name},
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit with cleanup.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if exc_type:
            logger.error(
                f"{self.provider_name.title()} client error",
                extra={
                    "provider": self.provider_name,
                    "exception": exc_type.__name__,
                    "error": str(exc_val),
                },
            )

        logger.debug(
            f"{self.provider_name.title()} client context exited",
            extra={"provider": self.provider_name},
        )

    def _log_extraction_start(
        self, page_number: int, total_pages: Optional[int] = None
    ):
        """
        Log extraction start for tracking.

        Args:
            page_number: Current page number
            total_pages: Total number of pages (if known)
        """
        extra = {"provider": self.provider_name, "page_number": page_number}
        if total_pages:
            extra["total_pages"] = total_pages
            extra["progress_pct"] = round((page_number / total_pages) * 100, 1)

        logger.debug(f"Extracting page {page_number}", extra=extra)

    def _log_extraction_complete(
        self, page_number: int, content_length: int, extraction_time: float
    ):
        """
        Log extraction completion with metrics.

        Args:
            page_number: Page number that was extracted
            content_length: Length of extracted content
            extraction_time: Time taken in seconds
        """
        logger.debug(
            f"Page {page_number} extraction complete",
            extra={
                "provider": self.provider_name,
                "page_number": page_number,
                "content_length": content_length,
                "extraction_time_seconds": round(extraction_time, 2),
            },
        )
