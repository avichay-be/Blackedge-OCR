"""
Unit tests for HTTP Client.

Tests the async HTTP client with connection pooling, timeout management,
and request logging.
"""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.http_client import HTTPClient, get_http_client


@pytest.mark.asyncio
class TestHTTPClient:
    """Test cases for HTTPClient class."""

    async def test_init(self):
        """Test HTTPClient initialization."""
        client = HTTPClient(timeout=60, max_connections=20)

        assert client.timeout == 60
        assert client.max_connections == 20
        assert client.client is None

    async def test_context_manager(self):
        """Test HTTPClient as async context manager."""
        async with HTTPClient(timeout=30) as client:
            assert client.client is not None
            assert isinstance(client.client, httpx.AsyncClient)

        # Client should be closed after context exit
        # We can't directly test if it's closed, but we can verify it existed

    async def test_get_without_context_manager(self):
        """Test GET request fails without context manager."""
        client = HTTPClient()

        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await client.get("https://example.com")

    async def test_post_without_context_manager(self):
        """Test POST request fails without context manager."""
        client = HTTPClient()

        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await client.post("https://example.com", json={"key": "value"})

    async def test_put_without_context_manager(self):
        """Test PUT request fails without context manager."""
        client = HTTPClient()

        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await client.put("https://example.com", json={"key": "value"})

    async def test_delete_without_context_manager(self):
        """Test DELETE request fails without context manager."""
        client = HTTPClient()

        with pytest.raises(RuntimeError, match="must be used as async context manager"):
            await client.delete("https://example.com")

    @patch('httpx.AsyncClient')
    async def test_get_request(self, mock_async_client):
        """Test GET request with mocked httpx client."""
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"test content"

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            response = await client.get(
                "https://api.example.com/test",
                headers={"Authorization": "Bearer token"},
                params={"page": 1}
            )

            assert response.status_code == 200
            assert response.content == b"test content"

            # Verify the call was made correctly
            mock_client_instance.get.assert_called_once_with(
                "https://api.example.com/test",
                headers={"Authorization": "Bearer token"},
                params={"page": 1}
            )

    @patch('httpx.AsyncClient')
    async def test_post_request_with_json(self, mock_async_client):
        """Test POST request with JSON payload."""
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 201
        mock_response.content = b'{"id": 123}'

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            response = await client.post(
                "https://api.example.com/create",
                json={"name": "test"},
                headers={"Content-Type": "application/json"}
            )

            assert response.status_code == 201

            # Verify the call
            mock_client_instance.post.assert_called_once()

    @patch('httpx.AsyncClient')
    async def test_post_request_with_files(self, mock_async_client):
        """Test POST request with file upload."""
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"uploaded"

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            response = await client.post(
                "https://api.example.com/upload",
                files={"file": ("test.pdf", b"pdf content")}
            )

            assert response.status_code == 200

    @patch('httpx.AsyncClient')
    async def test_put_request(self, mock_async_client):
        """Test PUT request."""
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"updated"

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.put = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            response = await client.put(
                "https://api.example.com/update/123",
                json={"status": "active"}
            )

            assert response.status_code == 200

    @patch('httpx.AsyncClient')
    async def test_delete_request(self, mock_async_client):
        """Test DELETE request."""
        # Setup mock response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 204
        mock_response.content = b""

        # Setup mock client
        mock_client_instance = AsyncMock()
        mock_client_instance.delete = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            response = await client.delete(
                "https://api.example.com/delete/123",
                headers={"Authorization": "Bearer token"}
            )

            assert response.status_code == 204

    @patch('httpx.AsyncClient')
    async def test_http_error_handling(self, mock_async_client):
        """Test HTTP error handling."""
        # Setup mock client to raise exception
        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(
            side_effect=httpx.TimeoutException("Request timeout")
        )
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            with pytest.raises(httpx.TimeoutException):
                await client.get("https://api.example.com/slow")

    @patch('httpx.AsyncClient')
    async def test_network_error_handling(self, mock_async_client):
        """Test network error handling."""
        # Setup mock client to raise network error
        mock_client_instance = AsyncMock()
        mock_client_instance.post = AsyncMock(
            side_effect=httpx.NetworkError("Connection failed")
        )
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with HTTPClient() as client:
            with pytest.raises(httpx.NetworkError):
                await client.post("https://api.example.com/endpoint", json={})


@pytest.mark.asyncio
class TestGetHTTPClient:
    """Test cases for get_http_client convenience function."""

    @patch('httpx.AsyncClient')
    async def test_convenience_function(self, mock_async_client):
        """Test get_http_client convenience function."""
        # Setup mock
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.content = b"success"

        mock_client_instance = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client_instance.aclose = AsyncMock()
        mock_async_client.return_value = mock_client_instance

        async with get_http_client(timeout=30) as client:
            response = await client.get("https://example.com")
            assert response.status_code == 200
            assert isinstance(client, HTTPClient)
