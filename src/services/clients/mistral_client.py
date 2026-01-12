"""
Mistral AI client for document processing.

This module provides a client for the Mistral AI API (via Azure OpenAI endpoint)
for extracting content from PDF documents.

Example:
    async with MistralClient() as client:
        sections = await client.process_document(
            "document.pdf",
            "Extract all financial data"
        )
"""

import time
from typing import List, Dict, Any, Optional
import pdfplumber

from src.services.clients.base_client import BaseDocumentClient
from src.core.http_client import HTTPClient
from src.core.retry import RetryableHTTPClient, RetryConfig
from src.core.rate_limiter import get_provider_limiter
from src.core.error_handling import (
    APIClientError,
    ConfigurationError,
    FileProcessingError,
)
from src.core.logging import get_logger
from src.core.constants import CONTENT_SEPARATOR
from src.models.workflow_models import ExtractedSection

logger = get_logger(__name__)


class MistralClient(BaseDocumentClient):
    """
    Mistral AI document processing client.

    Uses Mistral AI models via Azure OpenAI endpoint for document extraction.
    Provides high-quality general-purpose extraction capabilities.

    Attributes:
        api_key (str): Azure API key
        api_url (str): Mistral API endpoint URL
        model (str): Mistral model to use
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_url: Optional[str] = None,
        model: str = "mistral-large",
        timeout: float = 120.0,
    ):
        """
        Initialize Mistral client.

        Args:
            api_key: Azure API key (defaults to environment variable)
            api_url: Mistral API endpoint (defaults to environment variable)
            model: Mistral model to use
            timeout: Request timeout in seconds
        """
        from src.core.config import settings

        self.api_key = api_key or settings.AZURE_API_KEY
        self.api_url = api_url or settings.MISTRAL_API_URL
        self.model = model

        # Initialize base client (validates credentials)
        super().__init__(timeout=timeout, provider_name="mistral")

        # Rate limiter
        self.rate_limiter = get_provider_limiter().get("mistral")

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        if not self.api_key:
            raise ConfigurationError("Mistral API key (AZURE_API_KEY) is required")
        if not self.api_url:
            raise ConfigurationError("Mistral API URL (MISTRAL_API_URL) is required")

        logger.debug(
            "Mistral credentials validated",
            extra={"api_url": self.api_url, "model": self.model},
        )

    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """
        Extract content from a single page using Mistral AI.

        Args:
            page_data: Dictionary with "text" key containing page text
            query: User query describing what to extract
            page_number: Page number for tracking

        Returns:
            ExtractedSection: Extracted content with metadata
        """
        start_time = time.time()
        self._log_extraction_start(page_number)

        # Prepare prompt
        page_text = page_data.get("text", "")
        prompt = self._build_prompt(query, page_text, page_number)

        # Rate limit
        async with self.rate_limiter:
            # Make API request
            async with HTTPClient(timeout=self.timeout) as http_client:
                retry_client = RetryableHTTPClient(
                    http_client, config=RetryConfig(max_attempts=3, backoff_factor=2)
                )

                try:
                    response = await retry_client.post(
                        url=f"{self.api_url}/chat/completions",
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "temperature": 0.1,
                            "max_tokens": 4000,
                        },
                        headers={
                            "Content-Type": "application/json",
                            "api-key": self.api_key,
                        },
                    )

                    response.raise_for_status()
                    result = response.json()

                    # Extract content
                    content = result["choices"][0]["message"]["content"]

                    extraction_time = time.time() - start_time
                    self._log_extraction_complete(
                        page_number, len(content), extraction_time
                    )

                    return ExtractedSection(
                        page_number=page_number,
                        content=content,
                        metadata={
                            "provider": "mistral",
                            "model": self.model,
                            "extraction_time": extraction_time,
                            "input_length": len(page_text),
                            "output_length": len(content),
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Mistral extraction failed for page {page_number}",
                        extra={"page_number": page_number, "error": str(e)},
                    )
                    raise APIClientError(
                        f"Mistral extraction failed for page {page_number}: {str(e)}"
                    )

    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """
        Process entire PDF document with Mistral AI.

        Args:
            pdf_path: Path to PDF file
            query: User query describing what to extract
            chunk_size: Pages to process per chunk (for memory management)

        Returns:
            List[ExtractedSection]: Extracted sections, one per page
        """
        logger.info(
            f"Processing document with Mistral",
            extra={"pdf_path": pdf_path, "model": self.model},
        )

        try:
            # Extract text from PDF
            with pdfplumber.open(pdf_path) as pdf:
                total_pages = len(pdf.pages)
                logger.info(f"Document has {total_pages} pages")

                sections = []
                for page_num, page in enumerate(pdf.pages, start=1):
                    # Extract text
                    page_text = page.extract_text() or ""

                    # Process page
                    section = await self.extract_page_content(
                        page_data={"text": page_text, "number": page_num},
                        query=query,
                        page_number=page_num,
                    )

                    sections.append(section)

                logger.info(
                    f"Document processing complete",
                    extra={
                        "total_pages": total_pages,
                        "provider": "mistral",
                        "model": self.model,
                    },
                )

                return sections

        except FileNotFoundError:
            raise FileProcessingError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise FileProcessingError(f"Failed to process document: {str(e)}")

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Mistral API health.

        Returns:
            Dict with health status and latency
        """
        start_time = time.time()

        try:
            async with HTTPClient(timeout=10) as http_client:
                # Simple test request
                response = await http_client.post(
                    url=f"{self.api_url}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "api-key": self.api_key,
                    },
                )

                latency = (time.time() - start_time) * 1000  # ms

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "mistral",
                        "model": self.model,
                        "latency_ms": round(latency, 2),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "mistral",
                        "error": f"HTTP {response.status_code}",
                        "latency_ms": round(latency, 2),
                    }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "provider": "mistral",
                "error": str(e),
                "latency_ms": round(latency, 2),
            }

    def _build_prompt(self, query: str, page_text: str, page_number: int) -> str:
        """
        Build extraction prompt for Mistral.

        Args:
            query: User's extraction query
            page_text: Text from the page
            page_number: Page number

        Returns:
            str: Formatted prompt
        """
        return f"""You are a PDF content extraction assistant. Extract the requested information from the following page.

USER QUERY: {query}

PAGE {page_number} CONTENT:
{page_text}

Please extract the relevant information according to the query. Maintain the structure and formatting from the original document. If the query asks for specific data (like tables, lists, or numbers), preserve that structure in your response."""
