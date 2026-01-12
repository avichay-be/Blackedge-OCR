"""
Unit tests for Default Handler (Mistral).

Tests the Mistral-based extraction workflow.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.workflows.default_handler import DefaultHandler
from src.workflows.workflow_types import WorkflowType
from src.models.workflow_models import ExtractedSection
from src.core.error_handling import APIClientError, ExtractionError


@pytest.mark.asyncio
class TestDefaultHandler:
    """Test cases for DefaultHandler."""

    def test_initialization(self):
        """Test handler initialization."""
        handler = DefaultHandler()

        assert handler.workflow_type == WorkflowType.MISTRAL
        assert isinstance(handler, DefaultHandler)

    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_success(self, mock_get_factory):
        """Test successful extraction with Mistral."""
        # Mock Mistral client
        mock_mistral_client = MagicMock()
        mock_sections = [
            ExtractedSection(
                page_number=1,
                content="Page 1 content",
                metadata={"provider": "mistral"},
            ),
            ExtractedSection(
                page_number=2,
                content="Page 2 content",
                metadata={"provider": "mistral"},
            ),
        ]
        mock_mistral_client.process_document = AsyncMock(return_value=mock_sections)
        mock_mistral_client.model = "mistral-large"

        # Mock factory
        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute
        handler = DefaultHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract data")

        # Verify
        assert "Page 1 content" in result.content
        assert "Page 2 content" in result.content
        assert result.metadata["workflow"] == "mistral"
        assert result.metadata["provider"] == "mistral"
        assert result.metadata["pages"] == 2
        assert result.metadata["model"] == "mistral-large"
        assert len(result.sections) == 2

        # Verify client was called correctly
        mock_mistral_client.process_document.assert_called_once_with(
            pdf_path="/test/file.pdf", query="extract data"
        )

    @patch("src.services.workflows.default_handler.settings")
    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_with_validation_disabled(
        self, mock_get_factory, mock_settings
    ):
        """Test execution with validation disabled."""
        mock_settings.ENABLE_CROSS_VALIDATION = False

        # Mock client
        mock_mistral_client = MagicMock()
        mock_sections = [
            ExtractedSection(page_number=1, content="Content", metadata={})
        ]
        mock_mistral_client.process_document = AsyncMock(return_value=mock_sections)
        mock_mistral_client.model = "mistral-large"

        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute
        handler = DefaultHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract")

        # Verify validation was not performed
        assert result.validation_report is None
        assert result.metadata["validation_enabled"] is False

    @patch("src.services.workflows.default_handler.settings")
    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_with_validation_enabled(
        self, mock_get_factory, mock_settings
    ):
        """Test execution with validation enabled (not implemented yet)."""
        mock_settings.ENABLE_CROSS_VALIDATION = False  # Default off

        # Mock client
        mock_mistral_client = MagicMock()
        mock_sections = [
            ExtractedSection(page_number=1, content="Content", metadata={})
        ]
        mock_mistral_client.process_document = AsyncMock(return_value=mock_sections)
        mock_mistral_client.model = "mistral-large"

        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute with explicit validation=True
        handler = DefaultHandler()
        result = await handler.execute(
            pdf_path="/test/file.pdf", query="extract", enable_validation=True
        )

        # Since validation is not implemented yet (Phase 5), should still be None
        assert result.validation_report is None
        assert result.metadata["validation_enabled"] is True

    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_api_error(self, mock_get_factory):
        """Test handling of API client errors."""
        # Mock client to raise API error
        mock_mistral_client = MagicMock()
        mock_mistral_client.process_document = AsyncMock(
            side_effect=APIClientError("API rate limit exceeded")
        )
        mock_mistral_client.model = "mistral-large"

        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute should propagate APIClientError
        handler = DefaultHandler()
        with pytest.raises(APIClientError, match="API rate limit exceeded"):
            await handler.execute(pdf_path="/test/file.pdf", query="extract")

    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_generic_error(self, mock_get_factory):
        """Test handling of generic errors."""
        # Mock client to raise generic error
        mock_mistral_client = MagicMock()
        mock_mistral_client.process_document = AsyncMock(
            side_effect=Exception("Unexpected error")
        )
        mock_mistral_client.model = "mistral-large"

        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute should wrap in ExtractionError
        handler = DefaultHandler()
        with pytest.raises(ExtractionError, match="Failed to process document"):
            await handler.execute(pdf_path="/test/file.pdf", query="extract")

    @patch("src.services.workflows.default_handler.get_client_factory")
    async def test_execute_empty_sections(self, mock_get_factory):
        """Test execution when client returns empty sections."""
        # Mock client with empty result
        mock_mistral_client = MagicMock()
        mock_mistral_client.process_document = AsyncMock(return_value=[])
        mock_mistral_client.model = "mistral-large"

        mock_factory = MagicMock()
        mock_factory.mistral = mock_mistral_client
        mock_get_factory.return_value = mock_factory

        # Execute
        handler = DefaultHandler()
        result = await handler.execute(pdf_path="/test/file.pdf", query="extract")

        # Should handle empty result gracefully
        assert result.content == ""
        assert result.metadata["pages"] == 0
        assert len(result.sections) == 0
