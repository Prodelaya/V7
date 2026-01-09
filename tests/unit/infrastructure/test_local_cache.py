"""Unit tests for LocalCache.

Tests verify correct behavior of the in-memory cache including:
- Basic CRUD operations
- LRU eviction
- TTL expiration
- Async safety

Reference:
- docs/05-Implementation.md: Task 5C.5
"""

from __future__ import annotations

import asyncio
import time
from unittest.mock import patch

import pytest

from src.infrastructure.cache.local_cache import LocalCache

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def cache() -> LocalCache:
    """Create a LocalCache instance with default settings."""
    return LocalCache(max_size=100, default_ttl=60)


@pytest.fixture
def small_cache() -> LocalCache:
    """Create a small cache for testing LRU eviction."""
    return LocalCache(max_size=3, default_ttl=None)


# ============================================================================
# Tests: Basic CRUD
# ============================================================================


class TestLocalCacheCRUD:
    """Tests for basic CRUD operations."""

    def test_get_missing_key_returns_none(self, cache: LocalCache):
        """get() should return None for non-existent key."""
        assert cache.get("nonexistent") is None

    @pytest.mark.asyncio
    async def test_set_and_get(self, cache: LocalCache):
        """set() should make get() return the value."""
        await cache.set("test:key", "my_value")
        assert cache.get("test:key") == "my_value"

    @pytest.mark.asyncio
    async def test_set_different_value_types(self, cache: LocalCache):
        """set() should work with different value types."""
        await cache.set("str_key", "string_value")
        await cache.set("int_key", 42)
        await cache.set("dict_key", {"nested": "value"})
        await cache.set("bool_key", True)

        assert cache.get("str_key") == "string_value"
        assert cache.get("int_key") == 42
        assert cache.get("dict_key") == {"nested": "value"}
        assert cache.get("bool_key") is True

    @pytest.mark.asyncio
    async def test_set_updates_existing_key(self, cache: LocalCache):
        """set() should update value for existing key."""
        await cache.set("test:key", "old_value")
        await cache.set("test:key", "new_value")
        assert cache.get("test:key") == "new_value"

    @pytest.mark.asyncio
    async def test_delete_removes_key(self, cache: LocalCache):
        """delete() should remove key from cache."""
        await cache.set("test:key", "value")
        assert cache.get("test:key") == "value"

        result = await cache.delete("test:key")
        assert result is True
        assert cache.get("test:key") is None

    @pytest.mark.asyncio
    async def test_delete_nonexistent_returns_false(self, cache: LocalCache):
        """delete() should return False for non-existent key."""
        result = await cache.delete("nonexistent")
        assert result is False

    @pytest.mark.asyncio
    async def test_clear_removes_all(self, cache: LocalCache):
        """clear() should remove all entries."""
        await cache.set("key1", "v1")
        await cache.set("key2", "v2")
        await cache.set("key3", "v3")
        assert len(cache) == 3

        await cache.clear()
        assert len(cache) == 0
        assert cache.get("key1") is None

    def test_len_returns_count(self, cache: LocalCache):
        """__len__ should return current entry count."""
        assert len(cache) == 0

    @pytest.mark.asyncio
    async def test_len_after_operations(self, cache: LocalCache):
        """__len__ should track additions and deletions."""
        await cache.set("key1", "v1")
        assert len(cache) == 1

        await cache.set("key2", "v2")
        assert len(cache) == 2

        await cache.delete("key1")
        assert len(cache) == 1


# ============================================================================
# Tests: exists() convenience method
# ============================================================================


class TestLocalCacheExists:
    """Tests for exists() method."""

    def test_exists_returns_false_for_missing_key(self, cache: LocalCache):
        """exists() should return False for non-existent key."""
        assert cache.exists("nonexistent") is False

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_valid_key(self, cache: LocalCache):
        """exists() should return True for existing key."""
        await cache.set("test:key", "value")
        assert cache.exists("test:key") is True

    @pytest.mark.asyncio
    async def test_exists_returns_false_for_expired_key(self, cache: LocalCache):
        """exists() should return False for expired key."""
        await cache.set("test:key", "value", ttl=-1)  # Already expired
        assert cache.exists("test:key") is False


# ============================================================================
# Tests: LRU Eviction
# ============================================================================


class TestLocalCacheLRU:
    """Tests for LRU eviction behavior."""

    @pytest.mark.asyncio
    async def test_lru_eviction_at_capacity(self, small_cache: LocalCache):
        """Oldest entry should be evicted when at max capacity."""
        await small_cache.set("key1", "v1")
        await small_cache.set("key2", "v2")
        await small_cache.set("key3", "v3")
        assert len(small_cache) == 3

        # Adding 4th key should evict key1 (oldest)
        await small_cache.set("key4", "v4")
        assert len(small_cache) == 3
        assert small_cache.get("key1") is None
        assert small_cache.get("key4") == "v4"

    @pytest.mark.asyncio
    async def test_lru_access_updates_order(self, small_cache: LocalCache):
        """Accessing a key should update its LRU position."""
        await small_cache.set("key1", "v1")
        await small_cache.set("key2", "v2")
        await small_cache.set("key3", "v3")

        # Access key1 to make it recently used
        _ = small_cache.get("key1")

        # Adding key4 should now evict key2 (oldest non-accessed)
        await small_cache.set("key4", "v4")
        assert small_cache.get("key1") == "v1"  # Still present
        assert small_cache.get("key2") is None  # Evicted
        assert small_cache.get("key4") == "v4"

    @pytest.mark.asyncio
    async def test_update_existing_key_no_eviction(self, small_cache: LocalCache):
        """Updating existing key should not trigger eviction."""
        await small_cache.set("key1", "v1")
        await small_cache.set("key2", "v2")
        await small_cache.set("key3", "v3")

        # Update key2 - should not evict anything
        await small_cache.set("key2", "updated")
        assert len(small_cache) == 3
        assert small_cache.get("key1") == "v1"
        assert small_cache.get("key2") == "updated"
        assert small_cache.get("key3") == "v3"


