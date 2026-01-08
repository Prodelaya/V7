"""Redis repository for pick deduplication - NO Bloom Filter.

Implementation following ADRs:
- ADR-004: Pipeline batch operations for efficiency
- ADR-009: Cursor persistence for API recovery
- ADR-012: NO Bloom Filter (false positives lose picks)
- ADR-013: NO fire-and-forget (always await confirmation)

Reference:
- docs/05-Implementation.md: Task 5A.2
- docs/02-PDR.md: Section 3.3.4 (Redis Repository)
- docs/03-ADRs.md: ADR-004, ADR-012, ADR-013
- docs/01-SRS.md: RF-004
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple

import redis.asyncio as aioredis
from redis.asyncio import ConnectionPool
from redis.exceptions import RedisError

from .base import BaseRepository

if TYPE_CHECKING:
    from src.config.settings import RedisSettings
    from src.domain.entities.pick import Pick


logger = logging.getLogger(__name__)


class _SimpleLocalCache:
    """Simple LRU cache with TTL for first-level caching before Redis.

    Used to reduce Redis round-trips for frequently accessed keys.
    Thread-safe for async usage via simple dict operations.

    This is a simplified inline implementation as a workaround
    for the unimplemented LocalCache class.
    """

    def __init__(self, max_size: int = 2000, default_ttl: int = 300) -> None:
        """Initialize the cache.

        Args:
            max_size: Maximum number of entries before LRU eviction.
            default_ttl: Default time-to-live in seconds.
        """
        self._cache: OrderedDict[str, bool] = OrderedDict()
        self._expiry: Dict[str, float] = {}
        self._max_size = max_size
        self._default_ttl = default_ttl

    def get(self, key: str) -> bool:
        """Check if key exists and is not expired.

        Args:
            key: Cache key to check.

        Returns:
            True if key exists and not expired, False otherwise.
        """
        if key not in self._cache:
            return False

        # Check expiry
        if time.time() > self._expiry.get(key, float("inf")):
            # Expired, remove it
            self._cache.pop(key, None)
            self._expiry.pop(key, None)
            return False

        # Move to end for LRU
        self._cache.move_to_end(key)
        return True

    def set(self, key: str, ttl: Optional[int] = None) -> None:
        """Mark key as existing with optional TTL.

        Args:
            key: Cache key to set.
            ttl: Time-to-live in seconds (uses default if None).
        """
        # Evict oldest if at capacity
        if len(self._cache) >= self._max_size and key not in self._cache:
            self._cache.popitem(last=False)
            # Also clean up expiry for evicted key
            oldest_key = next(iter(self._expiry), None)
            if oldest_key:
                self._expiry.pop(oldest_key, None)

        self._cache[key] = True
        self._cache.move_to_end(key)

        effective_ttl = ttl if ttl is not None else self._default_ttl
        self._expiry[key] = time.time() + effective_ttl

    def delete(self, key: str) -> None:
        """Remove key from cache.

        Args:
            key: Cache key to remove.
        """
        self._cache.pop(key, None)
        self._expiry.pop(key, None)

    def clear(self) -> None:
        """Clear all entries."""
        self._cache.clear()
        self._expiry.clear()

    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)


class RedisRepository(BaseRepository):
    """Redis-based repository for pick deduplication.

    Features:
    - Pipeline batch operations for efficiency (ADR-004)
    - Local cache first-level cache to reduce Redis calls
    - TTL = time until event starts
    - Cursor persistence for API recovery (ADR-009)

    ⚠️ NO Bloom Filter (from ADR-012):
        1% false positives = lost picks = lost money

    ⚠️ NO fire-and-forget (from ADR-013):
        Race conditions cause duplicates

    Example:
        >>> repo = RedisRepository(host="localhost", port=6379)
        >>> await repo.set("pick:key", "1234567890", ttl=3600)
        True
        >>> await repo.exists("pick:key")
        True
    """

    # Key for persisting API cursor (ADR-009)
    CURSOR_KEY = "retador:api:cursor"

    # Default timeout for Redis operations (ADR-013)
    OPERATION_TIMEOUT = 0.5  # 500ms max per operation

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        username: Optional[str] = None,
        max_connections: int = 500,
        local_cache_size: int = 2000,
        socket_timeout: float = 5.0,
        retry_on_timeout: bool = True,
    ) -> None:
        """Initialize Redis repository.

        Args:
            host: Redis server hostname.
            port: Redis server port.
            password: Redis password (None if not required).
            db: Redis database number (0-15).
            username: Redis username for ACL (Redis 6+).
            max_connections: Connection pool size.
            local_cache_size: Local cache max entries.
            socket_timeout: Socket timeout in seconds.
            retry_on_timeout: Whether to retry on timeout.
        """
        self._host = host
        self._port = port
        self._password = password
        self._db = db
        self._username = username
        self._max_connections = max_connections
        self._socket_timeout = socket_timeout
        self._retry_on_timeout = retry_on_timeout

        # Lazy initialization
        self._pool: Optional[ConnectionPool] = None
        self._redis: Optional[aioredis.Redis] = None

        # Local cache for reducing Redis round-trips
        self._local_cache = _SimpleLocalCache(max_size=local_cache_size)

        logger.info(
            f"RedisRepository initialized: {host}:{port}/db{db} "
            f"(pool={max_connections}, cache={local_cache_size})"
        )

    async def _get_client(self) -> aioredis.Redis:
        """Get Redis client with lazy initialization.

        Creates connection pool and client on first call.
        Subsequent calls return the same client.

        Returns:
            Redis async client.

        Raises:
            RedisError: If connection fails.
        """
        if self._redis is not None:
            return self._redis

        # Create connection pool
        self._pool = ConnectionPool(
            host=self._host,
            port=self._port,
            db=self._db,
            password=self._password,
            username=self._username,
            max_connections=self._max_connections,
            socket_timeout=self._socket_timeout,
            retry_on_timeout=self._retry_on_timeout,
            decode_responses=True,
        )

        # Create client from pool
        self._redis = aioredis.Redis(connection_pool=self._pool)

        # Test connection
        try:
            await self._redis.ping()
            logger.info("Redis connection established successfully")
        except RedisError as e:
            logger.error(f"Failed to connect to Redis: {e}")
            raise

        return self._redis

    async def exists(self, key: str) -> bool:
        """Check if key exists (cache first, then Redis).

        Checks local cache first to avoid Redis round-trip.
        If not in cache but found in Redis, updates cache.

        Args:
            key: Redis key to check.

        Returns:
            True if key exists.
        """
        # Check local cache first
        if self._local_cache.get(key):
            return True

        # Check Redis
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                result = await client.exists(key)

                if result:
                    # Update local cache if exists in Redis
                    self._local_cache.set(key)

                return bool(result)

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout checking EXISTS {key}")
            return False
        except RedisError as e:
            logger.error(f"Redis error checking EXISTS {key}: {e}")
            return False

    async def exists_any(self, keys: List[str]) -> bool:
        """Check if any of the keys exist using pipeline.

        Uses pipeline for batch efficiency (ADR-004).

        Args:
            keys: List of keys to check.

        Returns:
            True if any key exists.
        """
        if not keys:
            return False

        # Check local cache first
        for key in keys:
            if self._local_cache.get(key):
                return True

        # Check Redis with pipeline
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()

                async with client.pipeline(transaction=False) as pipe:
                    for key in keys:
                        pipe.exists(key)
                    results = await pipe.execute()

                # Update cache for any found keys
                for key, exists in zip(keys, results, strict=True):
                    if exists:
                        self._local_cache.set(key)
                        return True

                return False

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout checking EXISTS_ANY for {len(keys)} keys")
            return False
        except RedisError as e:
            logger.error(f"Redis error checking EXISTS_ANY: {e}")
            return False

    async def exists_batch(self, keys: List[str]) -> Dict[str, bool]:
        """Check multiple keys existence using pipeline.

        More efficient than multiple exists() calls for batch operations.
        Uses pipeline to reduce round-trips to Redis (ADR-004).

        Args:
            keys: List of keys to check.

        Returns:
            Dict mapping each key to its existence status.
        """
        if not keys:
            return {}

        results: Dict[str, bool] = {}
        keys_to_check: List[str] = []

        # Check local cache first
        for key in keys:
            if self._local_cache.get(key):
                results[key] = True
            else:
                keys_to_check.append(key)

        if not keys_to_check:
            return results

        # Check remaining keys in Redis with pipeline
        redis_results = await self._check_keys_in_redis(keys_to_check)

        for key, exists in zip(keys_to_check, redis_results, strict=True):
            exists_bool = bool(exists)
            results[key] = exists_bool
            if exists_bool:
                self._local_cache.set(key)

        return results

    async def _check_keys_in_redis(self, keys: List[str]) -> List[bool]:
        """Check keys in Redis using pipeline (helper for exists_batch).

        Args:
            keys: Keys to check.

        Returns:
            List of existence booleans, False for each key on error.
        """
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                async with client.pipeline(transaction=False) as pipe:
                    for key in keys:
                        pipe.exists(key)
                    return await pipe.execute()  # type: ignore[return-value]
        except asyncio.TimeoutError:
            logger.warning(
                f"Redis timeout checking EXISTS_BATCH for {len(keys)} keys"
            )
            return [False] * len(keys)
        except RedisError as e:
            logger.error(f"Redis error checking EXISTS_BATCH: {e}")
            return [False] * len(keys)

    async def set(self, key: str, value: str, ttl: int) -> bool:
        """Set key with TTL (MUST await - no fire-and-forget).

        Always awaits confirmation per ADR-013 to prevent race conditions.

        Args:
            key: Redis key.
            value: Value to store.
            ttl: Time-to-live in seconds.

        Returns:
            True if successful.
        """
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                await client.setex(key, ttl, value)

                # Update local cache
                self._local_cache.set(key, ttl)

                return True

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout for SET {key}")
            return False
        except RedisError as e:
            logger.error(f"Redis error for SET {key}: {e}")
            return False

    async def set_batch(self, items: List[Tuple[str, str, int]]) -> bool:
        """Set multiple keys atomically with TTLs using pipeline.

        MUST await confirmation - no fire-and-forget (ADR-013).
        Uses transaction for atomicity.

        Args:
            items: List of (key, value, ttl_seconds) tuples.

        Returns:
            True if all operations successful.
        """
        if not items:
            return True

        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()

                async with client.pipeline(transaction=True) as pipe:
                    for key, value, ttl in items:
                        pipe.setex(key, ttl, value)
                    await pipe.execute()

                # Update local cache for all items
                for key, _, ttl in items:
                    self._local_cache.set(key, ttl)

                return True

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout for SET_BATCH ({len(items)} items)")
            return False
        except RedisError as e:
            logger.error(f"Redis error for SET_BATCH: {e}")
            return False

    async def get(self, key: str) -> Optional[str]:
        """Get value by key.

        Args:
            key: Redis key.

        Returns:
            Value if exists, None otherwise.
        """
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                result = await client.get(key)
                return result  # type: ignore[return-value]

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout for GET {key}")
            return None
        except RedisError as e:
            logger.error(f"Redis error for GET {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """Delete key.

        Args:
            key: Redis key.

        Returns:
            True if key was deleted (existed).
        """
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                result = await client.delete(key)

                # Remove from local cache
                self._local_cache.delete(key)

                return bool(result)

        except asyncio.TimeoutError:
            logger.warning(f"Redis timeout for DELETE {key}")
            return False
        except RedisError as e:
            logger.error(f"Redis error for DELETE {key}: {e}")
            return False

    async def save_with_opposites(self, pick: "Pick", ttl: int) -> bool:
        """Save pick key AND opposite market keys to prevent rebotes.

        When a pick is sent (e.g., OVER 2.5), we also mark its
        opposite markets (UNDER 2.5) as "sent" to prevent sending
        both sides of the same bet (RF-004).

        Args:
            pick: Pick entity with redis_key and get_opposite_keys().
            ttl: Time-to-live in seconds (typically until event starts).

        Returns:
            True if all keys saved successfully.

        Example:
            For a pick "Team1 vs Team2 OVER 2.5", this saves:
            - Team1:Team2:timestamp:over:2.5:bookie (original)
            - Team1:Team2:timestamp:under:2.5:bookie (opposite)
        """
        # Get all keys to save
        main_key = pick.redis_key
        opposite_keys = pick.get_opposite_keys()

        # Prepare items for batch save
        timestamp_value = str(time.time())
        items: List[Tuple[str, str, int]] = [(main_key, timestamp_value, ttl)]

        for opp_key in opposite_keys:
            items.append((opp_key, timestamp_value, ttl))

        # Save all keys atomically
        success = await self.set_batch(items)

        if success:
            logger.debug(
                f"Saved pick with {len(opposite_keys)} opposites: "
                f"{main_key[:50]}..."
            )
        else:
            logger.warning(f"Failed to save pick with opposites: {main_key[:50]}...")

        return success

    async def get_cursor(self) -> Optional[str]:
        """Get persisted API cursor for incremental fetch.

        The cursor allows resuming API polling from where we left off,
        avoiding re-processing already seen picks after restarts (ADR-009).

        Returns:
            Cursor string (format: "sort_by:id") or None if not set.
        """
        return await self.get(self.CURSOR_KEY)

    async def set_cursor(self, cursor: str) -> bool:
        """Persist API cursor for recovery after restarts.

        The cursor is stored without TTL (persistent).

        Args:
            cursor: Cursor string (format: "sort_by:id").

        Returns:
            True if saved successfully.
        """
        try:
            async with asyncio.timeout(self.OPERATION_TIMEOUT):
                client = await self._get_client()
                # No TTL - cursor should persist forever
                await client.set(self.CURSOR_KEY, cursor)
                return True

        except asyncio.TimeoutError:
            logger.warning("Redis timeout for SET_CURSOR")
            return False
        except RedisError as e:
            logger.error(f"Redis error for SET_CURSOR: {e}")
            return False

    async def close(self) -> None:
        """Close Redis connection and cleanup resources."""
        # Clear local cache
        self._local_cache.clear()

        # Close Redis connection
        if self._redis is not None:
            try:
                await self._redis.close()
                logger.info("Redis connection closed")
            except RedisError as e:
                logger.warning(f"Error closing Redis connection: {e}")
            finally:
                self._redis = None

        # Close connection pool
        if self._pool is not None:
            try:
                await self._pool.disconnect()
            except Exception as e:
                logger.warning(f"Error disconnecting pool: {e}")
            finally:
                self._pool = None

    @classmethod
    async def from_settings(cls, settings: "RedisSettings") -> "RedisRepository":
        """Factory method to create repository from RedisSettings.

        Args:
            settings: RedisSettings from config.

        Returns:
            Initialized and connected RedisRepository.

        Example:
            >>> from src.config.settings import Settings
            >>> settings = Settings()
            >>> repo = await RedisRepository.from_settings(settings.redis)
        """
        repo = cls(
            host=settings.host,
            port=settings.port,
            password=settings.password or None,
            db=settings.db,
            username=settings.username or None,
            max_connections=settings.max_connections,
        )

        # Initialize connection to verify it works
        await repo._get_client()

        return repo

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"RedisRepository(host={self._host!r}, port={self._port}, "
            f"db={self._db}, cache_size={len(self._local_cache)})"
        )
