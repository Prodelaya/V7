"""Integration tests for Redis repository with real Redis.

Test Requirements:
- Test with real Redis (Testcontainers)
- exists() / exists_any() / exists_batch() behavior
- set() / set_batch() with TTL
- Cursor persistence (ADR-009)
- NO false positives (ADR-012)
- Awaited confirmation (ADR-013)
- save_with_opposites (RF-004)

Reference:
- docs/05-Implementation.md: Task 5A.3
- docs/03-ADRs.md: ADR-004, ADR-009, ADR-012, ADR-013
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone

import pytest

from src.domain.entities.pick import Pick
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.infrastructure.repositories.redis_repository import RedisRepository


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def sample_pick() -> Pick:
    """Create a sample Pick for testing save_with_opposites."""
    return Pick(
        teams=("Team Alpha", "Team Beta"),
        odds=Odds(2.05),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime.now(timezone.utc),
        bookmaker="pinnaclesports",
        tournament="Test League",
        sport_id="Football",
    )


@pytest.fixture
def sample_pick_under() -> Pick:
    """Create a Pick with UNDER market type."""
    return Pick(
        teams=("Team Alpha", "Team Beta"),
        odds=Odds(1.85),
        market_type=MarketType.UNDER,
        variety="2.5",
        event_time=datetime.now(timezone.utc),
        bookmaker="bet365",
        tournament="Test League",
        sport_id="Football",
    )


# ============================================================================
# TestRedisRepositoryCRUD - Basic CRUD operations
# ============================================================================


class TestRedisRepositoryCRUD:
    """Integration tests for basic CRUD operations."""

    @pytest.mark.asyncio
    async def test_set_and_exists(self, redis_repo: RedisRepository):
        """set() should make exists() return True."""
        await redis_repo.set("test:key", "value", ttl=60)
        assert await redis_repo.exists("test:key")

    @pytest.mark.asyncio
    async def test_nonexistent_key_returns_false(self, redis_repo: RedisRepository):
        """exists() should return False for missing key."""
        assert not await redis_repo.exists("nonexistent:key:xyz")

    @pytest.mark.asyncio
    async def test_get_returns_value(self, redis_repo: RedisRepository):
        """get() should retrieve stored value."""
        await redis_repo.set("test:get", "my_value", ttl=60)
        result = await redis_repo.get("test:get")
        assert result == "my_value"

    @pytest.mark.asyncio
    async def test_get_nonexistent_returns_none(self, redis_repo: RedisRepository):
        """get() should return None for missing key."""
        result = await redis_repo.get("nonexistent:get:xyz")
        assert result is None

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, redis_repo: RedisRepository):
        """delete() should remove key."""
        await redis_repo.set("test:delete", "value", ttl=60)
        assert await redis_repo.exists("test:delete")

        result = await redis_repo.delete("test:delete")
        assert result is True
        assert not await redis_repo.exists("test:delete")


# ============================================================================
# TestRedisRepositoryBatch - Batch operations (ADR-004)
# ============================================================================


class TestRedisRepositoryBatch:
    """Integration tests for batch operations using pipeline (ADR-004)."""

    @pytest.mark.asyncio
    async def test_exists_any_with_one_match(self, redis_repo: RedisRepository):
        """exists_any() should return True if any key matches."""
        await redis_repo.set("test:exists_any", "value", ttl=60)
        keys = ["test:missing1", "test:exists_any", "test:missing2"]
        assert await redis_repo.exists_any(keys)

    @pytest.mark.asyncio
    async def test_exists_any_with_no_match(self, redis_repo: RedisRepository):
        """exists_any() should return False if no key matches."""
        keys = ["test:missing_a", "test:missing_b", "test:missing_c"]
        assert not await redis_repo.exists_any(keys)

    @pytest.mark.asyncio
    async def test_exists_any_empty_list(self, redis_repo: RedisRepository):
        """exists_any() should return False for empty key list."""
        assert not await redis_repo.exists_any([])

    @pytest.mark.asyncio
    async def test_exists_batch_returns_dict(self, redis_repo: RedisRepository):
        """exists_batch() should return Dict mapping each key to status."""
        await redis_repo.set("test:batch1", "v1", ttl=60)
        await redis_repo.set("test:batch3", "v3", ttl=60)

        keys = ["test:batch1", "test:batch2", "test:batch3"]
        result = await redis_repo.exists_batch(keys)

        assert result == {
            "test:batch1": True,
            "test:batch2": False,
            "test:batch3": True,
        }

    @pytest.mark.asyncio
    async def test_set_batch_sets_all(self, redis_repo: RedisRepository):
        """set_batch() should set multiple keys atomically."""
        items = [
            ("test:setbatch1", "v1", 60),
            ("test:setbatch2", "v2", 60),
            ("test:setbatch3", "v3", 60),
        ]
        result = await redis_repo.set_batch(items)
        assert result is True

        # Verify all keys were set
        assert await redis_repo.exists("test:setbatch1")
        assert await redis_repo.exists("test:setbatch2")
        assert await redis_repo.exists("test:setbatch3")

        # Verify values
        assert await redis_repo.get("test:setbatch1") == "v1"
        assert await redis_repo.get("test:setbatch2") == "v2"


# ============================================================================
# TestRedisRepositoryTTL - TTL expiration
# ============================================================================


class TestRedisRepositoryTTL:
    """Integration tests for TTL expiration."""

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, redis_repo: RedisRepository):
        """Key should expire after TTL."""
        await redis_repo.set("test:ttl", "value", ttl=1)
        assert await redis_repo.exists("test:ttl")

        # Wait for expiration
        await asyncio.sleep(1.5)

        assert not await redis_repo.exists("test:ttl")

    @pytest.mark.asyncio
    async def test_ttl_with_set_batch(self, redis_repo: RedisRepository):
        """set_batch() TTL should work correctly."""
        items = [
            ("test:ttl_batch1", "v1", 1),
            ("test:ttl_batch2", "v2", 1),
        ]
        await redis_repo.set_batch(items)

        assert await redis_repo.exists("test:ttl_batch1")

        # Wait for expiration
        await asyncio.sleep(1.5)

        assert not await redis_repo.exists("test:ttl_batch1")
        assert not await redis_repo.exists("test:ttl_batch2")


# ============================================================================
# TestRedisRepositoryCursor - Cursor persistence (ADR-009)
# ============================================================================


class TestRedisRepositoryCursor:
    """Integration tests for cursor persistence (ADR-009)."""

    @pytest.mark.asyncio
    async def test_cursor_set_and_get(self, redis_repo: RedisRepository):
        """Cursor should persist and be retrievable."""
        cursor = "created_at:12345"
        result = await redis_repo.set_cursor(cursor)
        assert result is True

        retrieved = await redis_repo.get_cursor()
        assert retrieved == cursor

    @pytest.mark.asyncio
    async def test_cursor_no_ttl(self, redis_repo: RedisRepository):
        """Cursor should not expire (no TTL)."""
        cursor = "created_at:67890"
        await redis_repo.set_cursor(cursor)

        # Wait to ensure no TTL applies
        await asyncio.sleep(2)

        retrieved = await redis_repo.get_cursor()
        assert retrieved == cursor

    @pytest.mark.asyncio
    async def test_cursor_survives_reconnection(
        self, redis_container, redis_repo: RedisRepository
    ):
        """Cursor should survive repository restart."""
        cursor = "created_at:99999"
        await redis_repo.set_cursor(cursor)

        # Create new repository instance (simulates restart)
        host = redis_container.get_container_host_ip()
        port = int(redis_container.get_exposed_port(6379))

        new_repo = RedisRepository(
            host=host,
            port=port,
            db=15,
            max_connections=10,
        )

        try:
            retrieved = await new_repo.get_cursor()
            assert retrieved == cursor
        finally:
            await new_repo.close()


# ============================================================================
# TestRedisRepositorySaveWithOpposites - RF-004 compliance
# ============================================================================


class TestRedisRepositorySaveWithOpposites:
    """Integration tests for save_with_opposites (RF-004)."""

    @pytest.mark.asyncio
    async def test_save_with_opposites_main_key(
        self, redis_repo: RedisRepository, sample_pick: Pick
    ):
        """save_with_opposites() should save main pick key."""
        result = await redis_repo.save_with_opposites(sample_pick, ttl=3600)
        assert result is True

        # Main key should exist
        assert await redis_repo.exists(sample_pick.redis_key)

    @pytest.mark.asyncio
    async def test_save_with_opposites_opposite_keys(
        self, redis_repo: RedisRepository, sample_pick: Pick
    ):
        """save_with_opposites() should save opposite market keys."""
        await redis_repo.save_with_opposites(sample_pick, ttl=3600)

        # Opposite keys should exist
        opposite_keys = sample_pick.get_opposite_keys()
        assert len(opposite_keys) >= 1

        for opp_key in opposite_keys:
            assert await redis_repo.exists(opp_key), f"Missing opposite key: {opp_key}"

    @pytest.mark.asyncio
    async def test_save_with_opposites_over_under(
        self, redis_repo: RedisRepository, sample_pick: Pick
    ):
        """OVER pick should save UNDER opposite and vice versa."""
        # Verify the pick is OVER
        assert sample_pick.market_type == MarketType.OVER

        await redis_repo.save_with_opposites(sample_pick, ttl=3600)

        # Get opposite keys
        opposite_keys = sample_pick.get_opposite_keys()

        # At least one opposite should contain "under"
        has_under = any("under" in key.lower() for key in opposite_keys)
        assert has_under, f"Expected UNDER opposite, got: {opposite_keys}"


# ============================================================================
# TestRedisRepositoryNoFalsePositives - ADR-012 compliance
# ============================================================================


class TestRedisRepositoryNoFalsePositives:
    """Integration tests verifying NO false positives (ADR-012)."""

    @pytest.mark.asyncio
    async def test_no_false_positives_similar_prefix(
        self, redis_repo: RedisRepository
    ):
        """Similar key with different suffix should NOT match."""
        await redis_repo.set("test:exact:key:123", "value", ttl=60)

        # Similar but different key should NOT exist
        assert not await redis_repo.exists("test:exact:key:12")

    @pytest.mark.asyncio
    async def test_no_false_positives_similar_suffix(
        self, redis_repo: RedisRepository
    ):
        """Similar key with different prefix should NOT match."""
        await redis_repo.set("test:exact:key:123", "value", ttl=60)

        # Similar but different key should NOT exist
        assert not await redis_repo.exists("test:exact:key:1234")

    @pytest.mark.asyncio
    async def test_no_partial_matches(self, redis_repo: RedisRepository):
        """Substring keys should NOT match."""
        await redis_repo.set("pick:TeamA:TeamB:12345:over:2.5:bookie", "v", ttl=60)

        # Partial/substring should NOT match
        assert not await redis_repo.exists("pick:TeamA:TeamB:12345")
        assert not await redis_repo.exists("TeamA:TeamB:12345:over:2.5:bookie")
        assert not await redis_repo.exists("over:2.5:bookie")


# ============================================================================
# TestRedisRepositoryConnection - Connection handling
# ============================================================================


class TestRedisRepositoryConnection:
    """Integration tests for connection handling."""

    @pytest.mark.asyncio
    async def test_close_clears_cache(self, redis_container):
        """close() should clear local cache."""
        host = redis_container.get_container_host_ip()
        port = int(redis_container.get_exposed_port(6379))

        repo = RedisRepository(
            host=host,
            port=port,
            db=15,
            max_connections=10,
            local_cache_size=100,
        )

        # Set and populate cache
        await repo.set("test:cache_clear", "value", ttl=60)
        assert repo._local_cache.get("test:cache_clear") is True

        await repo.close()

        # Cache should be cleared
        assert len(repo._local_cache) == 0

    @pytest.mark.asyncio
    async def test_close_closes_connection(self, redis_container):
        """close() should close Redis connection."""
        host = redis_container.get_container_host_ip()
        port = int(redis_container.get_exposed_port(6379))

        repo = RedisRepository(
            host=host,
            port=port,
            db=15,
        )

        # Initialize connection
        await repo._get_client()
        assert repo._redis is not None

        await repo.close()

        # Connection should be None
        assert repo._redis is None
        assert repo._pool is None


# ============================================================================
# TestRedisRepositoryLocalCache - Cache synchronization
# ============================================================================


class TestRedisRepositoryLocalCache:
    """Integration tests for local cache synchronization."""

    @pytest.mark.asyncio
    async def test_local_cache_populated_on_exists(
        self, redis_repo: RedisRepository
    ):
        """Local cache should be populated when exists() hits Redis."""
        # Set key directly
        await redis_repo.set("test:cache_pop", "value", ttl=60)

        # Clear local cache manually to test Redis hit
        redis_repo._local_cache.clear()

        # Exists should hit Redis and populate cache
        assert await redis_repo.exists("test:cache_pop")

        # Now cache should have the key
        assert redis_repo._local_cache.get("test:cache_pop") is True

    @pytest.mark.asyncio
    async def test_local_cache_invalidated_on_delete(
        self, redis_repo: RedisRepository
    ):
        """Local cache should be invalidated when delete() is called."""
        await redis_repo.set("test:cache_del", "value", ttl=60)

        # Verify cache has the key
        assert redis_repo._local_cache.get("test:cache_del") is True

        # Delete should invalidate cache
        await redis_repo.delete("test:cache_del")

        # Cache should no longer have the key
        assert redis_repo._local_cache.get("test:cache_del") is False


# ============================================================================
# TestRedisRepositoryRepr - Debugging
# ============================================================================


class TestRedisRepositoryRepr:
    """Integration tests for debugging utilities."""

    @pytest.mark.asyncio
    async def test_repr(self, redis_repo: RedisRepository):
        """__repr__ should return valid string representation."""
        repr_str = repr(redis_repo)
        assert "RedisRepository" in repr_str
        assert "host=" in repr_str
        assert "port=" in repr_str
        assert "db=" in repr_str
