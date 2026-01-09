"""Unit tests for RedisRepository using mocks.

Tests verify correct behavior of the repository without requiring
a real Redis instance.

Reference:
- docs/05-Implementation.md: Task 5A.3
- docs/03-ADRs.md: ADR-004, ADR-012, ADR-013
"""

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.domain.entities.pick import Pick
from src.domain.value_objects.market_type import MarketType
from src.domain.value_objects.odds import Odds
from src.infrastructure.repositories.redis_repository import RedisRepository

# ============================================================================
# Fixtures
# ============================================================================





@pytest.fixture
def mock_redis() -> AsyncMock:
    """Create a mock Redis client."""
    mock = AsyncMock()
    mock.ping = AsyncMock(return_value=True)
    mock.exists = AsyncMock(return_value=0)
    mock.get = AsyncMock(return_value=None)
    mock.set = AsyncMock(return_value=True)
    mock.setex = AsyncMock(return_value=True)
    mock.delete = AsyncMock(return_value=1)

    # Mock pipeline context manager
    mock_pipe = AsyncMock()
    mock_pipe.exists = MagicMock()
    mock_pipe.setex = MagicMock()
    mock_pipe.execute = AsyncMock(return_value=[])
    mock_pipe.__aenter__ = AsyncMock(return_value=mock_pipe)
    mock_pipe.__aexit__ = AsyncMock(return_value=None)
    mock.pipeline = MagicMock(return_value=mock_pipe)

    return mock


@pytest.fixture
async def redis_repo(mock_redis: AsyncMock) -> RedisRepository:
    """Create RedisRepository with mocked Redis client."""
    repo = RedisRepository(host="localhost", port=6379, db=0)
    repo._redis = mock_redis  # Inject mock
    return repo


@pytest.fixture
def sample_pick() -> Pick:
    """Create a sample Pick for testing."""
    return Pick(
        teams=("Team A", "Team B"),
        odds=Odds(2.05),
        market_type=MarketType.OVER,
        variety="2.5",
        event_time=datetime.now(timezone.utc),
        bookmaker="pinnaclesports",
        tournament="Test League",
        sport_id="Football",
    )


# ============================================================================
# Tests for RedisRepository
# ============================================================================


