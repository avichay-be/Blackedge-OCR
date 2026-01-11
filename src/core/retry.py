"""
Retry logic with exponential backoff for API calls.

This module provides decorators and utilities for implementing retry logic
with exponential backoff for handling transient failures in API calls.

Example:
    @with_retry(max_attempts=3)
    async def call_api():
        response = await client.post(url, json=data)
        return response
"""

import asyncio
import functools
from typing import Callable, TypeVar, Any, Optional, Tuple, Type
import httpx

from src.core.logging import get_logger
from src.core.constants import MAX_RETRIES, RETRY_BACKOFF_FACTOR, RETRY_STATUS_CODES

logger = get_logger(__name__)

# Type variable for generic function signatures
T = TypeVar("T")


class RetryConfig:
    """
    Configuration for retry behavior.

    Attributes:
        max_attempts: Maximum number of retry attempts (including first try)
        backoff_factor: Exponential backoff multiplier (in seconds)
        retry_status_codes: HTTP status codes that trigger retry
        retry_exceptions: Exception types that trigger retry
    """

    def __init__(
        self,
        max_attempts: int = MAX_RETRIES,
        backoff_factor: float = RETRY_BACKOFF_FACTOR,
        retry_status_codes: Optional[list] = None,
        retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
    ):
        """
        Initialize retry configuration.

        Args:
            max_attempts: Maximum retry attempts (default: from constants)
            backoff_factor: Backoff multiplier in seconds (default: from constants)
            retry_status_codes: Status codes to retry (default: from constants)
            retry_exceptions: Exception types to retry (default: httpx errors)
        """
        self.max_attempts = max_attempts
        self.backoff_factor = backoff_factor
        self.retry_status_codes = retry_status_codes or RETRY_STATUS_CODES
        self.retry_exceptions = retry_exceptions or (
            httpx.TimeoutException,
            httpx.NetworkError,
            httpx.RemoteProtocolError,
            httpx.ConnectError,
        )


def calculate_backoff(attempt: int, backoff_factor: float) -> float:
    """
    Calculate exponential backoff delay.

    Args:
        attempt: Current attempt number (0-indexed)
        backoff_factor: Base backoff factor in seconds

    Returns:
        float: Delay in seconds

    Example:
        >>> calculate_backoff(0, 2)
        2.0
        >>> calculate_backoff(1, 2)
        4.0
        >>> calculate_backoff(2, 2)
        8.0
    """
    return backoff_factor * (2**attempt)


def should_retry_status(status_code: int, retry_status_codes: list) -> bool:
    """
    Determine if HTTP status code should trigger retry.

    Args:
        status_code: HTTP status code
        retry_status_codes: List of status codes that should trigger retry

    Returns:
        bool: True if should retry, False otherwise
    """
    return status_code in retry_status_codes


async def retry_async(
    func: Callable[..., Any], config: RetryConfig, *args, **kwargs
) -> Any:
    """
    Execute async function with retry logic.

    Args:
        func: Async function to execute
        config: Retry configuration
        *args: Positional arguments for func
        **kwargs: Keyword arguments for func

    Returns:
        Any: Return value from func

    Raises:
        Exception: The last exception if all retries fail
    """
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            result = await func(*args, **kwargs)

            # Check if result is an httpx Response with retry-able status
            if isinstance(result, httpx.Response):
                if should_retry_status(result.status_code, config.retry_status_codes):
                    if attempt < config.max_attempts - 1:
                        delay = calculate_backoff(attempt, config.backoff_factor)

                        logger.warning(
                            "HTTP error - retrying",
                            extra={
                                "attempt": attempt + 1,
                                "max_attempts": config.max_attempts,
                                "status_code": result.status_code,
                                "delay_seconds": delay,
                            },
                        )

                        await asyncio.sleep(delay)
                        continue
                    else:
                        # Last attempt - return the error response
                        logger.error(
                            "HTTP error - max retries reached",
                            extra={
                                "attempts": config.max_attempts,
                                "status_code": result.status_code,
                            },
                        )
                        return result

            # Success or non-retry-able response
            if attempt > 0:
                logger.info(
                    "Retry succeeded",
                    extra={"attempt": attempt + 1, "total_attempts": attempt + 1},
                )

            return result

        except config.retry_exceptions as e:
            last_exception = e

            if attempt < config.max_attempts - 1:
                delay = calculate_backoff(attempt, config.backoff_factor)

                logger.warning(
                    "Request failed - retrying",
                    extra={
                        "attempt": attempt + 1,
                        "max_attempts": config.max_attempts,
                        "exception": type(e).__name__,
                        "error": str(e),
                        "delay_seconds": delay,
                    },
                )

                await asyncio.sleep(delay)
            else:
                logger.error(
                    "Request failed - max retries reached",
                    extra={
                        "attempts": config.max_attempts,
                        "exception": type(e).__name__,
                        "error": str(e),
                    },
                )
                raise

        except Exception as e:
            # Non-retry-able exception - fail immediately
            logger.error(
                "Non-retryable exception",
                extra={
                    "attempt": attempt + 1,
                    "exception": type(e).__name__,
                    "error": str(e),
                },
            )
            raise

    # Should not reach here, but handle it just in case
    if last_exception:
        raise last_exception


