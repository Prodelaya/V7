"""Integration tests for Redis repository.

These tests require a running Redis instance.
Skip if Redis is not available.
"""

import pytest
import asyncio
from typing import AsyncGenerator

try:
    from redis import asyncio as aioredis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

from src.infrastructure.repositories.redis_repository import RedisRepository


@pytest.fixture
async def redis_repository() -> AsyncGenerator[RedisRepository, None]:
    """Create Redis repository for testing."""
    repo = RedisRepository(
        host="localhost",
        port=6379,
        password="",
        db=15,  # Use test database
    )
    yield repo
    await repo.close()


@pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not available")
class TestRedisRepository:
    """Integration tests for RedisRepository."""
    
    @pytest.mark.asyncio
    async def test_set_and_exists(self, redis_repository):
        """Test setting and checking existence."""
        key = "test:pick:123"
        
        success = await redis_repository.set(key, "1", ttl=60)
        exists = await redis_repository.exists(key)
        
        assert success is True
        assert exists is True
        
        # Cleanup
        await redis_repository.delete(key)
    
    @pytest.mark.asyncio
    async def test_exists_not_found(self, redis_repository):
        """Test exists returns false for missing key."""
        exists = await redis_repository.exists("nonexistent:key:999")
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_exists_any_some_exist(self, redis_repository):
        """Test exists_any when some keys exist."""
        key1 = "test:pick:1"
        await redis_repository.set(key1, "1", ttl=60)
        
        keys = [key1, "nonexistent:1", "nonexistent:2"]
        exists = await redis_repository.exists_any(keys)
        
        assert exists is True
        
        # Cleanup
        await redis_repository.delete(key1)
    
    @pytest.mark.asyncio
    async def test_exists_any_none_exist(self, redis_repository):
        """Test exists_any when no keys exist."""
        keys = ["nonexistent:1", "nonexistent:2", "nonexistent:3"]
        
        exists = await redis_repository.exists_any(keys)
        
        assert exists is False
    
    @pytest.mark.asyncio
    async def test_cursor_persistence(self, redis_repository):
        """Test cursor save and retrieve."""
        cursor = "created_at:12345"
        
        await redis_repository.set_cursor(cursor)
        retrieved = await redis_repository.get_cursor()
        
        assert retrieved == cursor
