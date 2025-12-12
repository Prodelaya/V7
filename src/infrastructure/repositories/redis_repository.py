"""Redis repository for pick deduplication - NO Bloom Filter."""

import asyncio
import logging
import time
from typing import List, Optional

from redis import asyncio as aioredis

from .base import BaseRepository
from ..cache.local_cache import LocalCache


logger = logging.getLogger(__name__)


class RedisRepository(BaseRepository):
    """
    Redis-based repository for pick deduplication.
    
    Features:
    - Pipeline batch operations for efficiency
    - Local cache layer to reduce Redis calls
    - TTL based on event time
    
    NOTE: Does NOT use Bloom Filter to avoid false positives
    which would cause valid picks to be missed.
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        username: Optional[str] = None,
        max_connections: int = 500,
        local_cache_size: int = 2000,
    ):
        self._pool = aioredis.ConnectionPool(
            host=host,
            port=port,
            db=db,
            password=password,
            decode_responses=True,
            max_connections=max_connections,
            socket_timeout=5,
            retry_on_timeout=True,
        )
        
        self._redis = aioredis.Redis(
            connection_pool=self._pool,
            username=username,
            decode_responses=True,
            retry_on_timeout=True,
        )
        
        self._local_cache = LocalCache(max_size=local_cache_size)
        self._lock = asyncio.Lock()
    
    async def exists(self, key: str) -> bool:
        """Check if key exists (cache first, then Redis)."""
        # Check local cache first
        if self._local_cache.get(key):
            return True
        
        # Check Redis
        try:
            exists = await self._redis.exists(key)
            if exists:
                await self._local_cache.set(key, True)
            return bool(exists)
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    async def exists_any(self, keys: List[str]) -> bool:
        """Check if any key exists using pipeline."""
        if not keys:
            return False
        
        # Check local cache first
        for key in keys:
            if self._local_cache.get(key):
                return True
        
        # Check Redis with pipeline
        try:
            async with self._redis.pipeline(transaction=False) as pipe:
                for key in keys:
                    pipe.exists(key)
                results = await pipe.execute()
            
            for key, exists in zip(keys, results):
                if exists:
                    await self._local_cache.set(key, True)
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Redis exists_any error: {e}")
            return False
    
    async def set(self, key: str, value: str, ttl: int) -> bool:
        """Set key with TTL."""
        try:
            await self._redis.setex(key, ttl, value)
            await self._local_cache.set(key, True)
            return True
        except Exception as e:
            logger.error(f"Redis set error: {e}")
            return False
    
    async def set_batch(
        self, 
        items: List[tuple[str, str, int]]
    ) -> bool:
        """
        Set multiple keys with TTLs using pipeline.
        
        Args:
            items: List of (key, value, ttl) tuples
        """
        try:
            async with self._redis.pipeline(transaction=True) as pipe:
                for key, value, ttl in items:
                    if ttl > 0:
                        pipe.setex(key, ttl, value)
                        await self._local_cache.set(key, True)
                await pipe.execute()
            return True
        except Exception as e:
            logger.error(f"Redis batch set error: {e}")
            return False
    
    async def get(self, key: str) -> Optional[str]:
        """Get value by key."""
        try:
            return await self._redis.get(key)
        except Exception as e:
            logger.error(f"Redis get error: {e}")
            return None
    
    async def delete(self, key: str) -> bool:
        """Delete key."""
        try:
            await self._redis.delete(key)
            return True
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    async def get_cursor(self) -> Optional[str]:
        """Get persisted cursor for recovery."""
        return await self.get("retador:cursor")
    
    async def set_cursor(self, cursor: str) -> bool:
        """Persist cursor for recovery."""
        try:
            await self._redis.set("retador:cursor", cursor)
            return True
        except Exception as e:
            logger.error(f"Redis cursor set error: {e}")
            return False
    
    async def close(self) -> None:
        """Close Redis connection."""
        try:
            await self._redis.close()
            await self._pool.disconnect()
        except Exception as e:
            logger.error(f"Redis close error: {e}")
