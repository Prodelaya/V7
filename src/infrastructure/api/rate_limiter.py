"""Adaptive rate limiter with exponential backoff.

Implementation Requirements:
- Base interval: 0.5 seconds
- Max interval: 5.0 seconds
- Exponential backoff on 429 errors
- Gradual recovery on success
- Formula: interval = min(5.0, 0.5 * 2^consecutive_429)

Reference:
- docs/05-Implementation.md: Task 5B.1
- docs/02-PDR.md: Section 4.4 (Adaptive Rate Limiter)
- docs/03-ADRs.md: ADR-010
- docs/01-SRS.md: RF-002
"""

import asyncio


class AdaptiveRateLimiter:
    """
    Adaptive rate limiter with exponential backoff.

    Adjusts polling interval based on API responses:
    - On success: gradually decrease interval
    - On 429: exponentially increase interval

    Formula: interval = min(max_interval, base_interval * 2^consecutive_429)

    Intervals (from docs/01-SRS.md Appendix 6.3):
        | Scenario    | Interval |
        |-------------|----------|
        | Normal      | 0.5s     |
        | 1x 429      | 1.0s     |
        | 2x 429      | 2.0s     |
        | 3x 429      | 4.0s     |
        | 4+ 429      | 5.0s     |
        | Success     | -1 level |

    Example:
        >>> limiter = AdaptiveRateLimiter()
        >>> limiter.current_interval
        0.5
        >>> limiter.on_rate_limit()  # Received 429
        >>> limiter.current_interval
        1.0
        >>> limiter.on_success()  # Request succeeded
        >>> limiter.current_interval
        0.5
    """

    def __init__(
        self,
        requests_per_second: int = 2,
        base_interval: float = 0.5,
        max_interval: float = 5.0,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum requests per second (for compatibility)
            base_interval: Base polling interval in seconds (default: 0.5)
            max_interval: Maximum interval cap (default: 5.0)
        """
        self._requests_per_second = requests_per_second
        self._base_interval = base_interval
        self._max_interval = max_interval
        self._consecutive_429 = 0

    @property
    def current_interval(self) -> float:
        """
        Current polling interval based on error count.

        Formula: min(max_interval, base_interval * 2^consecutive_429)

        Returns:
            Current interval in seconds
        """
        return min(
            self._max_interval,
            self._base_interval * (2 ** self._consecutive_429),
        )

    async def acquire(self) -> None:
        """
        Wait for the current interval before allowing next request.

        This implements rate limiting by sleeping for the current_interval
        duration between requests.
        """
        await asyncio.sleep(self.current_interval)

    async def wait_if_needed(self) -> None:
        """
        Wait for the current interval before next request.

        Alias for acquire() for backward compatibility.
        """
        await self.acquire()

    def on_success(self) -> None:
        """
        Report successful request, decrease interval gradually.

        Decrements consecutive_429 counter (min 0).
        """
        self._consecutive_429 = max(0, self._consecutive_429 - 1)

    def on_rate_limit(self) -> None:
        """
        Report 429 error, increase interval exponentially.

        Increments consecutive_429 counter.
        """
        self._consecutive_429 += 1

    def report_success(self) -> None:
        """
        Report successful request, decrease interval gradually.

        Alias for on_success() for backward compatibility.
        """
        self.on_success()

    def report_rate_limit(self) -> None:
        """
        Report 429 error, increase interval exponentially.

        Alias for on_rate_limit() for backward compatibility.
        """
        self.on_rate_limit()

    def reset(self) -> None:
        """
        Reset to initial state.

        Sets consecutive_429 counter back to 0.
        """
        self._consecutive_429 = 0
