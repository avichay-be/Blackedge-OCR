"""
OpenAI client with vision API for document processing.

This module provides a client for OpenAI's GPT-4o with vision capabilities,
specialized for OCR and processing scanned documents, charts, and diagrams.

Example:
    async with OpenAIClient() as client:
        sections = await client.process_document(
            "scanned_document.pdf",
            "Extract all text using OCR"
        )
"""

import time
import base64
from typing import List, Dict, Any, Optional
from pathlib import Path

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


class OpenAIClient(BaseDocumentClient):
    """
    OpenAI GPT-4o with vision document processing client.

    Uses GPT-4o vision API for OCR and image-based extraction.
    Specialized for scanned documents, charts, diagrams, and low-quality text.

    Attributes:
        api_key (str): OpenAI API key
        model (str): OpenAI model to use (default: gpt-4o)
        api_base (str): API base URL
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-4o",
        api_base: str = "https://api.openai.com/v1",
        timeout: float = 120.0,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to environment variable)
            model: OpenAI model to use
            api_base: API base URL
            timeout: Request timeout in seconds
        """
        from src.core.config import settings

        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model
        self.api_base = api_base.rstrip("/")

        # Initialize base client (validates credentials)
        super().__init__(timeout=timeout, provider_name="openai")

        # Rate limiter
        self.rate_limiter = get_provider_limiter().get("openai")

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        if not self.api_key:
            raise ConfigurationError("OpenAI API key (OPENAI_API_KEY) is required")

        logger.debug(
            "OpenAI credentials validated",
            extra={"api_base": self.api_base, "model": self.model},
        )

    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """
        Extract content from a single page using OpenAI vision API.

        Args:
            page_data: Dictionary with "image" key containing image bytes
                      or "text" key for text content
            query: User query describing what to extract
            page_number: Page number for tracking

        Returns:
            ExtractedSection: Extracted content with metadata
        """
        start_time = time.time()
        self._log_extraction_start(page_number)

        # Check if we have image data for vision API
        if "image" in page_data:
            result = await self._extract_with_vision(
                page_data["image"], query, page_number
            )
        elif "text" in page_data:
            # Fallback to text-based extraction
            result = await self._extract_with_text(
                page_data["text"], query, page_number
            )
        else:
            raise ValueError("page_data must contain 'image' or 'text' key")

        extraction_time = time.time() - start_time
        self._log_extraction_complete(page_number, len(result), extraction_time)

        return ExtractedSection(
            page_number=page_number,
            content=result,
            metadata={
                "provider": "openai",
                "model": self.model,
                "extraction_time": extraction_time,
                "has_image": "image" in page_data,
                "output_length": len(result),
            },
        )

    async def _extract_with_vision(
        self, image_bytes: bytes, query: str, page_number: int
    ) -> str:
        """
        Extract content using vision API.

        Args:
            image_bytes: Image data as bytes
            query: User query
            page_number: Page number

        Returns:
            str: Extracted content
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode("utf-8")

        # Build messages with image
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"""You are an OCR and document analysis assistant. Extract information from this image.

USER QUERY: {query}

PAGE: {page_number}

Please extract all relevant information according to the query. Use OCR to read any text, and describe any charts, diagrams, or visual elements. Maintain structure and formatting.""",
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{base64_image}"},
                    },
                ],
            }
        ]

        # Rate limit
        async with self.rate_limiter:
            # Make API request
            async with HTTPClient(timeout=self.timeout) as http_client:
                retry_client = RetryableHTTPClient(
                    http_client, config=RetryConfig(max_attempts=3, backoff_factor=2)
                )

                try:
                    response = await retry_client.post(
                        url=f"{self.api_base}/chat/completions",
                        json={
                            "model": self.model,
                            "messages": messages,
                            "max_tokens": 4000,
                            "temperature": 0.1,
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}",
                        },
                    )

                    response.raise_for_status()
                    result = response.json()

                    # Extract content
                    content = result["choices"][0]["message"]["content"]
                    return content

                except Exception as e:
                    logger.error(
                        f"OpenAI vision extraction failed for page {page_number}",
                        extra={"page_number": page_number, "error": str(e)},
                    )
                    raise APIClientError(
                        f"OpenAI vision extraction failed for page {page_number}: {str(e)}"
                    )

    async def _extract_with_text(self, text: str, query: str, page_number: int) -> str:
        """
        Extract content using text-based API (fallback).

        Args:
            text: Text content
            query: User query
            page_number: Page number

        Returns:
            str: Extracted content
        """
        prompt = f"""You are a document extraction assistant. Extract the requested information.

USER QUERY: {query}

PAGE {page_number} CONTENT:
{text}

Please extract the relevant information according to the query."""

        # Rate limit
        async with self.rate_limiter:
            async with HTTPClient(timeout=self.timeout) as http_client:
                retry_client = RetryableHTTPClient(
                    http_client, config=RetryConfig(max_attempts=3, backoff_factor=2)
                )

                try:
                    response = await retry_client.post(
                        url=f"{self.api_base}/chat/completions",
                        json={
                            "model": self.model,
                            "messages": [{"role": "user", "content": prompt}],
                            "max_tokens": 4000,
                            "temperature": 0.1,
                        },
                        headers={
                            "Content-Type": "application/json",
                            "Authorization": f"Bearer {self.api_key}",
                        },
                    )

                    response.raise_for_status()
                    result = response.json()

                    return result["choices"][0]["message"]["content"]

                except Exception as e:
                    logger.error(
                        f"OpenAI text extraction failed for page {page_number}",
                        extra={"page_number": page_number, "error": str(e)},
                    )
                    raise APIClientError(
                        f"OpenAI extraction failed for page {page_number}: {str(e)}"
                    )

    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """
        Process entire PDF document with OpenAI vision API.

        Note: This is a placeholder implementation. Full implementation
        requires pdf2image for converting PDF pages to images.

        Args:
            pdf_path: Path to PDF file
            query: User query describing what to extract
            chunk_size: Pages to process per chunk

        Returns:
            List[ExtractedSection]: Extracted sections, one per page

        Raises:
            NotImplementedError: PDF to image conversion not yet implemented
        """
        logger.warning(
            "OpenAI process_document requires pdf2image implementation",
            extra={"pdf_path": pdf_path},
        )

        raise NotImplementedError(
            "PDF to image conversion not yet implemented. "
            "Use extract_page_content with pre-converted images."
        )

    async def health_check(self) -> Dict[str, Any]:
        """
        Check OpenAI API health.

        Returns:
            Dict with health status and latency
        """
        start_time = time.time()

        try:
            async with HTTPClient(timeout=10) as http_client:
                # Simple test request
                response = await http_client.post(
                    url=f"{self.api_base}/chat/completions",
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": "test"}],
                        "max_tokens": 10,
                    },
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {self.api_key}",
                    },
                )

                latency = (time.time() - start_time) * 1000  # ms

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "openai",
                        "model": self.model,
                        "latency_ms": round(latency, 2),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "openai",
                        "error": f"HTTP {response.status_code}",
                        "latency_ms": round(latency, 2),
                    }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "provider": "openai",
                "error": str(e),
                "latency_ms": round(latency, 2),
            }
