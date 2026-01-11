"""
Unit tests for OpenAI Client.

Tests the OpenAI GPT-4o client with vision API support.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import base64

from src.services.clients.openai_client import OpenAIClient
from src.core.error_handling import ConfigurationError, APIClientError


@pytest.mark.asyncio
class TestOpenAIClient:
    """Test cases for OpenAIClient."""

    @patch("src.services.clients.openai_client.get_provider_limiter")
    def test_init_success(self, mock_limiter):
        """Test successful initialization."""
        mock_limiter.return_value.get.return_value = MagicMock()

        with patch.dict("os.environ", {"OPENAI_API_KEY": "test_key"}, clear=False):
            client = OpenAIClient(api_key="test_key")

            assert client.api_key == "test_key"
            assert client.model == "gpt-4o"
            assert client.provider_name == "openai"
            assert client.timeout == 120.0

    @patch("src.services.clients.openai_client.get_provider_limiter")
    def test_init_missing_api_key(self, mock_limiter):
        """Test initialization with missing API key."""
        mock_limiter.return_value.get.return_value = MagicMock()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ConfigurationError, match="OpenAI API key"):
                OpenAIClient(api_key=None)

    @patch("src.services.clients.openai_client.get_provider_limiter")
    @patch("src.services.clients.openai_client.HTTPClient")
    async def test_extract_with_vision(self, mock_http_client, mock_limiter):
        """Test vision-based extraction."""
        # Setup mocks
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.__aenter__ = AsyncMock(return_value=None)
        mock_rate_limiter.__aexit__ = AsyncMock(return_value=None)
        mock_limiter.return_value.get.return_value = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={
                "choices": [{"message": {"content": "Extracted text from image"}}]
            }
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Create client
        client = OpenAIClient(api_key="test_key")

        # Test extraction with image
        image_bytes = b"fake image data"
        section = await client.extract_page_content(
            page_data={"image": image_bytes}, query="Extract text", page_number=1
        )

        assert section.page_number == 1
        assert section.content == "Extracted text from image"
        assert section.metadata["provider"] == "openai"
        assert section.metadata["has_image"] is True

    @patch("src.services.clients.openai_client.get_provider_limiter")
    @patch("src.services.clients.openai_client.HTTPClient")
    async def test_extract_with_text(self, mock_http_client, mock_limiter):
        """Test text-based extraction (fallback)."""
        # Setup mocks
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.__aenter__ = AsyncMock(return_value=None)
        mock_rate_limiter.__aexit__ = AsyncMock(return_value=None)
        mock_limiter.return_value.get.return_value = mock_rate_limiter

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.raise_for_status = MagicMock()
        mock_response.json = MagicMock(
            return_value={"choices": [{"message": {"content": "Extracted from text"}}]}
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Create client
        client = OpenAIClient(api_key="test_key")

        # Test extraction with text
        section = await client.extract_page_content(
            page_data={"text": "Sample text"}, query="Extract data", page_number=1
        )

        assert section.page_number == 1
        assert section.content == "Extracted from text"
        assert section.metadata["has_image"] is False

    @patch("src.services.clients.openai_client.get_provider_limiter")
    async def test_extract_missing_data(self, mock_limiter):
        """Test extraction with missing page data."""
        mock_limiter.return_value.get.return_value = MagicMock()

        client = OpenAIClient(api_key="test_key")

        with pytest.raises(ValueError, match="must contain 'image' or 'text'"):
            await client.extract_page_content(
                page_data={}, query="Extract", page_number=1
            )

    @patch("src.services.clients.openai_client.get_provider_limiter")
    async def test_process_document_not_implemented(self, mock_limiter):
        """Test that process_document raises NotImplementedError."""
        mock_limiter.return_value.get.return_value = MagicMock()

        client = OpenAIClient(api_key="test_key")

        with pytest.raises(NotImplementedError, match="PDF to image conversion"):
            await client.process_document("test.pdf", "Extract all")

    @patch("src.services.clients.openai_client.get_provider_limiter")
    @patch("src.services.clients.openai_client.HTTPClient")
    async def test_health_check_healthy(self, mock_http_client, mock_limiter):
        """Test health check with healthy API."""
        mock_limiter.return_value.get.return_value = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 200

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        client = OpenAIClient(api_key="test_key")
        health = await client.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "openai"
        assert "latency_ms" in health

    @patch("src.services.clients.openai_client.get_provider_limiter")
    @patch("src.services.clients.openai_client.HTTPClient")
    async def test_health_check_unhealthy(self, mock_http_client, mock_limiter):
        """Test health check with unhealthy API."""
        mock_limiter.return_value.get.return_value = MagicMock()

        mock_response = MagicMock()
        mock_response.status_code = 503

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        client = OpenAIClient(api_key="test_key")
        health = await client.health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health

    @patch("src.services.clients.openai_client.get_provider_limiter")
    @patch("src.services.clients.openai_client.HTTPClient")
    async def test_extraction_api_error(self, mock_http_client, mock_limiter):
        """Test extraction with API error."""
        # Setup mocks
        mock_rate_limiter = MagicMock()
        mock_rate_limiter.__aenter__ = AsyncMock(return_value=None)
        mock_rate_limiter.__aexit__ = AsyncMock(return_value=None)
        mock_limiter.return_value.get.return_value = mock_rate_limiter

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("API Error"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        client = OpenAIClient(api_key="test_key")

        with pytest.raises(APIClientError, match="OpenAI vision extraction failed"):
            await client.extract_page_content(
                page_data={"image": b"data"}, query="Extract", page_number=1
            )