def with_retry(
    max_attempts: int = MAX_RETRIES,
    backoff_factor: float = RETRY_BACKOFF_FACTOR,
    retry_status_codes: Optional[list] = None,
    retry_exceptions: Optional[Tuple[Type[Exception], ...]] = None,
):
    """
    Decorator to add retry logic to async functions.

    Args:
        max_attempts: Maximum retry attempts
        backoff_factor: Exponential backoff multiplier
        retry_status_codes: HTTP status codes to retry
        retry_exceptions: Exception types to retry

    Returns:
        Callable: Decorated function with retry logic

    Example:
        @with_retry(max_attempts=3, backoff_factor=2)
        async def fetch_data(url: str):
            async with HTTPClient() as client:
                response = await client.get(url)
                return response.json()
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        backoff_factor=backoff_factor,
        retry_status_codes=retry_status_codes,
        retry_exceptions=retry_exceptions,
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            return await retry_async(func, config, *args, **kwargs)

        return wrapper

    return decorator


class RetryableHTTPClient:
    """
    HTTP client wrapper with built-in retry logic.

    Wraps an HTTPClient instance and automatically retries failed requests.

    Example:
        from src.core.http_client import HTTPClient

        async with HTTPClient() as http_client:
            retry_client = RetryableHTTPClient(http_client)
            response = await retry_client.get("https://api.example.com")
    """

    def __init__(self, http_client: Any, config: Optional[RetryConfig] = None):
        """
        Initialize retryable HTTP client.

        Args:
            http_client: HTTPClient instance to wrap
            config: Optional retry configuration (uses defaults if not provided)
        """
        self.http_client = http_client
        self.config = config or RetryConfig()

        logger.debug(
            "RetryableHTTPClient initialized",
            extra={
                "max_attempts": self.config.max_attempts,
                "backoff_factor": self.config.backoff_factor,
            },
        )

    async def get(self, url: str, **kwargs) -> httpx.Response:
        """
        Make GET request with retry logic.

        Args:
            url: URL to request
            **kwargs: Additional arguments for http_client.get()

        Returns:
            httpx.Response: HTTP response
        """
        return await retry_async(self.http_client.get, self.config, url, **kwargs)

    async def post(self, url: str, **kwargs) -> httpx.Response:
        """
        Make POST request with retry logic.

        Args:
            url: URL to request
            **kwargs: Additional arguments for http_client.post()

        Returns:
            httpx.Response: HTTP response
        """
        return await retry_async(self.http_client.post, self.config, url, **kwargs)

    async def put(self, url: str, **kwargs) -> httpx.Response:
        """
        Make PUT request with retry logic.

        Args:
            url: URL to request
            **kwargs: Additional arguments for http_client.put()

        Returns:
            httpx.Response: HTTP response
        """
        return await retry_async(self.http_client.put, self.config, url, **kwargs)

    async def delete(self, url: str, **kwargs) -> httpx.Response:
        """
        Make DELETE request with retry logic.

        Args:
            url: URL to request
            **kwargs: Additional arguments for http_client.delete()

        Returns:
            httpx.Response: HTTP response
        """
        return await retry_async(self.http_client.delete, self.config, url, **kwargs)
