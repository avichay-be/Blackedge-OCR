"""
Unit tests for Gemini Client.

Tests the Google Gemini AI client.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.services.clients.gemini_client import GeminiClient
from src.core.error_handling import ConfigurationError, APIClientError


@pytest.mark.asyncio
class TestGeminiClient:
    """Test cases for GeminiClient."""

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    def test_init_success(self, mock_limiter):
        """Test successful initialization."""
        mock_limiter.return_value.get.return_value = MagicMock()

        client = GeminiClient(api_key="test_key")

        assert client.api_key == "test_key"
        assert client.model == "gemini-pro"
        assert client.provider_name == "gemini"
        assert client.timeout == 120.0

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    def test_init_missing_api_key(self, mock_limiter):
        """Test initialization with missing API key."""
        mock_limiter.return_value.get.return_value = MagicMock()

        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ConfigurationError, match="Gemini API key"):
                GeminiClient(api_key=None)

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    @patch("src.services.clients.gemini_client.HTTPClient")
    async def test_extract_page_content(self, mock_http_client, mock_limiter):
        """Test single page extraction."""
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
                "candidates": [
                    {"content": {"parts": [{"text": "Extracted content from Gemini"}]}}
                ]
            }
        )

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        # Create client and test
        client = GeminiClient(api_key="test_key")

        section = await client.extract_page_content(
            page_data={"text": "Sample text"}, query="Extract data", page_number=1
        )

        assert section.page_number == 1
        assert section.content == "Extracted content from Gemini"
        assert section.metadata["provider"] == "gemini"
        assert section.metadata["model"] == "gemini-pro"

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    @patch("src.services.clients.gemini_client.HTTPClient")
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

        client = GeminiClient(api_key="test_key")
        health = await client.health_check()

        assert health["status"] == "healthy"
        assert health["provider"] == "gemini"
        assert health["model"] == "gemini-pro"
        assert "latency_ms" in health

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    @patch("src.services.clients.gemini_client.HTTPClient")
    async def test_health_check_unhealthy(self, mock_http_client, mock_limiter):
        """Test health check with unhealthy API."""
        mock_limiter.return_value.get.return_value = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.post = AsyncMock(side_effect=Exception("Connection error"))
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock(return_value=None)
        mock_http_client.return_value = mock_client_instance

        client = GeminiClient(api_key="test_key")
        health = await client.health_check()

        assert health["status"] == "unhealthy"
        assert "error" in health

    @patch("src.services.clients.gemini_client.get_provider_limiter")
    @patch("src.services.clients.gemini_client.HTTPClient")
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

        client = GeminiClient(api_key="test_key")

        with pytest.raises(APIClientError, match="Gemini extraction failed"):
            await client.extract_page_content(
                page_data={"text": "test"}, query="Extract", page_number=1
            )

    def test_build_prompt(self):
        """Test prompt building."""
        client = GeminiClient(api_key="test_key")

        prompt = client._build_prompt(
            query="Extract tables", page_text="Page content here", page_number=5
        )

        assert "Extract tables" in prompt
        assert "PAGE 5" in prompt
        assert "Page content here" in prompt
        assert "PDF content extraction assistant" in prompt
