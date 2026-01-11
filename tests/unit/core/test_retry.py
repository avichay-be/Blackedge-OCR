"""
Unit tests for Retry Logic.

Tests the retry mechanism with exponential backoff, status code handling,
and exception handling.
"""

import pytest
import asyncio
import httpx
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.retry import (
    RetryConfig,
    calculate_backoff,
    should_retry_status,
    retry_async,
    with_retry,
    RetryableHTTPClient
)


class TestCalculateBackoff:
    """Test cases for calculate_backoff function."""

    def test_backoff_calculation(self):
        """Test exponential backoff calculation."""
        assert calculate_backoff(0, 2) == 2.0
        assert calculate_backoff(1, 2) == 4.0
        assert calculate_backoff(2, 2) == 8.0
        assert calculate_backoff(3, 2) == 16.0

    def test_backoff_with_different_factor(self):
        """Test backoff with different base factor."""
        assert calculate_backoff(0, 1) == 1.0
        assert calculate_backoff(1, 1) == 2.0
        assert calculate_backoff(2, 1) == 4.0

    def test_backoff_with_fractional_factor(self):
        """Test backoff with fractional factor."""
        assert calculate_backoff(0, 0.5) == 0.5
        assert calculate_backoff(1, 0.5) == 1.0
        assert calculate_backoff(2, 0.5) == 2.0


class TestShouldRetryStatus:
    """Test cases for should_retry_status function."""

    def test_retry_status_codes(self):
        """Test detection of retry-able status codes."""
        retry_codes = [429, 500, 502, 503, 504]

        assert should_retry_status(429, retry_codes) is True
        assert should_retry_status(500, retry_codes) is True
        assert should_retry_status(502, retry_codes) is True
        assert should_retry_status(503, retry_codes) is True
        assert should_retry_status(504, retry_codes) is True

    def test_non_retry_status_codes(self):
        """Test detection of non-retry-able status codes."""
        retry_codes = [429, 500, 502, 503, 504]

        assert should_retry_status(200, retry_codes) is False
        assert should_retry_status(400, retry_codes) is False
        assert should_retry_status(401, retry_codes) is False
        assert should_retry_status(404, retry_codes) is False


class TestRetryConfig:
    """Test cases for RetryConfig class."""

    def test_default_config(self):
        """Test default retry configuration."""
        config = RetryConfig()

        assert config.max_attempts == 3
        assert config.backoff_factor == 2
        assert 429 in config.retry_status_codes
        assert 500 in config.retry_status_codes

    def test_custom_config(self):
        """Test custom retry configuration."""
        config = RetryConfig(
            max_attempts=5,
            backoff_factor=1.5,
            retry_status_codes=[429, 503],
            retry_exceptions=(ValueError,)
        )

        assert config.max_attempts == 5
        assert config.backoff_factor == 1.5
        assert config.retry_status_codes == [429, 503]
        assert config.retry_exceptions == (ValueError,)


@pytest.mark.asyncio
class TestRetryAsync:
    """Test cases for retry_async function."""

    async def test_successful_first_attempt(self):
        """Test successful execution on first attempt."""
        mock_func = AsyncMock(return_value="success")

        result = await retry_async(mock_func, RetryConfig(max_attempts=3))

        assert result == "success"
        assert mock_func.call_count == 1

    async def test_retry_on_exception(self):
        """Test retry on exception."""
        mock_func = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                httpx.TimeoutException("timeout"),
                "success"
            ]
        )

        config = RetryConfig(max_attempts=3, backoff_factor=0.01)
        result = await retry_async(mock_func, config)

        assert result == "success"
        assert mock_func.call_count == 3

    async def test_max_retries_exceeded(self):
        """Test failure after max retries exceeded."""
        mock_func = AsyncMock(
            side_effect=httpx.TimeoutException("timeout")
        )

        config = RetryConfig(max_attempts=3, backoff_factor=0.01)

        with pytest.raises(httpx.TimeoutException):
            await retry_async(mock_func, config)

        assert mock_func.call_count == 3

    async def test_non_retryable_exception(self):
        """Test immediate failure on non-retryable exception."""
        mock_func = AsyncMock(side_effect=ValueError("bad value"))

        config = RetryConfig(max_attempts=3, backoff_factor=0.01)

        with pytest.raises(ValueError, match="bad value"):
            await retry_async(mock_func, config)

        # Should fail immediately, not retry
        assert mock_func.call_count == 1

    async def test_retry_on_status_code(self):
        """Test retry on specific HTTP status codes."""
        # Create mock responses
        response_503 = MagicMock(spec=httpx.Response)
        response_503.status_code = 503
        response_503.content = b"service unavailable"

        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.content = b"success"

        mock_func = AsyncMock(
            side_effect=[response_503, response_503, response_200]
        )

        config = RetryConfig(
            max_attempts=3,
            backoff_factor=0.01,
            retry_status_codes=[503]
        )

        result = await retry_async(mock_func, config)

        assert result.status_code == 200
        assert mock_func.call_count == 3

    async def test_non_retry_status_code(self):
        """Test no retry on non-retry-able status codes."""
        response_400 = MagicMock(spec=httpx.Response)
        response_400.status_code = 400
        response_400.content = b"bad request"

        mock_func = AsyncMock(return_value=response_400)

        config = RetryConfig(
            max_attempts=3,
            backoff_factor=0.01,
            retry_status_codes=[429, 503]  # 400 not in list
        )

        result = await retry_async(mock_func, config)

        # Should not retry on 400
        assert result.status_code == 400
        assert mock_func.call_count == 1

    async def test_backoff_timing(self):
        """Test that exponential backoff actually waits."""
        import time

        mock_func = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                "success"
            ]
        )

        config = RetryConfig(max_attempts=3, backoff_factor=0.1)

        start = time.time()
        await retry_async(mock_func, config)
        elapsed = time.time() - start

        # First backoff should be ~0.1 seconds
        assert elapsed >= 0.09
        assert elapsed < 0.5


