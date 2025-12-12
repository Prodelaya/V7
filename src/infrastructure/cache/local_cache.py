"""Local in-memory cache with LRU eviction."""

import asyncio
import time
from typing import Any, Dict, Optional


class LocalCache:
    """
    Local in-memory cache with LRU eviction.
    
    Used as a layer before Redis to reduce network calls.
    Thread-safe with asyncio lock.
    """
    
    def __init__(
        self,
        max_size: int = 1000,
        cleanup_interval: int = 300,
    ):
        self._max_size = max_size
        self._cleanup_interval = cleanup_interval
        
        self._cache: Dict[str, Any] = {}
        self._access_times: Dict[str, float] = {}
        self._lock = asyncio.Lock()
        
        self._cleanup_task: Optional[asyncio.Task] = None
        self._last_cleanup = time.time()
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Updates access time for LRU tracking.
        """
        if key in self._cache:
            self._access_times[key] = time.time()
            return self._cache[key]
        return None
    
    async def set(self, key: str, value: Any) -> None:
        """Set value in cache with LRU eviction."""
        async with self._lock:
            current_time = time.time()
            
            self._cache[key] = value
            self._access_times[key] = current_time
            
            # Start cleanup task if not running
            if not self._cleanup_task or self._cleanup_task.done():
                self._cleanup_task = asyncio.create_task(self._auto_cleanup())
            
            # Evict if over size
            if len(self._cache) > self._max_size:
                await self._evict(int(self._max_size * 0.2))
    
    async def delete(self, key: str) -> None:
        """Remove key from cache."""
        async with self._lock:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    async def clear(self) -> None:
        """Clear all cache entries."""
        async with self._lock:
            self._cache.clear()
            self._access_times.clear()
    
    async def _evict(self, count: int) -> None:
        """Evict least recently used entries."""
        if not self._access_times:
            return
        
        # Sort by access time (oldest first)
        entries = sorted(self._access_times.items(), key=lambda x: x[1])
        to_remove = entries[:count]
        
        for key, _ in to_remove:
            self._cache.pop(key, None)
            self._access_times.pop(key, None)
    
    async def _auto_cleanup(self) -> None:
        """Periodic cleanup task."""
        while True:
            try:
                await asyncio.sleep(60)
                
                current_time = time.time()
                if current_time - self._last_cleanup >= self._cleanup_interval:
                    async with self._lock:
                        if len(self._cache) > self._max_size * 0.9:
                            await self._evict(int(self._max_size * 0.1))
                    self._last_cleanup = current_time
                    
            except asyncio.CancelledError:
                break
            except Exception:
                await asyncio.sleep(60)
    
    @property
    def size(self) -> int:
        """Current cache size."""
        return len(self._cache)
    
    async def cleanup(self) -> None:
        """Stop cleanup task and clear cache."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        await self.clear()
