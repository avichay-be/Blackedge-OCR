"""
Unit tests for Rate Limiter.

Tests the token bucket rate limiter with async support and provider-specific limits.
"""

import pytest
import asyncio
import time
from unittest.mock import patch

from src.core.rate_limiter import (
    RateLimiter,
    ProviderRateLimiter,
    get_provider_limiter
)


@pytest.mark.asyncio
class TestRateLimiter:
    """Test cases for RateLimiter class."""

    def test_init(self):
        """Test RateLimiter initialization."""
        limiter = RateLimiter(rate_per_minute=60)

        assert limiter.rate_per_minute == 60
        assert limiter.tokens == 60.0
        assert limiter.max_tokens == 60

    def test_init_invalid_rate(self):
        """Test RateLimiter with invalid rate."""
        with pytest.raises(ValueError, match="Rate per minute must be positive"):
            RateLimiter(rate_per_minute=0)

        with pytest.raises(ValueError, match="Rate per minute must be positive"):
            RateLimiter(rate_per_minute=-10)

    def test_replenish_tokens(self):
        """Test token replenishment over time."""
        limiter = RateLimiter(rate_per_minute=60)
        limiter.tokens = 0.0
        limiter.last_update = time.time() - 1.0  # 1 second ago

        limiter._replenish_tokens()

        # After 1 second, should have ~1 token (60/60 = 1 per second)
        assert limiter.tokens >= 0.9
        assert limiter.tokens <= 1.1

    def test_tokens_dont_exceed_max(self):
        """Test that tokens don't exceed maximum capacity."""
        limiter = RateLimiter(rate_per_minute=60)
        limiter.last_update = time.time() - 120.0  # 2 minutes ago

        limiter._replenish_tokens()

        # Even after 2 minutes, tokens should be capped at max
        assert limiter.tokens == 60.0

    async def test_acquire_with_available_tokens(self):
        """Test acquiring token when tokens are available."""
        limiter = RateLimiter(rate_per_minute=60)

        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should be nearly instant
        assert elapsed < 0.1
        assert limiter.tokens < 60.0  # One token consumed

    async def test_acquire_waits_when_no_tokens(self):
        """Test that acquire waits when no tokens available."""
        limiter = RateLimiter(rate_per_minute=60)  # 1 token per second
        limiter.tokens = 0.5  # Not enough for one request

        start = time.time()
        await limiter.acquire()
        elapsed = time.time() - start

        # Should wait approximately 0.5 seconds to get to 1.0 tokens
        assert elapsed >= 0.4  # Allow some margin
        assert elapsed < 1.0

    async def test_context_manager(self):
        """Test RateLimiter as async context manager."""
        limiter = RateLimiter(rate_per_minute=60)
        initial_tokens = limiter.tokens

        async with limiter:
            # Token should be consumed
            assert limiter.tokens < initial_tokens

    async def test_multiple_concurrent_acquires(self):
        """Test multiple concurrent token acquisitions."""
        limiter = RateLimiter(rate_per_minute=60)

        # Try to acquire 5 tokens concurrently
        start = time.time()
        await asyncio.gather(
            limiter.acquire(),
            limiter.acquire(),
            limiter.acquire(),
            limiter.acquire(),
            limiter.acquire()
        )
        elapsed = time.time() - start

        # Should be relatively fast since we start with 60 tokens
        assert elapsed < 1.0
        # 5 tokens should be consumed
        assert limiter.tokens < 56.0

    async def test_rate_limiting_enforcement(self):
        """Test that rate limiting actually limits requests."""
        limiter = RateLimiter(rate_per_minute=120)  # 2 per second
        limiter.tokens = 2.0  # Start with only 2 tokens

        # Acquire 3 tokens - third should wait
        start = time.time()
        await limiter.acquire()  # 1st - instant
        await limiter.acquire()  # 2nd - instant
        await limiter.acquire()  # 3rd - should wait ~0.5 seconds

        elapsed = time.time() - start

        # Should have waited for token replenishment
        assert elapsed >= 0.4
        assert elapsed < 1.0

    def test_get_available_tokens(self):
        """Test getting available token count."""
        limiter = RateLimiter(rate_per_minute=60)
        limiter.tokens = 45.7

        available = limiter.get_available_tokens()

        assert available == 45

    def test_reset(self):
        """Test resetting rate limiter."""
        limiter = RateLimiter(rate_per_minute=60)
        limiter.tokens = 10.0

        limiter.reset()

        assert limiter.tokens == 60.0


