"""Parallel prefetch manager for API polling.

Enables overlap between API fetching and pick processing to reduce
effective latency by ~100-200ms per cycle.

Implementation:
- Background task fetches next batch while current is processed
- Bounded queue (maxsize=2) to limit memory usage
- Respects AdaptiveRateLimiter (ADR-010)
- Graceful shutdown

Reference:
- docs/03-ADRs.md: ADR-010 (Adaptive Rate Limiter)
- legacy/RetadorV6.py: OptimizedPrefetchManager (lines 710-768)
"""

import asyncio
import logging
from typing import TYPE_CHECKING, List, Optional

if TYPE_CHECKING:
    from src.infrastructure.api.rate_limiter import AdaptiveRateLimiter
    from src.infrastructure.api.surebet_client import SurebetClient

logger = logging.getLogger(__name__)


class PrefetchManager:
    """Parallel prefetch manager for API polling.

    Fetches the next batch of picks in the background while the current
    batch is being processed, reducing effective per-cycle latency.

    Flow (with overlap):
        [Fetch N] → [Process N + Fetch N+1] → [Process N+1 + Fetch N+2]
                    ↑ overlap saves ~100-200ms

    Features:
    - Bounded asyncio.Queue (default maxsize=2)
    - Respects rate limiter delays
    - Graceful shutdown with queue drain

    Example:
        >>> prefetch = PrefetchManager(client, rate_limiter)
        >>> await prefetch.start()
        >>> while running:
        ...     picks = await prefetch.get_next_batch()
        ...     await process(picks)
        >>> await prefetch.stop()
    """

    DEFAULT_MAX_QUEUE_SIZE = 2

    def __init__(
        self,
        client: "SurebetClient",
        rate_limiter: "AdaptiveRateLimiter",
        max_queue_size: int = DEFAULT_MAX_QUEUE_SIZE,
    ) -> None:
        """Initialize prefetch manager.

        Args:
            client: SurebetClient for API calls
            rate_limiter: AdaptiveRateLimiter for respecting API limits
            max_queue_size: Maximum batches to keep ahead (default: 2)
        """
        self._client = client
        self._rate_limiter = rate_limiter
        self._max_queue_size = max_queue_size

        self._queue: asyncio.Queue[List[dict]] = asyncio.Queue(
            maxsize=max_queue_size
        )
        self._is_running = False
        self._fetch_task: Optional[asyncio.Task] = None

        logger.info(
            f"PrefetchManager initialized (max_queue_size={max_queue_size})"
        )

    async def start(self) -> None:
        """Start background prefetching.

        Idempotent - calling multiple times is safe.
        """
        if self._is_running:
            logger.debug("PrefetchManager already running")
            return

        self._is_running = True
        self._fetch_task = asyncio.create_task(
            self._prefetch_loop(),
            name="prefetch_manager_loop",
        )
        logger.info("PrefetchManager started")

    async def stop(self) -> None:
        """Stop prefetching gracefully.

        Waits for current fetch to complete, then drains queue.
        """
        if not self._is_running:
            return

        self._is_running = False

        # Cancel the fetch task
        if self._fetch_task and not self._fetch_task.done():
            self._fetch_task.cancel()
            try:
                await self._fetch_task
            except asyncio.CancelledError:
                pass

        # Drain the queue
        drained = 0
        while not self._queue.empty():
            try:
                self._queue.get_nowait()
                drained += 1
            except asyncio.QueueEmpty:
                break

        logger.info(f"PrefetchManager stopped (drained {drained} batches)")

    async def get_next_batch(self, timeout: Optional[float] = None) -> List[dict]:
        """Get next batch of picks.

        Blocks if queue is empty until a batch is available.

        Args:
            timeout: Optional timeout in seconds (None = wait forever)

        Returns:
            List of pick records from API

        Raises:
            asyncio.TimeoutError: If timeout is reached
        """
        try:
            if timeout is not None:
                async with asyncio.timeout(timeout):
                    batch = await self._queue.get()
            else:
                batch = await self._queue.get()

            logger.debug(
                f"Got batch of {len(batch)} picks, "
                f"queue size: {self._queue.qsize()}"
            )
            return batch

        except asyncio.TimeoutError:
            logger.warning(f"get_next_batch timed out after {timeout}s")
            raise

    async def _prefetch_loop(self) -> None:
        """Background loop that continuously fetches picks.

        Respects rate limiter between fetches.
        """
        logger.debug("Prefetch loop started")

        while self._is_running:
            try:
                # Wait for rate limiter before fetching
                await self._rate_limiter.wait_if_needed()

                # Fetch next batch
                picks = await self._client.fetch_picks()

                if picks:
                    # Put in queue (blocks if full until space available)
                    await self._queue.put(picks)
                    logger.debug(
                        f"Prefetched {len(picks)} picks, "
                        f"queue size: {self._queue.qsize()}"
                    )
                else:
                    # Empty response - wait a bit before retrying
                    await asyncio.sleep(0.1)

            except asyncio.CancelledError:
                logger.debug("Prefetch loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in prefetch loop: {e}")
                # Wait before retrying on error
                await asyncio.sleep(1.0)

        logger.debug("Prefetch loop exited")

    @property
    def is_running(self) -> bool:
        """Check if prefetching is active."""
        return self._is_running

    @property
    def queue_size(self) -> int:
        """Current number of batches in queue."""
        return self._queue.qsize()

    @property
    def queue_full(self) -> bool:
        """Check if queue is at capacity."""
        return self._queue.full()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return (
            f"PrefetchManager(running={self._is_running}, "
            f"queue_size={self.queue_size}/{self._max_queue_size})"
        )
