"""
HTTP Client with connection pooling and timeout management.

This module provides an async HTTP client built on httpx with connection pooling,
configurable timeouts, and request logging for all external API calls.

Example:
    async with HTTPClient(timeout=60) as client:
        response = await client.get("https://api.example.com/endpoint")
        print(response.json())
"""

import httpx
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from src.core.logging import get_logger
from src.core.constants import REQUEST_TIMEOUT, MAX_CONCURRENT_REQUESTS

logger = get_logger(__name__)


class HTTPClient:
    """
    Async HTTP client with connection pooling and timeout configuration.

    Provides a reusable HTTP client for making API requests with automatic
    connection pooling, configurable timeouts, and request/response logging.

    Attributes:
        timeout (int): Request timeout in seconds
        max_connections (int): Maximum number of concurrent connections
        client (Optional[httpx.AsyncClient]): The underlying httpx client

    Example:
        async with HTTPClient(timeout=60) as client:
            response = await client.post(
                "https://api.example.com/extract",
                json={"query": "extract data"},
                headers={"Authorization": "Bearer token"}
            )
    """

    def __init__(
        self,
        timeout: int = REQUEST_TIMEOUT,
        max_connections: int = MAX_CONCURRENT_REQUESTS * 2,
    ):
        """
        Initialize HTTP client with timeout and connection pool settings.

        Args:
            timeout: Request timeout in seconds (default: from constants)
            max_connections: Maximum number of connections in pool
                           (default: 2x concurrent requests for efficiency)
        """
        self.timeout = timeout
        self.max_connections = max_connections
        self.client: Optional[httpx.AsyncClient] = None

        logger.debug(
            "HTTPClient initialized",
            extra={"timeout": timeout, "max_connections": max_connections},
        )

    async def __aenter__(self):
        """
        Async context manager entry - creates the httpx client.

        Returns:
            HTTPClient: The initialized client instance
        """
        limits = httpx.Limits(
            max_connections=self.max_connections,
            max_keepalive_connections=self.max_connections // 2,
        )

        self.client = httpx.AsyncClient(
            timeout=httpx.Timeout(self.timeout), limits=limits, follow_redirects=True
        )

        logger.info(
            "HTTP client connection pool created",
            extra={"max_connections": self.max_connections, "timeout": self.timeout},
        )

        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit - closes the httpx client.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        if self.client:
            await self.client.aclose()
            logger.info("HTTP client connection pool closed")

    async def get(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make an async GET request.

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            params: Optional query parameters

        Returns:
            httpx.Response: The HTTP response

        Raises:
            RuntimeError: If client is not initialized (use context manager)
            httpx.HTTPError: On HTTP errors
        """
        if not self.client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(
            "Making GET request",
            extra={
                "url": url,
                "has_headers": bool(headers),
                "has_params": bool(params),
            },
        )

        try:
            response = await self.client.get(url, headers=headers, params=params)

            logger.debug(
                "GET request completed",
                extra={
                    "url": url,
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                },
            )

            return response

        except httpx.HTTPError as e:
            logger.error("GET request failed", extra={"url": url, "error": str(e)})
            raise

    async def post(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make an async POST request.

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            json: Optional JSON payload
            data: Optional form data
            files: Optional files to upload

        Returns:
            httpx.Response: The HTTP response

        Raises:
            RuntimeError: If client is not initialized (use context manager)
            httpx.HTTPError: On HTTP errors
        """
        if not self.client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(
            "Making POST request",
            extra={
                "url": url,
                "has_headers": bool(headers),
                "has_json": bool(json),
                "has_data": bool(data),
                "has_files": bool(files),
            },
        )

        try:
            response = await self.client.post(
                url, headers=headers, json=json, data=data, files=files
            )

            logger.debug(
                "POST request completed",
                extra={
                    "url": url,
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                },
            )

            return response

        except httpx.HTTPError as e:
            logger.error("POST request failed", extra={"url": url, "error": str(e)})
            raise

    async def put(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[str, Any]] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make an async PUT request.

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            json: Optional JSON payload
            data: Optional form data

        Returns:
            httpx.Response: The HTTP response

        Raises:
            RuntimeError: If client is not initialized (use context manager)
            httpx.HTTPError: On HTTP errors
        """
        if not self.client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(
            "Making PUT request",
            extra={
                "url": url,
                "has_headers": bool(headers),
                "has_json": bool(json),
                "has_data": bool(data),
            },
        )

        try:
            response = await self.client.put(url, headers=headers, json=json, data=data)

            logger.debug(
                "PUT request completed",
                extra={
                    "url": url,
                    "status_code": response.status_code,
                    "response_size": len(response.content),
                },
            )

            return response

        except httpx.HTTPError as e:
            logger.error("PUT request failed", extra={"url": url, "error": str(e)})
            raise

    async def delete(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        params: Optional[Dict[str, Any]] = None,
    ) -> httpx.Response:
        """
        Make an async DELETE request.

        Args:
            url: The URL to request
            headers: Optional HTTP headers
            params: Optional query parameters

        Returns:
            httpx.Response: The HTTP response

        Raises:
            RuntimeError: If client is not initialized (use context manager)
            httpx.HTTPError: On HTTP errors
        """
        if not self.client:
            raise RuntimeError("HTTPClient must be used as async context manager")

        logger.debug(
            "Making DELETE request",
            extra={
                "url": url,
                "has_headers": bool(headers),
                "has_params": bool(params),
            },
        )

        try:
            response = await self.client.delete(url, headers=headers, params=params)

            logger.debug(
                "DELETE request completed",
                extra={"url": url, "status_code": response.status_code},
            )

            return response

        except httpx.HTTPError as e:
            logger.error("DELETE request failed", extra={"url": url, "error": str(e)})
            raise


@asynccontextmanager
async def get_http_client(
    timeout: int = REQUEST_TIMEOUT, max_connections: int = MAX_CONCURRENT_REQUESTS * 2
):
    """
    Convenience async context manager for creating HTTP client.

    Args:
        timeout: Request timeout in seconds
        max_connections: Maximum number of connections in pool

    Yields:
        HTTPClient: An initialized HTTP client

    Example:
        async with get_http_client(timeout=60) as client:
            response = await client.get("https://api.example.com")
    """
    client = HTTPClient(timeout=timeout, max_connections=max_connections)
    async with client:
        yield client
