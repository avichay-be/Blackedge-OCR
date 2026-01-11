"""
Unit tests for Client Factory.

Tests the singleton factory for managing all document processing clients.
"""

import pytest
from unittest.mock import patch, MagicMock, AsyncMock

from src.services.client_factory import ClientFactory, get_client_factory


class TestClientFactory:
    """Test cases for ClientFactory."""

    def test_singleton_pattern(self):
        """Test that ClientFactory implements singleton pattern."""
        factory1 = ClientFactory()
        factory2 = ClientFactory()

        assert factory1 is factory2

    def test_get_client_factory_singleton(self):
        """Test that get_client_factory returns singleton."""
        factory1 = get_client_factory()
        factory2 = get_client_factory()

        assert factory1 is factory2
        assert isinstance(factory1, ClientFactory)

    @patch("src.services.client_factory.MistralClient")
    def test_mistral_lazy_initialization(self, mock_mistral):
        """Test that Mistral client is lazily initialized."""
        factory = ClientFactory()
        factory.reset()  # Clear any existing clients

        # Client should not be created yet
        assert factory._mistral_client is None

        # Access property
        mock_mistral.return_value = MagicMock()
        client = factory.mistral

        # Now client should be created
        assert client is not None
        mock_mistral.assert_called_once()

        # Second access should return same instance
        client2 = factory.mistral
        assert client is client2
        assert mock_mistral.call_count == 1  # Still only called once

    @patch("src.services.client_factory.OpenAIClient")
    def test_openai_lazy_initialization(self, mock_openai):
        """Test that OpenAI client is lazily initialized."""
        factory = ClientFactory()
        factory.reset()

        assert factory._openai_client is None

        mock_openai.return_value = MagicMock()
        client = factory.openai

        assert client is not None
        mock_openai.assert_called_once()

    @patch("src.services.client_factory.GeminiClient")
    def test_gemini_lazy_initialization(self, mock_gemini):
        """Test that Gemini client is lazily initialized."""
        factory = ClientFactory()
        factory.reset()

        assert factory._gemini_client is None

        mock_gemini.return_value = MagicMock()
        client = factory.gemini

        assert client is not None
        mock_gemini.assert_called_once()

    @patch("src.services.client_factory.AzureDIClient")
    def test_azure_di_lazy_initialization(self, mock_azure):
        """Test that Azure DI client is lazily initialized."""
        factory = ClientFactory()
        factory.reset()

        assert factory._azure_di_client is None

        mock_azure.return_value = MagicMock()
        client = factory.azure_di

        assert client is not None
        mock_azure.assert_called_once()

    @patch("src.services.client_factory.MistralClient")
    def test_get_client_by_name(self, mock_mistral):
        """Test getting client by provider name."""
        factory = ClientFactory()
        factory.reset()

        mock_mistral.return_value = MagicMock()

        client = factory.get_client("mistral")
        assert client is not None

        client2 = factory.get_client("MISTRAL")  # Case insensitive
        assert client2 is client

    def test_get_client_unknown_provider(self):
        """Test getting client with unknown provider name."""
        factory = ClientFactory()

        with pytest.raises(ValueError, match="Unknown provider"):
            factory.get_client("unknown_provider")

    @pytest.mark.asyncio
    @patch("src.services.client_factory.MistralClient")
    @patch("src.services.client_factory.OpenAIClient")
    async def test_health_check_all_no_clients(self, mock_openai, mock_mistral):
        """Test health check when no clients are initialized."""
        factory = ClientFactory()
        factory.reset()

        health = await factory.health_check_all()

        assert health == {}

    @pytest.mark.asyncio
    @patch("src.services.client_factory.MistralClient")
    async def test_health_check_all_with_clients(self, mock_mistral):
        """Test health check with active clients."""
        factory = ClientFactory()
        factory.reset()

        # Create mock client with health check
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(
            return_value={"status": "healthy", "latency_ms": 100}
        )
        mock_mistral.return_value = mock_client

        # Initialize client
        _ = factory.mistral

        # Health check
        health = await factory.health_check_all()

        assert "mistral" in health
        assert health["mistral"]["status"] == "healthy"
        assert health["mistral"]["latency_ms"] == 100

    @pytest.mark.asyncio
    @patch("src.services.client_factory.MistralClient")
    async def test_health_check_with_error(self, mock_mistral):
        """Test health check when client health check fails."""
        factory = ClientFactory()
        factory.reset()

        # Create mock client that raises error
        mock_client = MagicMock()
        mock_client.health_check = AsyncMock(side_effect=Exception("Connection error"))
        mock_mistral.return_value = mock_client

        # Initialize client
        _ = factory.mistral

        # Health check should not raise, but return error status
        health = await factory.health_check_all()

        assert "mistral" in health
        assert health["mistral"]["status"] == "unhealthy"
        assert "error" in health["mistral"]

    @pytest.mark.asyncio
    async def test_cleanup(self):
        """Test cleanup of all clients."""
        factory = ClientFactory()
        factory.reset()

        # Set some mock clients
        factory._mistral_client = MagicMock()
        factory._openai_client = MagicMock()

        await factory.cleanup()

        # All clients should be None
        assert factory._mistral_client is None
        assert factory._openai_client is None

    def test_get_active_clients_none(self):
        """Test getting active clients when none are initialized."""
        factory = ClientFactory()
        factory.reset()

        active = factory.get_active_clients()

        assert active == []

    @patch("src.services.client_factory.MistralClient")
    @patch("src.services.client_factory.OpenAIClient")
    def test_get_active_clients_multiple(self, mock_openai, mock_mistral):
        """Test getting active clients when multiple are initialized."""
        factory = ClientFactory()
        factory.reset()

        mock_mistral.return_value = MagicMock()
        mock_openai.return_value = MagicMock()

        # Initialize some clients
        _ = factory.mistral
        _ = factory.openai

        active = factory.get_active_clients()

        assert "mistral" in active
        assert "openai" in active
        assert len(active) == 2

    def test_reset(self):
        """Test resetting factory."""
        factory = ClientFactory()

        # Set some mock clients
        factory._mistral_client = MagicMock()
        factory._openai_client = MagicMock()

        # Reset
        factory.reset()

        # All should be None
        assert factory._mistral_client is None
        assert factory._openai_client is None
        assert factory._gemini_client is None
        assert factory._azure_di_client is None

    @patch("src.services.client_factory.AzureDIClient")
    def test_get_client_azure_di_variants(self, mock_azure):
        """Test that Azure DI client can be accessed with different name variants."""
        factory = ClientFactory()
        factory.reset()

        mock_azure.return_value = MagicMock()

        # All these should work
        client1 = factory.get_client("azure_di")
        client2 = factory.get_client("azure-di")
        client3 = factory.get_client("azuredi")

        assert client1 is client2 is client3
