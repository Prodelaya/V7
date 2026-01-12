"""Unit tests for PrefetchManager.

Tests:
- Background prefetching behavior
- Queue bounds and blocking
- Rate limiter integration
- Graceful shutdown
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from src.infrastructure.api.prefetch_manager import PrefetchManager


@pytest.fixture
def mock_client():
    """Mock SurebetClient."""
    client = MagicMock()
    client.fetch_picks = AsyncMock(return_value=[{"id": 1}, {"id": 2}])
    return client


@pytest.fixture
def mock_rate_limiter():
    """Mock AdaptiveRateLimiter."""
    limiter = MagicMock()
    limiter.wait_if_needed = AsyncMock()
    limiter.current_interval = 0.5
    return limiter


@pytest.fixture
def prefetch_manager(mock_client, mock_rate_limiter):
    """Create PrefetchManager with mocks."""
    return PrefetchManager(
        client=mock_client,
        rate_limiter=mock_rate_limiter,
        max_queue_size=2,
    )


class TestPrefetchManagerInit:
    """Test initialization."""

    def test_init_default_values(self, mock_client, mock_rate_limiter):
        """Test initialization with defaults."""
        pm = PrefetchManager(mock_client, mock_rate_limiter)

        assert pm.is_running is False
        assert pm.queue_size == 0
        assert pm._max_queue_size == 2

    def test_init_custom_queue_size(self, mock_client, mock_rate_limiter):
        """Test custom max_queue_size."""
        pm = PrefetchManager(mock_client, mock_rate_limiter, max_queue_size=5)

        assert pm._max_queue_size == 5


class TestPrefetchManagerStart:
    """Test start behavior."""

    @pytest.mark.asyncio
    async def test_start_sets_running(self, prefetch_manager):
        """Test start() sets is_running to True."""
        await prefetch_manager.start()

        assert prefetch_manager.is_running is True

        # Cleanup
        await prefetch_manager.stop()

    @pytest.mark.asyncio
    async def test_start_idempotent(self, prefetch_manager):
        """Test calling start() multiple times is safe."""
        await prefetch_manager.start()
        await prefetch_manager.start()  # Second call should be no-op

        assert prefetch_manager.is_running is True

        await prefetch_manager.stop()

    @pytest.mark.asyncio
    async def test_start_creates_fetch_task(self, prefetch_manager):
        """Test start() creates background fetch task."""
        await prefetch_manager.start()

        assert prefetch_manager._fetch_task is not None
        assert not prefetch_manager._fetch_task.done()

        await prefetch_manager.stop()


class TestPrefetchManagerStop:
    """Test stop behavior."""

    @pytest.mark.asyncio
    async def test_stop_sets_not_running(self, prefetch_manager):
        """Test stop() sets is_running to False."""
        await prefetch_manager.start()
        await prefetch_manager.stop()

        assert prefetch_manager.is_running is False

    @pytest.mark.asyncio
    async def test_stop_when_not_started(self, prefetch_manager):
        """Test stop() when never started is safe."""
        await prefetch_manager.stop()

        assert prefetch_manager.is_running is False

    @pytest.mark.asyncio
    async def test_stop_cancels_task(self, prefetch_manager):
        """Test stop() cancels the fetch task."""
        await prefetch_manager.start()
        task = prefetch_manager._fetch_task

        await prefetch_manager.stop()

        assert task.done() or task.cancelled()

    @pytest.mark.asyncio
    async def test_stop_drains_queue(self, prefetch_manager, mock_client):
        """Test stop() drains the queue."""
        # Add items to queue manually
        await prefetch_manager._queue.put([{"id": 1}])
        await prefetch_manager._queue.put([{"id": 2}])

        assert prefetch_manager.queue_size == 2

        prefetch_manager._is_running = True  # Simulate running state
        await prefetch_manager.stop()

        assert prefetch_manager.queue_size == 0


class TestPrefetchManagerGetNextBatch:
    """Test get_next_batch behavior."""

    @pytest.mark.asyncio
    async def test_get_next_batch_returns_picks(self, prefetch_manager):
        """Test get_next_batch returns picks from queue."""
        # Add a batch to queue
        expected = [{"id": 1}, {"id": 2}]
        await prefetch_manager._queue.put(expected)

        result = await prefetch_manager.get_next_batch()

        assert result == expected

    @pytest.mark.asyncio
    async def test_get_next_batch_blocks_when_empty(self, prefetch_manager):
        """Test get_next_batch blocks when queue is empty."""
        with pytest.raises(asyncio.TimeoutError):
            await prefetch_manager.get_next_batch(timeout=0.1)

    @pytest.mark.asyncio
    async def test_get_next_batch_with_timeout(self, prefetch_manager):
        """Test get_next_batch respects timeout."""
        # Queue is empty, should timeout
        with pytest.raises(asyncio.TimeoutError):
            await prefetch_manager.get_next_batch(timeout=0.05)


class TestPrefetchManagerPrefetchLoop:
    """Test prefetch loop behavior."""

    @pytest.mark.asyncio
    async def test_prefetch_loop_calls_rate_limiter(
        self, prefetch_manager, mock_rate_limiter
    ):
        """Test prefetch loop waits for rate limiter."""
        await prefetch_manager.start()

        # Give it time to do at least one fetch
        await asyncio.sleep(0.1)

        await prefetch_manager.stop()

        # Rate limiter should have been called
        mock_rate_limiter.wait_if_needed.assert_called()

    @pytest.mark.asyncio
    async def test_prefetch_loop_calls_client(
        self, prefetch_manager, mock_client
    ):
        """Test prefetch loop calls client.fetch_picks."""
        await prefetch_manager.start()

        # Give it time to do at least one fetch
        await asyncio.sleep(0.1)

        await prefetch_manager.stop()

        # Client should have been called
        mock_client.fetch_picks.assert_called()

    @pytest.mark.asyncio
    async def test_prefetch_loop_populates_queue(
        self, prefetch_manager, mock_client
    ):
        """Test prefetch loop adds picks to queue."""
        mock_client.fetch_picks = AsyncMock(return_value=[{"id": 1}])

        await prefetch_manager.start()

        # Wait for queue to be populated
        await asyncio.sleep(0.1)

        assert prefetch_manager.queue_size > 0

        await prefetch_manager.stop()

    @pytest.mark.asyncio
    async def test_prefetch_loop_respects_max_queue(
        self, prefetch_manager, mock_client
    ):
        """Test queue doesn't exceed max size."""
        # Set up client to return data
        mock_client.fetch_picks = AsyncMock(return_value=[{"id": 1}])

        await prefetch_manager.start()

        # Let it run a bit
        await asyncio.sleep(0.2)

        # Queue should not exceed max
        assert prefetch_manager.queue_size <= prefetch_manager._max_queue_size

        await prefetch_manager.stop()

    @pytest.mark.asyncio
    async def test_prefetch_loop_handles_empty_response(
        self, prefetch_manager, mock_client
    ):
        """Test prefetch loop handles empty API response."""
        mock_client.fetch_picks = AsyncMock(return_value=[])

        await prefetch_manager.start()

        # Should not crash
        await asyncio.sleep(0.15)

        # Queue should remain empty
        assert prefetch_manager.queue_size == 0

        await prefetch_manager.stop()

    @pytest.mark.asyncio
    async def test_prefetch_loop_handles_exception(
        self, prefetch_manager, mock_client
    ):
        """Test prefetch loop continues after exception."""
        call_count = 0

        async def failing_fetch():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("Simulated error")
            return [{"id": 1}]

        mock_client.fetch_picks = failing_fetch

        await prefetch_manager.start()

        # Wait for retry
        await asyncio.sleep(1.2)

        await prefetch_manager.stop()

        # Should have retried after error
        assert call_count >= 2


class TestPrefetchManagerProperties:
    """Test property methods."""

    def test_is_running_initially_false(self, prefetch_manager):
        """Test is_running starts as False."""
        assert prefetch_manager.is_running is False

    def test_queue_size_empty(self, prefetch_manager):
        """Test queue_size when empty."""
        assert prefetch_manager.queue_size == 0

    @pytest.mark.asyncio
    async def test_queue_full(self, prefetch_manager):
        """Test queue_full property."""
        assert prefetch_manager.queue_full is False

        # Fill queue
        await prefetch_manager._queue.put([{"id": 1}])
        await prefetch_manager._queue.put([{"id": 2}])

        assert prefetch_manager.queue_full is True

    def test_repr(self, prefetch_manager):
        """Test string representation."""
        result = repr(prefetch_manager)

        assert "PrefetchManager" in result
        assert "running=False" in result
        assert "queue_size=0/2" in result