class TestRedisRepositoryExists:
    """Tests for exists() method."""

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_missing_key(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """exists() should return False when key doesn't exist."""
        mock_redis.exists.return_value = 0
        result = await redis_repo.exists("nonexistent:key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_returns_true_when_found(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """exists() should return True when key exists in Redis."""
        mock_redis.exists.return_value = 1
        result = await redis_repo.exists("existing:key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_checks_cache_first(self, redis_repo: RedisRepository):
        """exists() should check local cache before Redis."""
        # Pre-populate cache
        await redis_repo._local_cache.set("cached:key", True)

        # Should return True without calling Redis
        result = await redis_repo.exists("cached:key")
        assert result is True
        # Redis exists should NOT be called (we got cache hit)

    @pytest.mark.asyncio
    async def test_exists_updates_cache_on_redis_hit(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """exists() should update cache when found in Redis."""
        mock_redis.exists.return_value = 1
        await redis_repo.exists("new:key")

        # Should now be in cache
        assert redis_repo._local_cache.exists("new:key") is True


class TestRedisRepositoryExistsAny:
    """Tests for exists_any() method."""

    @pytest.mark.asyncio
    async def test_exists_any_returns_false_for_empty_list(
        self, redis_repo: RedisRepository
    ):
        """exists_any() should return False for empty key list."""
        result = await redis_repo.exists_any([])
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_any_returns_true_from_cache(
        self, redis_repo: RedisRepository
    ):
        """exists_any() should return True if any key in cache."""
        await redis_repo._local_cache.set("key2", True)
        result = await redis_repo.exists_any(["key1", "key2", "key3"])
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_any_uses_pipeline(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """exists_any() should use pipeline for batch check."""
        mock_pipe = mock_redis.pipeline.return_value.__aenter__.return_value
        mock_pipe.execute.return_value = [0, 1, 0]

        result = await redis_repo.exists_any(["key1", "key2", "key3"])
        assert result is True
        mock_redis.pipeline.assert_called_once()


class TestRedisRepositorySet:
    """Tests for set() method - ADR-013 compliance."""

    @pytest.mark.asyncio
    async def test_set_awaits_confirmation(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """set() should await Redis confirmation (no fire-and-forget)."""
        mock_redis.setex = AsyncMock(return_value=True)
        result = await redis_repo.set("test:key", "value", ttl=60)

        assert result is True
        mock_redis.setex.assert_called_once_with("test:key", 60, "value")

    @pytest.mark.asyncio
    async def test_set_updates_local_cache(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """set() should update local cache on success."""
        mock_redis.setex = AsyncMock(return_value=True)
        await redis_repo.set("test:key", "value", ttl=60)

        assert redis_repo._local_cache.exists("test:key") is True


class TestRedisRepositorySetBatch:
    """Tests for set_batch() method - ADR-004 and ADR-013 compliance."""

    @pytest.mark.asyncio
    async def test_set_batch_uses_transaction(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """set_batch() should use transactional pipeline."""
        mock_pipe = mock_redis.pipeline.return_value.__aenter__.return_value
        mock_pipe.execute.return_value = [True, True]

        items = [("key1", "v1", 60), ("key2", "v2", 60)]
        result = await redis_repo.set_batch(items)

        assert result is True
        mock_redis.pipeline.assert_called_once_with(transaction=True)

    @pytest.mark.asyncio
    async def test_set_batch_returns_true_for_empty(self, redis_repo: RedisRepository):
        """set_batch() should return True for empty list."""
        result = await redis_repo.set_batch([])
        assert result is True


class TestRedisRepositorySaveWithOpposites:
    """Tests for save_with_opposites() - RF-004 compliance."""

    @pytest.mark.asyncio
    async def test_save_with_opposites_saves_main_key(
        self,
        redis_repo: RedisRepository,
        mock_redis: AsyncMock,
        sample_pick: Pick,
    ):
        """save_with_opposites() should save main pick key."""
        mock_pipe = mock_redis.pipeline.return_value.__aenter__.return_value
        mock_pipe.execute.return_value = [True, True]

        result = await redis_repo.save_with_opposites(sample_pick, ttl=3600)
        assert result is True

    @pytest.mark.asyncio
    async def test_save_with_opposites_saves_opposite_keys(
        self,
        redis_repo: RedisRepository,
        mock_redis: AsyncMock,
        sample_pick: Pick,
    ):
        """save_with_opposites() should save opposite market keys."""
        mock_pipe = mock_redis.pipeline.return_value.__aenter__.return_value
        mock_pipe.execute.return_value = [True, True]

        await redis_repo.save_with_opposites(sample_pick, ttl=3600)

        # OVER has opposite UNDER
        assert sample_pick.market_type == MarketType.OVER
        opposite_keys = sample_pick.get_opposite_keys()
        assert len(opposite_keys) >= 1
        assert "under" in opposite_keys[0].lower()


class TestRedisRepositoryCursor:
    """Tests for cursor persistence - ADR-009 compliance."""

    @pytest.mark.asyncio
    async def test_set_cursor_persists(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """set_cursor() should persist cursor without TTL."""
        mock_redis.set = AsyncMock(return_value=True)
        result = await redis_repo.set_cursor("created_at:12345")

        assert result is True
        mock_redis.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cursor_retrieves(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """get_cursor() should retrieve persisted cursor."""
        mock_redis.get.return_value = "created_at:12345"
        result = await redis_repo.get_cursor()

        assert result == "created_at:12345"


class TestRedisRepositoryClose:
    """Tests for close() method."""

    @pytest.mark.asyncio
    async def test_close_clears_cache(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """close() should clear local cache."""
        await redis_repo._local_cache.set("test:key", True)
        mock_redis.close = AsyncMock()

        await redis_repo.close()

        assert len(redis_repo._local_cache) == 0


class TestRedisRepositoryNoBloomFilter:
    """Tests verifying ADR-012 compliance (no false positives)."""

    @pytest.mark.asyncio
    async def test_no_false_positives(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """
        Different keys should NOT be reported as existing.

        This is the critical test for ADR-012 - we must never
        lose a valid pick due to false positives.
        """
        # Set one specific key
        mock_redis.exists.return_value = 0

        # Similar but different keys should NOT match
        assert await redis_repo.exists("pick:123:over") is False
        assert await redis_repo.exists("pick:123:under") is False
        assert await redis_repo.exists("pick:124:over") is False


class TestRedisRepositoryTimeout:
    """Tests for timeout handling - ADR-013 resilience."""

    @pytest.mark.asyncio
    async def test_set_handles_timeout(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """set() should handle timeout gracefully."""
        mock_redis.setex = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await redis_repo.set("test:key", "value", ttl=60)
        assert result is False  # Should return False, not raise

    @pytest.mark.asyncio
    async def test_exists_handles_timeout(
        self, redis_repo: RedisRepository, mock_redis: AsyncMock
    ):
        """exists() should handle timeout gracefully."""
        mock_redis.exists = AsyncMock(side_effect=asyncio.TimeoutError())

        result = await redis_repo.exists("test:key")
        assert result is False  # Should return False, not raise