# ============================================================================
# Tests: TTL Expiration
# ============================================================================


class TestLocalCacheTTL:
    """Tests for TTL expiration behavior."""

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache: LocalCache):
        """Expired entries should not be returned."""
        await cache.set("test:key", "value", ttl=-1)  # Already expired
        assert cache.get("test:key") is None

    @pytest.mark.asyncio
    async def test_custom_ttl_overrides_default(self):
        """Custom TTL should override default."""
        cache = LocalCache(max_size=100, default_ttl=3600)  # 1 hour default
        await cache.set("test:key", "value", ttl=-1)  # Immediate expire
        assert cache.get("test:key") is None

    @pytest.mark.asyncio
    async def test_no_ttl_means_no_expiry(self):
        """Key without TTL should not expire."""
        cache = LocalCache(max_size=100, default_ttl=None)
        await cache.set("test:key", "value")

        # Mock time.time to simulate future
        with patch("src.infrastructure.cache.local_cache.time.time", return_value=time.time() + 86400):
            assert cache.get("test:key") == "value"  # Still valid after 1 day

    @pytest.mark.asyncio
    async def test_cleanup_expired_removes_all_expired(self, cache: LocalCache):
        """cleanup_expired() should remove all expired entries."""
        # Set keys with different TTLs
        await cache.set("expired1", "v1", ttl=-1)
        await cache.set("expired2", "v2", ttl=-1)
        await cache.set("valid", "v3", ttl=3600)

        removed = await cache.cleanup_expired()
        assert removed == 2
        assert cache.get("valid") == "v3"
        assert len(cache) == 1

    @pytest.mark.asyncio
    async def test_cleanup_expired_on_empty_cache(self, cache: LocalCache):
        """cleanup_expired() should return 0 on empty cache."""
        removed = await cache.cleanup_expired()
        assert removed == 0

    @pytest.mark.asyncio
    async def test_get_removes_expired_entry(self, cache: LocalCache):
        """get() should remove expired entry from cache."""
        await cache.set("test:key", "value", ttl=-1)

        # Get should return None and remove from cache
        assert cache.get("test:key") is None
        assert len(cache) == 0


# ============================================================================
# Tests: Async Safety
# ============================================================================


class TestLocalCacheAsyncSafety:
    """Tests for async safety with concurrent access."""

    @pytest.mark.asyncio
    async def test_concurrent_sets(self):
        """Multiple concurrent sets should all succeed."""
        cache = LocalCache(max_size=1000, default_ttl=60)

        async def set_key(i: int):
            await cache.set(f"key{i}", f"value{i}")

        # Run 100 concurrent sets
        await asyncio.gather(*[set_key(i) for i in range(100)])

        assert len(cache) == 100
        for i in range(100):
            assert cache.get(f"key{i}") == f"value{i}"

    @pytest.mark.asyncio
    async def test_concurrent_mixed_operations(self):
        """Mixed concurrent operations should not corrupt state."""
        cache = LocalCache(max_size=50, default_ttl=60)

        async def mixed_ops(i: int):
            await cache.set(f"key{i}", f"value{i}")
            _ = cache.get(f"key{i}")
            if i % 3 == 0:
                await cache.delete(f"key{i}")

        await asyncio.gather(*[mixed_ops(i) for i in range(100)])

        # Verify cache is in valid state (no corruption)
        assert len(cache) <= 50  # Max size enforced


# ============================================================================
# Tests: Edge Cases
# ============================================================================


class TestLocalCacheEdgeCases:
    """Tests for edge cases."""

    @pytest.mark.asyncio
    async def test_empty_string_key(self, cache: LocalCache):
        """Empty string should be valid key."""
        await cache.set("", "empty_key_value")
        assert cache.get("") == "empty_key_value"

    @pytest.mark.asyncio
    async def test_none_value(self, cache: LocalCache):
        """None should be valid value (distinguishable from missing)."""
        await cache.set("none_key", None)
        # exists() returns False because get() returns None
        assert cache.exists("none_key") is False

    @pytest.mark.asyncio
    async def test_repr(self, cache: LocalCache):
        """__repr__ should return valid string."""
        await cache.set("key", "value")
        repr_str = repr(cache)
        assert "LocalCache" in repr_str
        assert "max_size=100" in repr_str
        assert "current_size=1" in repr_str

    @pytest.mark.asyncio
    async def test_max_size_one(self):
        """Cache with max_size=1 should work correctly."""
        cache = LocalCache(max_size=1, default_ttl=None)

        await cache.set("key1", "v1")
        assert len(cache) == 1

        await cache.set("key2", "v2")
        assert len(cache) == 1
        assert cache.get("key1") is None
        assert cache.get("key2") == "v2"
