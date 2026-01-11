"""
Google Gemini client for document processing.

This module provides a client for Google's Gemini API for high-quality
document extraction as an alternative to Mistral.

Example:
    async with GeminiClient() as client:
        sections = await client.process_document(
            "document.pdf",
            "Extract all data"
        )
"""

import time
from typing import List, Dict, Any, Optional

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
from src.models.workflow_models import ExtractedSection

logger = get_logger(__name__)


class GeminiClient(BaseDocumentClient):
    """
    Google Gemini document processing client.

    Uses Google Gemini AI for high-quality document extraction.
    Provides alternative to Mistral with different strengths.

    Attributes:
        api_key (str): Google Gemini API key
        model (str): Gemini model to use
        api_base (str): API base URL
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gemini-pro",
        api_base: str = "https://generativelanguage.googleapis.com/v1beta",
        timeout: float = 120.0,
    ):
        """
        Initialize Gemini client.

        Args:
            api_key: Gemini API key (defaults to environment variable)
            model: Gemini model to use
            api_base: API base URL
            timeout: Request timeout in seconds
        """
        from src.core.config import settings

        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model
        self.api_base = api_base.rstrip("/")

        # Initialize base client (validates credentials)
        super().__init__(timeout=timeout, provider_name="gemini")

        # Rate limiter
        self.rate_limiter = get_provider_limiter().get("gemini")

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        if not self.api_key:
            raise ConfigurationError("Gemini API key (GEMINI_API_KEY) is required")

        logger.debug(
            "Gemini credentials validated",
            extra={"api_base": self.api_base, "model": self.model},
        )

    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """
        Extract content from a single page using Gemini.

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
                        url=f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}",
                        json={
                            "contents": [{"parts": [{"text": prompt}]}],
                            "generationConfig": {
                                "temperature": 0.1,
                                "maxOutputTokens": 4000,
                            },
                        },
                        headers={"Content-Type": "application/json"},
                    )

                    response.raise_for_status()
                    result = response.json()

                    # Extract content from Gemini response format
                    content = result["candidates"][0]["content"]["parts"][0]["text"]

                    extraction_time = time.time() - start_time
                    self._log_extraction_complete(
                        page_number, len(content), extraction_time
                    )

                    return ExtractedSection(
                        page_number=page_number,
                        content=content,
                        metadata={
                            "provider": "gemini",
                            "model": self.model,
                            "extraction_time": extraction_time,
                            "input_length": len(page_text),
                            "output_length": len(content),
                        },
                    )

                except Exception as e:
                    logger.error(
                        f"Gemini extraction failed for page {page_number}",
                        extra={"page_number": page_number, "error": str(e)},
                    )
                    raise APIClientError(
                        f"Gemini extraction failed for page {page_number}: {str(e)}"
                    )

    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """
        Process entire PDF document with Gemini.

        Note: Requires pdfplumber for text extraction.

        Args:
            pdf_path: Path to PDF file
            query: User query describing what to extract
            chunk_size: Pages to process per chunk

        Returns:
            List[ExtractedSection]: Extracted sections, one per page
        """
        import pdfplumber

        logger.info(
            f"Processing document with Gemini",
            extra={"pdf_path": pdf_path, "model": self.model},
        )

        try:
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
                        "provider": "gemini",
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
        Check Gemini API health.

        Returns:
            Dict with health status and latency
        """
        start_time = time.time()

        try:
            async with HTTPClient(timeout=10) as http_client:
                # Simple test request
                response = await http_client.post(
                    url=f"{self.api_base}/models/{self.model}:generateContent?key={self.api_key}",
                    json={
                        "contents": [{"parts": [{"text": "test"}]}],
                        "generationConfig": {"maxOutputTokens": 10},
                    },
                    headers={"Content-Type": "application/json"},
                )

                latency = (time.time() - start_time) * 1000  # ms

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "gemini",
                        "model": self.model,
                        "latency_ms": round(latency, 2),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "gemini",
                        "error": f"HTTP {response.status_code}",
                        "latency_ms": round(latency, 2),
                    }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "provider": "gemini",
                "error": str(e),
                "latency_ms": round(latency, 2),
            }

    def _build_prompt(self, query: str, page_text: str, page_number: int) -> str:
        """
        Build extraction prompt for Gemini.

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
