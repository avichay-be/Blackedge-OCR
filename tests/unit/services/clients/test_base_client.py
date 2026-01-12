"""
Unit tests for Base Document Client.

Tests the abstract base class that all AI provider clients inherit from.
"""

import pytest
from typing import Dict, Any, List

from src.services.clients.base_client import BaseDocumentClient
from src.core.error_handling import ConfigurationError
from src.models.workflow_models import ExtractedSection


class ConcreteTestClient(BaseDocumentClient):
    """Concrete implementation for testing BaseDocumentClient."""

    def __init__(self, api_key: str = None, should_fail_validation: bool = False):
        self.api_key = api_key
        self.should_fail_validation = should_fail_validation
        super().__init__(timeout=60.0, provider_name="test")

    def _validate_credentials(self):
        """Test credential validation."""
        if self.should_fail_validation:
            raise ConfigurationError("Test validation failed")
        if not self.api_key:
            raise ConfigurationError("API key required")

    async def extract_page_content(
        self, page_data: Dict[str, Any], query: str, page_number: int
    ) -> ExtractedSection:
        """Test page extraction."""
        return ExtractedSection(
            page_number=page_number,
            content=f"Extracted content for page {page_number}",
            metadata={"provider": "test", "query": query},
        )

    async def process_document(
        self, pdf_path: str, query: str, chunk_size: int = 50
    ) -> List[ExtractedSection]:
        """Test document processing."""
        return [
            ExtractedSection(
                page_number=1,
                content="Page 1 content",
                metadata={"provider": "test"},
            )
        ]

    async def health_check(self) -> Dict[str, Any]:
        """Test health check."""
        return {"status": "healthy", "provider": "test"}


class TestBaseDocumentClient:
    """Test cases for BaseDocumentClient."""

    def test_init_success(self):
        """Test successful initialization."""
        client = ConcreteTestClient(api_key="test_key")

        assert client.timeout == 60.0
        assert client.provider_name == "test"
        assert client.api_key == "test_key"

    def test_init_validation_failure(self):
        """Test initialization with credential validation failure."""
        with pytest.raises(ConfigurationError, match="Test validation failed"):
            ConcreteTestClient(api_key="key", should_fail_validation=True)

    def test_init_missing_credentials(self):
        """Test initialization with missing credentials."""
        with pytest.raises(ConfigurationError, match="API key required"):
            ConcreteTestClient(api_key=None)

    @pytest.mark.asyncio
    async def test_context_manager(self):
        """Test async context manager protocol."""
        client = ConcreteTestClient(api_key="test_key")

        async with client as ctx_client:
            assert ctx_client is client
            assert ctx_client.provider_name == "test"

    @pytest.mark.asyncio
    async def test_extract_page_content(self):
        """Test page content extraction."""
        client = ConcreteTestClient(api_key="test_key")

        section = await client.extract_page_content(
            page_data={"text": "sample text"}, query="extract data", page_number=1
        )

        assert section.page_number == 1
        assert "Extracted content for page 1" in section.content
        assert section.metadata["provider"] == "test"
        assert section.metadata["query"] == "extract data"

    @pytest.mark.asyncio
    async def test_process_document(self):
        """Test full document processing."""
        client = ConcreteTestClient(api_key="test_key")

        sections = await client.process_document(
            pdf_path="test.pdf", query="extract all"
        )

        assert len(sections) == 1
        assert sections[0].page_number == 1
        assert sections[0].content == "Page 1 content"

    @pytest.mark.asyncio
    async def test_health_check(self):
        """Test health check."""
        client = ConcreteTestClient(api_key="test_key")

        health = await client.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "test"

    def test_log_extraction_start(self):
        """Test extraction start logging."""
        client = ConcreteTestClient(api_key="test_key")

        # Should not raise exception
        client._log_extraction_start(page_number=1)
        client._log_extraction_start(page_number=1, total_pages=10)

    def test_log_extraction_complete(self):
        """Test extraction completion logging."""
        client = ConcreteTestClient(api_key="test_key")

        # Should not raise exception
        client._log_extraction_complete(
            page_number=1, content_length=100, extraction_time=1.5
        )

    @pytest.mark.asyncio
    async def test_context_manager_with_exception(self):
        """Test context manager handles exceptions."""

        class FailingClient(ConcreteTestClient):
            async def extract_page_content(self, page_data, query, page_number):
                raise ValueError("Test error")

        client = FailingClient(api_key="test_key")

        with pytest.raises(ValueError, match="Test error"):
            async with client:
                await client.extract_page_content({}, "query", 1)
