"""Tests for rate limiter."""

import time

import pytest

from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter


class TestAdaptiveRateLimiter:
    """Tests for AdaptiveRateLimiter."""

    def test_initial_state(self):
        """Test initial state of rate limiter."""
        limiter = AdaptiveRateLimiter(
            requests_per_second=2,
            base_interval=0.5,
            max_interval=5.0,
        )

        assert limiter.current_interval == 0.5

    def test_on_rate_limit_increases_interval(self):
        """Test that rate limit response increases interval."""
        limiter = AdaptiveRateLimiter(base_interval=0.5, max_interval=5.0)

        limiter.on_rate_limit()

        assert limiter.current_interval > 0.5

    def test_exponential_backoff(self):
        """Test exponential backoff on multiple rate limits."""
        limiter = AdaptiveRateLimiter(base_interval=0.5, max_interval=5.0)

        limiter.on_rate_limit()  # 1.0s
        limiter.on_rate_limit()  # 2.0s
        limiter.on_rate_limit()  # 4.0s
        limiter.on_rate_limit()  # 5.0s (max)

        assert limiter.current_interval == 5.0  # Capped at max

    def test_on_success_decreases_interval(self):
        """Test that success gradually decreases interval."""
        limiter = AdaptiveRateLimiter(base_interval=0.5, max_interval=5.0)

        # Simulate rate limits
        limiter.on_rate_limit()
        limiter.on_rate_limit()

        # Simulate successes
        limiter.on_success()
        limiter.on_success()

        assert limiter.current_interval == 0.5  # Back to base

    def test_reset(self):
        """Test reset returns to initial state."""
        limiter = AdaptiveRateLimiter(base_interval=0.5)

        limiter.on_rate_limit()
        limiter.on_rate_limit()

        limiter.reset()

        assert limiter.current_interval == 0.5

    @pytest.mark.asyncio
    async def test_acquire_respects_rate_limit(self):
        """Test that acquire respects rate limit."""
        limiter = AdaptiveRateLimiter(
            requests_per_second=10,
            base_interval=0.01,  # Very short for testing
        )

        start = time.time()

        # Make 5 rapid requests
        for _ in range(5):
            await limiter.acquire()

        elapsed = time.time() - start

        # Should take at least some time due to rate limiting
        assert elapsed >= 0.04  # At least 4 intervals
