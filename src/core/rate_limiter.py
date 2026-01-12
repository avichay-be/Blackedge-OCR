"""
Rate Limiter using token bucket algorithm.

This module implements async-safe rate limiting using the token bucket algorithm
to prevent exceeding API provider rate limits.

Example:
    limiter = RateLimiter(rate_per_minute=60)
    async with limiter:
        # Make API call - automatically waits if rate limit exceeded
        response = await api_call()
"""

import asyncio
import time
from typing import Optional

from src.core.logging import get_logger
from src.core.constants import RATE_LIMITS

logger = get_logger(__name__)


class RateLimiter:
    """
    Token bucket rate limiter for async API calls.

    Implements the token bucket algorithm to control request rates.
    Each request consumes one token. Tokens are replenished at a constant rate.
    If no tokens are available, requests wait until a token is available.

    Attributes:
        rate_per_minute (int): Maximum requests per minute
        tokens (float): Current number of available tokens
        max_tokens (int): Maximum token capacity (same as rate)
        last_update (float): Timestamp of last token replenishment

    Example:
        limiter = RateLimiter(rate_per_minute=60)
        async with limiter:
            # This call will wait if rate limit is exceeded
            response = await make_api_call()
    """

    def __init__(self, rate_per_minute: int):
        """
        Initialize rate limiter with specified rate.

        Args:
            rate_per_minute: Maximum number of requests allowed per minute
        """
        if rate_per_minute <= 0:
            raise ValueError("Rate per minute must be positive")

        self.rate_per_minute = rate_per_minute
        self.tokens = float(rate_per_minute)
        self.max_tokens = rate_per_minute
        self.last_update = time.time()
        self._lock = asyncio.Lock()

        logger.debug(
            "RateLimiter initialized",
            extra={"rate_per_minute": rate_per_minute, "initial_tokens": self.tokens},
        )

    def _replenish_tokens(self):
        """
        Replenish tokens based on elapsed time.

        Calculates how many tokens should be added based on time elapsed
        since last update and adds them to the bucket (up to max capacity).
        """
        now = time.time()
        elapsed = now - self.last_update

        # Calculate tokens to add based on elapsed time
        # rate_per_minute / 60 = tokens per second
        tokens_to_add = (self.rate_per_minute / 60.0) * elapsed

        # Add tokens, but don't exceed maximum
        self.tokens = min(self.max_tokens, self.tokens + tokens_to_add)
        self.last_update = now

        logger.debug(
            "Tokens replenished",
            extra={
                "elapsed_seconds": elapsed,
                "tokens_added": tokens_to_add,
                "current_tokens": self.tokens,
            },
        )

    async def acquire(self):
        """
        Acquire a token (wait if necessary).

        Waits until a token is available, then consumes it.
        This method is async-safe and can be called from multiple coroutines.

        Raises:
            asyncio.CancelledError: If the coroutine is cancelled while waiting
        """
        async with self._lock:
            while True:
                self._replenish_tokens()

                if self.tokens >= 1.0:
                    # Token available - consume it and proceed
                    self.tokens -= 1.0

                    logger.debug(
                        "Token acquired",
                        extra={
                            "remaining_tokens": self.tokens,
                            "rate_per_minute": self.rate_per_minute,
                        },
                    )
                    return

                # No tokens available - calculate wait time
                wait_time = (1.0 - self.tokens) / (self.rate_per_minute / 60.0)

                logger.debug(
                    "Rate limit reached - waiting",
                    extra={
                        "wait_seconds": wait_time,
                        "current_tokens": self.tokens,
                        "rate_per_minute": self.rate_per_minute,
                    },
                )

                # Release lock while waiting
                await asyncio.sleep(wait_time)

    async def __aenter__(self):
        """
        Async context manager entry - acquires a token.

        Returns:
            RateLimiter: The rate limiter instance
        """
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """
        Async context manager exit.

        Args:
            exc_type: Exception type if an exception occurred
            exc_val: Exception value if an exception occurred
            exc_tb: Exception traceback if an exception occurred
        """
        # Nothing to clean up - token was already consumed
        pass

    def get_available_tokens(self) -> int:
        """
        Get the current number of available tokens (rounded down).

        Returns:
            int: Number of tokens available
        """
        self._replenish_tokens()
        return int(self.tokens)

    def reset(self):
        """
        Reset the rate limiter to full capacity.

        Useful for testing or manual rate limit resets.
        """
        self.tokens = float(self.max_tokens)
        self.last_update = time.time()

        logger.info(
            "RateLimiter reset",
            extra={"rate_per_minute": self.rate_per_minute, "tokens": self.tokens},
        )


class ProviderRateLimiter:
    """
    Rate limiter factory for different AI providers.

    Creates and manages rate limiters for each AI provider based on
    their specific rate limits defined in constants.

    Example:
        limiters = ProviderRateLimiter()
        async with limiters.get("mistral"):
            # Make Mistral API call
            response = await mistral_client.extract(pdf)
    """

    def __init__(self):
        """Initialize provider rate limiters based on constants."""
        self._limiters = {
            provider: RateLimiter(rate_per_minute)
            for provider, rate_per_minute in RATE_LIMITS.items()
        }

        logger.info(
            "ProviderRateLimiter initialized",
            extra={
                "providers": list(self._limiters.keys()),
                "rate_limits": RATE_LIMITS,
            },
        )

    def get(self, provider: str) -> RateLimiter:
        """
        Get rate limiter for a specific provider.

        Args:
            provider: Provider name (mistral, openai, gemini, azure_di)

        Returns:
            RateLimiter: The rate limiter for this provider

        Raises:
            ValueError: If provider is not recognized
        """
        if provider not in self._limiters:
            raise ValueError(
                f"Unknown provider: {provider}. "
                f"Available providers: {list(self._limiters.keys())}"
            )

        return self._limiters[provider]

    def get_status(self) -> dict:
        """
        Get current status of all rate limiters.

        Returns:
            dict: Dictionary mapping provider names to available token counts
        """
        return {
            provider: limiter.get_available_tokens()
            for provider, limiter in self._limiters.items()
        }

    def reset_all(self):
        """Reset all provider rate limiters to full capacity."""
        for limiter in self._limiters.values():
            limiter.reset()

        logger.info("All provider rate limiters reset")

    def reset(self, provider: str):
        """
        Reset a specific provider's rate limiter.

        Args:
            provider: Provider name to reset

        Raises:
            ValueError: If provider is not recognized
        """
        limiter = self.get(provider)
        limiter.reset()


# Global provider rate limiter instance (singleton)
_provider_limiter: Optional[ProviderRateLimiter] = None


def get_provider_limiter() -> ProviderRateLimiter:
    """
    Get the global provider rate limiter instance (singleton).

    Returns:
        ProviderRateLimiter: The global rate limiter instance

    Example:
        limiter = get_provider_limiter()
        async with limiter.get("mistral"):
            response = await mistral_api_call()
    """
    global _provider_limiter

    if _provider_limiter is None:
        _provider_limiter = ProviderRateLimiter()

    return _provider_limiter
