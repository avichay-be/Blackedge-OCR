"""
Azure Document Intelligence client for document processing.

This module provides a client for Azure Document Intelligence (Form Recognizer)
specialized for complex tables, forms, and structured document extraction.

Example:
    async with AzureDIClient() as client:
        sections = await client.process_document(
            "form_document.pdf",
            "Extract all form fields and tables"
        )
"""

import time
import asyncio
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


class AzureDIClient(BaseDocumentClient):
    """
    Azure Document Intelligence client.

    Uses Azure Form Recognizer / Document Intelligence for extraction
    of complex tables, forms, and structured documents.

    Attributes:
        endpoint (str): Azure DI endpoint URL
        api_key (str): Azure DI API key
        api_version (str): API version to use
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        api_version: str = "2023-07-31",
        timeout: float = 120.0,
    ):
        """
        Initialize Azure DI client.

        Args:
            endpoint: Azure DI endpoint (defaults to environment variable)
            api_key: Azure DI API key (defaults to environment variable)
            api_version: API version to use
            timeout: Request timeout in seconds
        """
        from src.core.config import settings

        self.endpoint = (endpoint or settings.AZURE_DI_ENDPOINT).rstrip("/")
        self.api_key = api_key or settings.AZURE_DI_KEY
        self.api_version = api_version

        # Initialize base client (validates credentials)
        super().__init__(timeout=timeout, provider_name="azure_di")

        # Rate limiter
        self.rate_limiter = get_provider_limiter().get("azure_di")

    def _validate_credentials(self):
        """Validate that required credentials are present."""
        if not self.endpoint:
            raise ConfigurationError(
                "Azure DI endpoint (AZURE_DI_ENDPOINT) is required"
            )
        if not self.api_key:
            raise ConfigurationError("Azure DI API key (AZURE_DI_KEY) is required")

        logger.debug(
            "Azure DI credentials validated",
            extra={"endpoint": self.endpoint, "api_version": self.api_version},
        )

    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """
        Extract content from a single page using Azure DI.

        Note: Azure DI works best with full documents. This method
        is provided for interface compatibility but may not be optimal.

        Args:
            page_data: Dictionary with page information
            query: User query describing what to extract
            page_number: Page number for tracking

        Returns:
            ExtractedSection: Extracted content with metadata
        """
        start_time = time.time()
        self._log_extraction_start(page_number)

        # For single page, we'll use a simplified text extraction
        # Real implementation would require document submission
        logger.warning(
            "Azure DI single page extraction is limited. "
            "Use process_document() for best results."
        )

        content = f"Page {page_number} - Azure DI requires full document processing"

        extraction_time = time.time() - start_time
        self._log_extraction_complete(page_number, len(content), extraction_time)

        return ExtractedSection(
            page_number=page_number,
            content=content,
            metadata={
                "provider": "azure_di",
                "extraction_time": extraction_time,
                "warning": "Single page extraction not fully supported",
            },
        )

    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """
        Process entire PDF document with Azure Document Intelligence.

        Submits document for analysis and polls for results.

        Args:
            pdf_path: Path to PDF file
            query: User query (informational - Azure DI extracts all content)
            chunk_size: Not used (Azure DI processes entire document)

        Returns:
            List[ExtractedSection]: Extracted sections with tables and forms
        """
        logger.info(
            f"Processing document with Azure DI",
            extra={"pdf_path": pdf_path, "api_version": self.api_version},
        )

        try:
            # Read PDF file
            with open(pdf_path, "rb") as f:
                pdf_bytes = f.read()

            # Submit document for analysis
            operation_location = await self._submit_document(pdf_bytes)

            # Poll for results
            result = await self._poll_for_result(operation_location)

            # Parse results into sections
            sections = self._parse_analysis_result(result)

            logger.info(
                f"Document processing complete",
                extra={
                    "total_pages": len(sections),
                    "provider": "azure_di",
                },
            )

            return sections

        except FileNotFoundError:
            raise FileProcessingError(f"PDF file not found: {pdf_path}")
        except Exception as e:
            logger.error(f"Document processing failed: {str(e)}")
            raise FileProcessingError(f"Failed to process document: {str(e)}")

    async def _submit_document(self, pdf_bytes: bytes) -> str:
        """
        Submit document to Azure DI for analysis.

        Args:
            pdf_bytes: PDF file bytes

        Returns:
            str: Operation location URL for polling
        """
        # Rate limit
        async with self.rate_limiter:
            async with HTTPClient(timeout=self.timeout) as http_client:
                retry_client = RetryableHTTPClient(
                    http_client, config=RetryConfig(max_attempts=3, backoff_factor=2)
                )

                try:
                    response = await retry_client.post(
                        url=f"{self.endpoint}/formrecognizer/documentModels/prebuilt-layout:analyze?api-version={self.api_version}",
                        data=pdf_bytes,
                        headers={
                            "Content-Type": "application/pdf",
                            "Ocp-Apim-Subscription-Key": self.api_key,
                        },
                    )

                    response.raise_for_status()

                    # Get operation location from headers
                    operation_location = response.headers.get("Operation-Location")
                    if not operation_location:
                        raise APIClientError("No operation location in response")

                    logger.info(
                        "Document submitted to Azure DI",
                        extra={"operation_location": operation_location},
                    )

                    return operation_location

                except Exception as e:
                    logger.error(f"Failed to submit document: {str(e)}")
                    raise APIClientError(f"Document submission failed: {str(e)}")

    async def _poll_for_result(
        self, operation_location: str, max_wait: int = 300, poll_interval: int = 2
    ) -> Dict[str, Any]:
        """
        Poll for analysis results.

        Args:
            operation_location: URL to poll for results
            max_wait: Maximum wait time in seconds
            poll_interval: Polling interval in seconds

        Returns:
            Dict: Analysis result

        Raises:
            APIClientError: If polling times out or fails
        """
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            async with HTTPClient(timeout=30) as http_client:
                try:
                    response = await http_client.get(
                        url=operation_location,
                        headers={"Ocp-Apim-Subscription-Key": self.api_key},
                    )

                    response.raise_for_status()
                    result = response.json()

                    status = result.get("status")

                    if status == "succeeded":
                        logger.info(
                            "Analysis complete",
                            extra={
                                "elapsed_seconds": time.time() - start_time,
                            },
                        )
                        return result

                    elif status == "failed":
                        error = result.get("error", {})
                        raise APIClientError(f"Analysis failed: {error}")

                    elif status in ["notStarted", "running"]:
                        logger.debug(f"Analysis in progress: {status}")
                        await asyncio.sleep(poll_interval)

                    else:
                        raise APIClientError(f"Unknown status: {status}")

                except Exception as e:
                    if "Analysis failed" in str(e):
                        raise
                    logger.warning(f"Polling error: {str(e)}")
                    await asyncio.sleep(poll_interval)

        raise APIClientError(f"Analysis timeout after {max_wait} seconds")

    def _parse_analysis_result(self, result: Dict[str, Any]) -> List[ExtractedSection]:
        """
        Parse Azure DI analysis result into sections.

        Args:
            result: Analysis result from Azure DI

        Returns:
            List[ExtractedSection]: Extracted sections by page
        """
        analysis_result = result.get("analyzeResult", {})
        pages = analysis_result.get("pages", [])

        sections = []
        for page in pages:
            page_num = page.get("pageNumber", 0)

            # Extract all text
            lines = page.get("lines", [])
            text_content = "\n".join([line.get("content", "") for line in lines])

            # Extract tables if present
            tables = self._extract_tables_for_page(analysis_result, page_num)
            if tables:
                text_content += "\n\n" + tables

            sections.append(
                ExtractedSection(
                    page_number=page_num,
                    content=text_content,
                    metadata={
                        "provider": "azure_di",
                        "has_tables": bool(tables),
                        "line_count": len(lines),
                    },
                )
            )

        return sections

    def _extract_tables_for_page(
        self, analysis_result: Dict[str, Any], page_num: int
    ) -> str:
        """
        Extract formatted tables for a specific page.

        Args:
            analysis_result: Full analysis result
            page_num: Page number to extract tables from

        Returns:
            str: Formatted tables as text
        """
        tables = analysis_result.get("tables", [])
        page_tables = []

        for table in tables:
            # Check if table is on this page
            if table.get("boundingRegions", [{}])[0].get("pageNumber") == page_num:
                # Format table cells
                rows = {}
                for cell in table.get("cells", []):
                    row_idx = cell.get("rowIndex", 0)
                    col_idx = cell.get("columnIndex", 0)
                    content = cell.get("content", "")

                    if row_idx not in rows:
                        rows[row_idx] = {}
                    rows[row_idx][col_idx] = content

                # Format as text
                table_text = "\n".join(
                    [
                        " | ".join(
                            [rows[row].get(col, "") for col in sorted(rows[row].keys())]
                        )
                        for row in sorted(rows.keys())
                    ]
                )
                page_tables.append(f"\nTABLE:\n{table_text}")

        return "\n".join(page_tables)

    async def health_check(self) -> Dict[str, Any]:
        """
        Check Azure DI API health.

        Returns:
            Dict with health status and latency
        """
        start_time = time.time()

        try:
            # Check endpoint availability
            async with HTTPClient(timeout=10) as http_client:
                # Info endpoint doesn't need document submission
                response = await http_client.get(
                    url=f"{self.endpoint}/formrecognizer/info?api-version={self.api_version}",
                    headers={"Ocp-Apim-Subscription-Key": self.api_key},
                )

                latency = (time.time() - start_time) * 1000  # ms

                if response.status_code == 200:
                    return {
                        "status": "healthy",
                        "provider": "azure_di",
                        "api_version": self.api_version,
                        "latency_ms": round(latency, 2),
                    }
                else:
                    return {
                        "status": "unhealthy",
                        "provider": "azure_di",
                        "error": f"HTTP {response.status_code}",
                        "latency_ms": round(latency, 2),
                    }

        except Exception as e:
            latency = (time.time() - start_time) * 1000
            return {
                "status": "unhealthy",
                "provider": "azure_di",
                "error": str(e),
                "latency_ms": round(latency, 2),
            }
