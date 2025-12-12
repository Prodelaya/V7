"""Cache package - Local in-memory cache.

Contains:
- local_cache: LRU cache with TTL

Reference: docs/05-Implementation.md Task 5.10
"""

from .local_cache import LocalCache

__all__ = ["LocalCache"]
