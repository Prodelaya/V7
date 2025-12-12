"""Adaptive rate limiter with backoff."""

import asyncio
import time
import logging
from collections import deque


logger = logging.getLogger(__name__)


class AdaptiveRateLimiter:
    """
    Rate limiter with adaptive polling interval.
    
    Adjusts interval based on API responses:
    - Increases on 429 errors (up to max)
    - Decreases gradually on success
    """
    
    def __init__(
        self,
        requests_per_second: int = 2,
        base_interval: float = 0.5,
        max_interval: float = 5.0,
    ):
        self._requests_per_second = requests_per_second
        self._base_interval = base_interval
        self._max_interval = max_interval
        self._current_interval = base_interval
        
        # Request timestamps for sliding window
        self._request_times: deque = deque(maxlen=requests_per_second)
        self._lock = asyncio.Lock()
        
        # Backoff state
        self._consecutive_429s = 0
        self._last_request_time = 0.0
    
    async def acquire(self) -> None:
        """
        Acquire permission to make a request.
        
        Enforces rate limit and applies current interval.
        """
        async with self._lock:
            current_time = time.time()
            
            # Clean old timestamps (older than 1 second)
            while self._request_times and current_time - self._request_times[0] > 1.0:
                self._request_times.popleft()
            
            # Wait if at limit
            if len(self._request_times) >= self._requests_per_second:
                wait_time = 1.0 - (current_time - self._request_times[0])
                if wait_time > 0:
                    await asyncio.sleep(wait_time)
            
            # Apply current interval
            time_since_last = current_time - self._last_request_time
            if time_since_last < self._current_interval:
                await asyncio.sleep(self._current_interval - time_since_last)
            
            # Record request
            self._request_times.append(time.time())
            self._last_request_time = time.time()
    
    def on_rate_limit(self, retry_after: int = 0) -> None:
        """
        Handle rate limit response.
        
        Increases interval using exponential backoff.
        """
        self._consecutive_429s += 1
        
        # Exponential backoff
        new_interval = min(
            self._max_interval,
            self._base_interval * (2 ** self._consecutive_429s)
        )
        
        self._current_interval = max(new_interval, float(retry_after))
        
        logger.warning(
            f"Rate limited. Interval increased to {self._current_interval:.2f}s "
            f"(429 count: {self._consecutive_429s})"
        )
    
    def on_success(self) -> None:
        """
        Handle successful response.
        
        Gradually decreases interval back to base.
        """
        if self._consecutive_429s > 0:
            self._consecutive_429s = max(0, self._consecutive_429s - 1)
            
            if self._consecutive_429s == 0:
                self._current_interval = self._base_interval
            else:
                self._current_interval = min(
                    self._current_interval,
                    self._base_interval * (2 ** self._consecutive_429s)
                )
    
    @property
    def current_interval(self) -> float:
        """Get current polling interval."""
        return self._current_interval
    
    def reset(self) -> None:
        """Reset to base state."""
        self._consecutive_429s = 0
        self._current_interval = self._base_interval
        self._request_times.clear()
