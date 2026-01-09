"""Local in-memory cache.

Implementation Requirements:
- LRU eviction when max size reached
- Optional TTL per entry
- Thread-safe for async usage
- First-level cache before Redis

Reference:
- docs/05-Implementation.md: Task 5C.5
- docs/02-PDR.md: Section 3.3.4 (Local Cache)
- docs/03-ADRs.md: ADR-011 (Cache HTML)
"""

import asyncio
import time
from collections import OrderedDict
from typing import Any, Optional


class LocalCache:
    """
    In-memory cache with LRU eviction and TTL support.

    Used as first-level cache before Redis to reduce
    network round trips.

    Features:
    - Max size with LRU eviction (O(1) using OrderedDict)
    - Optional TTL per entry
    - Async-safe with asyncio.Lock

    Example:
        >>> cache = LocalCache(max_size=1000, default_ttl=60)
        >>> await cache.set("key", "value")
        >>> cache.get("key")
        'value'
        >>> cache.exists("key")
        True
    """

    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        Initialize cache.

        Args:
            max_size: Maximum entries before eviction
            default_ttl: Default TTL in seconds (None = no expiry)
        """
        self._max_size = max_size
        self._default_ttl = default_ttl
        self._cache: OrderedDict[str, Any] = OrderedDict()
        self._expiry_times: dict[str, float] = {}
        self._lock = asyncio.Lock()

    def get(self, key: str) -> Optional[Any]:
        """
        Get value by key.

        Returns None if not found or expired.
        Updates access time for LRU.

        Args:
            key: Cache key

        Returns:
            Cached value or None
        """
        if key not in self._cache:
            return None

        # Check TTL expiration
        if key in self._expiry_times:
            if time.time() > self._expiry_times[key]:
                # Expired - remove and return None
                self._cache.pop(key, None)
                self._expiry_times.pop(key, None)
                return None

        # Update LRU order (move to end = most recently used)
        self._cache.move_to_end(key)
        return self._cache[key]

    def exists(self, key: str) -> bool:
        """
        Check if key exists and is not expired.

        Convenience method for boolean existence checks.

        Args:
            key: Cache key

        Returns:
            True if key exists and is valid
        """
        return self.get(key) is not None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value with optional TTL.

        Evicts LRU entries if at max size.

        Args:
            key: Cache key
            value: Value to cache
            ttl: TTL in seconds (None = use default)
        """
        async with self._lock:
            # Evict oldest if at capacity and key is new
            if len(self._cache) >= self._max_size and key not in self._cache:
                # Remove oldest (first item in OrderedDict)
                oldest_key, _ = self._cache.popitem(last=False)
                self._expiry_times.pop(oldest_key, None)

            # Set value
            self._cache[key] = value
            self._cache.move_to_end(key)

            # Calculate expiry time
            effective_ttl = ttl if ttl is not None else self._default_ttl
            if effective_ttl is not None:
                self._expiry_times[key] = time.time() + effective_ttl
            elif key in self._expiry_times:
                # Remove old expiry if setting without TTL
                del self._expiry_times[key]

    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.

        Args:
            key: Cache key

        Returns:
            True if key existed
        """
        async with self._lock:
            existed = key in self._cache
            self._cache.pop(key, None)
            self._expiry_times.pop(key, None)
            return existed

    async def clear(self) -> None:
        """Clear all entries."""
        async with self._lock:
            self._cache.clear()
            self._expiry_times.clear()

    async def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        async with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, expiry in self._expiry_times.items()
                if current_time > expiry
            ]

            for key in expired_keys:
                self._cache.pop(key, None)
                self._expiry_times.pop(key, None)

            return len(expired_keys)

    def __len__(self) -> int:
        """Current cache size."""
        return len(self._cache)

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"LocalCache(max_size={self._max_size}, "
            f"default_ttl={self._default_ttl}, "
            f"current_size={len(self._cache)})"
        )