@pytest.mark.asyncio
class TestWithRetryDecorator:
    """Test cases for with_retry decorator."""

    async def test_decorator_on_success(self):
        """Test decorator with successful function."""
        @with_retry(max_attempts=3, backoff_factor=0.01)
        async def successful_func():
            return "success"

        result = await successful_func()
        assert result == "success"

    async def test_decorator_with_retries(self):
        """Test decorator with retries."""
        call_count = 0

        @with_retry(max_attempts=3, backoff_factor=0.01)
        async def flaky_func():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise httpx.TimeoutException("timeout")
            return "success"

        result = await flaky_func()

        assert result == "success"
        assert call_count == 3

    async def test_decorator_with_args(self):
        """Test decorator with function arguments."""
        @with_retry(max_attempts=3, backoff_factor=0.01)
        async def func_with_args(x, y, z=10):
            return x + y + z

        result = await func_with_args(5, 3, z=2)
        assert result == 10

    async def test_decorator_preserves_function_metadata(self):
        """Test that decorator preserves function metadata."""
        @with_retry(max_attempts=3)
        async def documented_func():
            """This is a documented function."""
            return "result"

        assert documented_func.__name__ == "documented_func"
        assert "documented function" in documented_func.__doc__


@pytest.mark.asyncio
class TestRetryableHTTPClient:
    """Test cases for RetryableHTTPClient class."""

    async def test_init(self):
        """Test RetryableHTTPClient initialization."""
        mock_client = MagicMock()
        retry_client = RetryableHTTPClient(mock_client)

        assert retry_client.http_client is mock_client
        assert retry_client.config is not None

    async def test_init_with_custom_config(self):
        """Test initialization with custom config."""
        mock_client = MagicMock()
        config = RetryConfig(max_attempts=5, backoff_factor=1.5)
        retry_client = RetryableHTTPClient(mock_client, config=config)

        assert retry_client.config.max_attempts == 5
        assert retry_client.config.backoff_factor == 1.5

    async def test_get_with_retry(self):
        """Test GET request with retry."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            side_effect=[
                httpx.TimeoutException("timeout"),
                MagicMock(status_code=200, content=b"success")
            ]
        )

        config = RetryConfig(max_attempts=3, backoff_factor=0.01)
        retry_client = RetryableHTTPClient(mock_client, config=config)

        response = await retry_client.get("https://api.example.com")

        assert response.status_code == 200
        assert mock_client.get.call_count == 2

    async def test_post_with_retry(self):
        """Test POST request with retry."""
        mock_client = MagicMock()

        response_503 = MagicMock(spec=httpx.Response)
        response_503.status_code = 503
        response_503.content = b"unavailable"

        response_200 = MagicMock(spec=httpx.Response)
        response_200.status_code = 200
        response_200.content = b"success"

        mock_client.post = AsyncMock(
            side_effect=[response_503, response_200]
        )

        config = RetryConfig(
            max_attempts=3,
            backoff_factor=0.01,
            retry_status_codes=[503]
        )
        retry_client = RetryableHTTPClient(mock_client, config=config)

        response = await retry_client.post(
            "https://api.example.com",
            json={"data": "test"}
        )

        assert response.status_code == 200
        assert mock_client.post.call_count == 2

    async def test_put_with_retry(self):
        """Test PUT request with retry."""
        mock_client = MagicMock()
        mock_client.put = AsyncMock(
            return_value=MagicMock(status_code=200, content=b"updated")
        )

        retry_client = RetryableHTTPClient(mock_client)

        response = await retry_client.put(
            "https://api.example.com",
            json={"status": "active"}
        )

        assert response.status_code == 200
        assert mock_client.put.call_count == 1

    async def test_delete_with_retry(self):
        """Test DELETE request with retry."""
        mock_client = MagicMock()
        mock_client.delete = AsyncMock(
            return_value=MagicMock(status_code=204, content=b"")
        )

        retry_client = RetryableHTTPClient(mock_client)

        response = await retry_client.delete("https://api.example.com/123")

        assert response.status_code == 204
        assert mock_client.delete.call_count == 1

    async def test_all_methods_support_kwargs(self):
        """Test that all methods pass through kwargs correctly."""
        mock_client = MagicMock()
        mock_client.get = AsyncMock(
            return_value=MagicMock(status_code=200, content=b"ok")
        )
        mock_client.post = AsyncMock(
            return_value=MagicMock(status_code=201, content=b"created")
        )

        retry_client = RetryableHTTPClient(mock_client)

        # Test GET with headers
        await retry_client.get(
            "https://api.example.com",
            headers={"Authorization": "Bearer token"}
        )
        mock_client.get.assert_called_once()

        # Test POST with json and headers
        await retry_client.post(
            "https://api.example.com",
            json={"data": "test"},
            headers={"Content-Type": "application/json"}
        )
        mock_client.post.assert_called_once()