@pytest.mark.asyncio
class TestProviderRateLimiter:
    """Test cases for ProviderRateLimiter class."""

    def test_init(self):
        """Test ProviderRateLimiter initialization."""
        limiter = ProviderRateLimiter()

        assert "mistral" in limiter._limiters
        assert "openai" in limiter._limiters
        assert "gemini" in limiter._limiters
        assert "azure_di" in limiter._limiters

    def test_get_limiter(self):
        """Test getting limiter for specific provider."""
        limiters = ProviderRateLimiter()

        mistral_limiter = limiters.get("mistral")
        assert isinstance(mistral_limiter, RateLimiter)
        assert mistral_limiter.rate_per_minute == 60

        openai_limiter = limiters.get("openai")
        assert isinstance(openai_limiter, RateLimiter)
        assert openai_limiter.rate_per_minute == 50

    def test_get_unknown_provider(self):
        """Test getting limiter for unknown provider."""
        limiters = ProviderRateLimiter()

        with pytest.raises(ValueError, match="Unknown provider"):
            limiters.get("unknown_provider")

    async def test_provider_specific_rates(self):
        """Test that different providers have different rates."""
        limiters = ProviderRateLimiter()

        mistral = limiters.get("mistral")
        openai = limiters.get("openai")
        azure_di = limiters.get("azure_di")

        assert mistral.rate_per_minute == 60
        assert openai.rate_per_minute == 50
        assert azure_di.rate_per_minute == 30

    def test_get_status(self):
        """Test getting status of all limiters."""
        limiters = ProviderRateLimiter()

        status = limiters.get_status()

        assert "mistral" in status
        assert "openai" in status
        assert "gemini" in status
        assert "azure_di" in status

        # All should start at their max
        assert status["mistral"] == 60
        assert status["openai"] == 50
        assert status["gemini"] == 60
        assert status["azure_di"] == 30

    async def test_reset_all(self):
        """Test resetting all provider limiters."""
        limiters = ProviderRateLimiter()

        # Consume some tokens
        await limiters.get("mistral").acquire()
        await limiters.get("openai").acquire()

        # Reset all
        limiters.reset_all()

        status = limiters.get_status()
        assert status["mistral"] == 60
        assert status["openai"] == 50

    async def test_reset_specific_provider(self):
        """Test resetting specific provider limiter."""
        limiters = ProviderRateLimiter()

        # Consume tokens
        await limiters.get("mistral").acquire()
        await limiters.get("openai").acquire()

        # Reset only mistral
        limiters.reset("mistral")

        status = limiters.get_status()
        assert status["mistral"] == 60
        assert status["openai"] < 50  # Should still be consumed

    async def test_independent_rate_limits(self):
        """Test that provider rate limits are independent."""
        limiters = ProviderRateLimiter()

        # Use mistral limiter
        mistral = limiters.get("mistral")
        await mistral.acquire()

        # OpenAI should still have full tokens
        openai = limiters.get("openai")
        assert openai.get_available_tokens() == 50


@pytest.mark.asyncio
class TestGetProviderLimiter:
    """Test cases for get_provider_limiter singleton function."""

    def test_singleton_behavior(self):
        """Test that get_provider_limiter returns singleton."""
        limiter1 = get_provider_limiter()
        limiter2 = get_provider_limiter()

        assert limiter1 is limiter2

    async def test_singleton_state_persistence(self):
        """Test that singleton state persists across calls."""
        limiter1 = get_provider_limiter()
        await limiter1.get("mistral").acquire()

        limiter2 = get_provider_limiter()
        status = limiter2.get_status()

        # Token should be consumed from previous call
        assert status["mistral"] < 60
