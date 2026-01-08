"""Base repository abstract class for Repository Pattern (ADR-004).

Defines the interface for data persistence and deduplication.
All methods are async to support I/O operations (Redis, PostgreSQL).

Design Decisions:
- NO Bloom Filter (ADR-012: false positives lose picks)
- NO fire-and-forget (ADR-013: race conditions cause duplicates)
- Pipeline batch operations for efficiency (ADR-004)
- Cursor persistence for API recovery (ADR-009)

Reference:
- docs/05-Implementation.md: Task 5A.1
- docs/02-PDR.md: Section 4.3 (Repository Pattern), Section 6.1 (Interface)
- docs/03-ADRs.md: ADR-004, ADR-009, ADR-012, ADR-013
"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from src.domain.entities.pick import Pick


class BaseRepository(ABC):
    """
    Abstract base class for data repositories.

    Defines the interface for pick persistence and deduplication.
    Implementations include RedisRepository (primary) and future
    PostgresRepository (historical data).

    Key Responsibilities:
    - Key existence checks (single and batch)
    - Key-value storage with TTL
    - Pick-specific storage with opposite markets
    - API cursor persistence for incremental fetch

    Example:
        >>> class RedisRepository(BaseRepository):
        ...     async def exists(self, key: str) -> bool:
        ...         return await self.redis.exists(key)

    Reference:
        - PDR Section 4.3, 6.1 in docs/02-PDR.md
        - ADR-004, ADR-009 in docs/03-ADRs.md
    """

    @abstractmethod
    async def exists(self, key: str) -> bool:
        """
        Check if key exists.

        Args:
            key: Unique key to check

        Returns:
            True if key exists
        """
        pass

    @abstractmethod
    async def exists_any(self, keys: List[str]) -> bool:
        """
        Check if any of the keys exist.

        Args:
            keys: List of keys to check

        Returns:
            True if any key exists

        Note:
            Use pipeline for efficiency (ADR-004)
        """
        pass

    @abstractmethod
    async def set(self, key: str, value: str, ttl: int) -> bool:
        """
        Set key with TTL.

        Args:
            key: Unique key
            value: Value to store
            ttl: Time-to-live in seconds

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    async def get(self, key: str) -> Optional[str]:
        """
        Get value by key.

        Args:
            key: Unique key

        Returns:
            Value if exists, None otherwise
        """
        pass

    @abstractmethod
    async def delete(self, key: str) -> bool:
        """
        Delete key.

        Args:
            key: Unique key

        Returns:
            True if deleted
        """
        pass

    @abstractmethod
    async def exists_batch(self, keys: List[str]) -> Dict[str, bool]:
        """
        Check multiple keys existence using pipeline.

        More efficient than multiple exists() calls for batch operations.
        Uses pipeline to reduce round-trips to storage.

        Args:
            keys: List of keys to check

        Returns:
            Dict mapping each key to its existence status

        Reference:
            - ADR-004 in docs/03-ADRs.md (pipeline batch)
        """
        pass

    @abstractmethod
    async def set_batch(
        self, items: List[Tuple[str, str, int]]
    ) -> bool:
        """
        Set multiple keys atomically with TTLs.

        MUST await confirmation - no fire-and-forget (ADR-013).

        Args:
            items: List of (key, value, ttl_seconds) tuples

        Returns:
            True if all operations successful

        Reference:
            - ADR-013 in docs/03-ADRs.md (no fire-and-forget)
        """
        pass

    @abstractmethod
    async def save_with_opposites(
        self, pick: "Pick", ttl: int
    ) -> bool:
        """
        Save pick key AND opposite market keys to prevent rebotes.

        When a pick is sent (e.g., OVER 2.5), we also mark its
        opposite markets (UNDER 2.5) as "sent" to prevent sending
        both sides of the same bet.

        Args:
            pick: Pick entity with redis_key and get_opposite_keys()
            ttl: Time-to-live in seconds (typically until event starts)

        Returns:
            True if all keys saved successfully

        Reference:
            - RF-004 in docs/01-SRS.md (deduplication)
            - Appendix 6.1 in docs/01-SRS.md (opposite markets)
        """
        pass

    @abstractmethod
    async def get_cursor(self) -> Optional[str]:
        """
        Get persisted API cursor for incremental fetch.

        The cursor allows resuming API polling from where we left off,
        avoiding re-processing already seen picks after restarts.

        Returns:
            Cursor string (format: "sort_by:id") or None if not set

        Reference:
            - ADR-009 in docs/03-ADRs.md (cursor incremental)
        """
        pass

    @abstractmethod
    async def set_cursor(self, cursor: str) -> bool:
        """
        Persist API cursor for recovery after restarts.

        Args:
            cursor: Cursor string (format: "sort_by:id")

        Returns:
            True if saved successfully

        Reference:
            - ADR-009 in docs/03-ADRs.md (cursor incremental)
        """
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection."""
        pass
