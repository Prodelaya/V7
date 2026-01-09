"""Telegram gateway with priority queue and bot rotation.

Implementation:
- Priority queue (heap) ordered by profit descending
- Dynamic multi-bot rotation (configurable via TELEGRAM_BOT_TOKENS)
- Max queue size: 1000 (reject low priority if full)
- Retry with exponential backoff

Reference:
- docs/05-Implementation.md: Task 5C.3
- docs/02-PDR.md: Section 3.3.2 (Telegram Gateway)
- docs/03-ADRs.md: ADR-006 (Heap Priorizado)
- docs/01-SRS.md: RF-008
"""

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, List, Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

if TYPE_CHECKING:
    from src.domain.entities.pick import Pick
    from src.infrastructure.messaging.message_formatter import MessageFormatter

logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityMessage:
    """
    Message with priority for heap queue.

    Uses negative profit for max-heap behavior (heapq is a min-heap).
    Timestamp is used as tie-breaker for equal profits (FIFO).

    Attributes:
        priority: Negative profit for max-heap (lower = higher priority)
        timestamp: Creation time for FIFO ordering on ties
        pick: Original Pick entity (not used in comparison)
        channel_id: Target Telegram channel ID
        formatted: Pre-formatted HTML message
        retries: Number of send attempts made
    """

    priority: float  # Negative profit for max-heap
    timestamp: float = field(compare=True)
    pick: object = field(compare=False)
    channel_id: int = field(compare=False)
    formatted: str = field(compare=False)
    retries: int = field(default=0, compare=False)


class TelegramGateway:
    """
    Gateway for sending picks to Telegram with priority queue.

    Features:
    - Priority queue (heap) ordered by profit (higher first)
    - Dynamic multi-bot rotation (number of bots configurable via .env)
    - Graceful degradation when queue full (reject low priority)
    - Retry with exponential backoff

    Heap structure (from ADR-006):
        (-profit, timestamp, channel_id, message)
        Negative profit for max-heap behavior

    Queue behavior (from SRS RF-008):
        - Max size: 1000 messages
        - If full and new profit > min in queue: replace min
        - If full and new profit <= min: reject new

    Bot Configuration:
        Bots are loaded from TELEGRAM_BOT_TOKENS in .env (comma-separated).
        All bots participate in round-robin rotation for rate limiting.
    """

    MAX_QUEUE_SIZE = 1000
    RATE_LIMIT_WINDOW = 1.0  # seconds
    MESSAGES_PER_WINDOW = 30  # per bot

    def __init__(
        self,
        bot_tokens: List[str],
        formatter: "MessageFormatter",
        max_retries: int = 3,
        max_queue_size: Optional[int] = None,
    ):
        """
        Initialize gateway with dynamic bot pool.

        Args:
            bot_tokens: List of Telegram bot tokens (any number supported)
            formatter: MessageFormatter for formatting messages
            max_retries: Max send attempts per message (default: 3)
            max_queue_size: Override default max queue size (default: 1000)

        Raises:
            ValueError: If no bot tokens provided
        """
        if not bot_tokens:
            raise ValueError("At least one bot token is required")

        self._bots = [Bot(token=token) for token in bot_tokens]
        self._current_bot_index = 0
        self._formatter = formatter
        self._max_retries = max_retries
        self._max_queue_size = max_queue_size or self.MAX_QUEUE_SIZE
        self._queue: List[PriorityMessage] = []
        self._is_running = False
        self._process_task: Optional[asyncio.Task] = None

        # Retry delays with exponential backoff
        self._retry_delays = {1: 1, 2: 5, 3: 15}
        self._max_wait_time = 30  # Max seconds before discarding

        logger.info(
            f"TelegramGateway initialized with {len(self._bots)} bots, "
            f"max_queue_size={self._max_queue_size}"
        )

    async def send(
        self,
        pick: "Pick",
        channel_id: int,
        profit: float,
        formatted_message: Optional[str] = None,
    ) -> bool:
        """
        Add pick to priority queue for sending.

        Higher profit picks are sent first. If queue is full:
        - Reject if new profit <= minimum profit in queue
        - Replace minimum if new profit > minimum profit

        Args:
            pick: Pick entity to send
            channel_id: Target Telegram channel ID
            profit: Profit percentage (used for priority)
            formatted_message: Pre-formatted message (optional, uses formatter if None)

        Returns:
            True if queued successfully, False if rejected
        """
        # Format message if not provided
        if formatted_message is None:
            formatted_message = await self._formatter.format(pick)
            if not formatted_message:
                logger.debug("Empty formatted message for pick, skipping")
                return False

        # Create priority message with negative profit for max-heap
        message = PriorityMessage(
            priority=-profit,  # Negative for max-heap
            timestamp=time.time(),
            pick=pick,
            channel_id=channel_id,
            formatted=formatted_message,
            retries=0,
        )

        # Check queue capacity
        if len(self._queue) >= self._max_queue_size:
            # Queue full - find item with lowest profit (highest priority value)
            # Need to scan since heap root has highest profit, not lowest
            min_idx = 0
            min_priority = self._queue[0].priority
            for i, msg in enumerate(self._queue):
                if msg.priority > min_priority:  # Higher priority value = lower profit
                    min_priority = msg.priority
                    min_idx = i

            min_profit = -min_priority

            if profit <= min_profit:
                # New message has lower or equal priority - reject
                logger.debug(
                    f"Queue full, rejecting pick with profit {profit:.2f}% "
                    f"(min in queue: {min_profit:.2f}%)"
                )
                return False

            # New message has higher priority - replace minimum
            # Remove the min item and push new one
            self._queue[min_idx] = self._queue[-1]
            self._queue.pop()
            heapq.heapify(self._queue)
            heapq.heappush(self._queue, message)
            logger.debug(
                f"Queue full, replaced min profit {min_profit:.2f}% "
                f"with new profit {profit:.2f}%"
            )
            return True

        # Queue has space - just add
        heapq.heappush(self._queue, message)
        logger.debug(
            f"Queued pick with profit {profit:.2f}%, queue size: {len(self._queue)}"
        )
        return True

    async def start_processing(self) -> None:
        """
        Start background processing task.

        Idempotent - calling multiple times is safe.
        """
        if self._is_running:
            logger.debug("Processing already running")
            return

        self._is_running = True
        self._process_task = asyncio.create_task(
            self._process_loop(),
            name="telegram_gateway_process_loop",
        )
        logger.info("TelegramGateway processing started")

    async def stop_processing(self) -> None:
        """
        Stop background processing gracefully.

        Waits for current send to complete before stopping.
        """
        if not self._is_running:
            return

        self._is_running = False

        if self._process_task and not self._process_task.done():
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass

        logger.info(
            f"TelegramGateway processing stopped, "
            f"{len(self._queue)} messages remaining in queue"
        )

    async def _process_loop(self) -> None:
        """
        Main processing loop - sends highest priority messages first.

        Runs until stop_processing() is called.
        """
        while self._is_running:
            if not self._queue:
                # No messages - sleep briefly to avoid busy-wait
                await asyncio.sleep(0.05)
                continue

            # Pop highest priority message (lowest priority value due to negative)
            message = heapq.heappop(self._queue)
            success = await self._send_message(message)

            if not success and message.retries < self._max_retries:
                # Re-queue with incremented retry count and lower priority
                message.retries += 1
                # Slightly lower priority for retried messages
                message.priority += 0.001
                heapq.heappush(self._queue, message)
                # Wait before retry
                delay = self._retry_delays.get(message.retries, 15)
                await asyncio.sleep(delay)

    async def _send_message(self, message: PriorityMessage) -> bool:
        """
        Send message with retries and bot rotation.

        Handles Telegram-specific exceptions:
        - TelegramRetryAfter: Wait and retry with rotated bot
        - TelegramBadRequest: Log and fail (invalid format)
        - TelegramForbiddenError: Log and rotate bot

        Args:
            message: PriorityMessage to send

        Returns:
            True if sent successfully, False otherwise
        """
        start_time = time.time()
        tried_bots: set = set()

        while len(tried_bots) < len(self._bots):
            # Check timeout
            if time.time() - start_time > self._max_wait_time:
                logger.warning(
                    f"Message discarded after {self._max_wait_time}s timeout, "
                    f"channel: {message.channel_id}"
                )
                return False

            bot = self._bots[self._current_bot_index]
            bot_id = bot.token.split(":")[0] if bot.token else str(self._current_bot_index)

            if bot_id in tried_bots:
                self._rotate_bot()
                continue

            try:
                await bot.send_message(
                    chat_id=message.channel_id,
                    text=message.formatted,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                    disable_notification=True,
                )
                logger.debug(
                    f"Message sent successfully via bot {bot_id} "
                    f"to channel {message.channel_id}"
                )
                return True

            except TelegramRetryAfter as e:
                tried_bots.add(bot_id)
                logger.warning(
                    f"Rate limit on bot {bot_id}, retry after {e.retry_after}s"
                )
                self._rotate_bot()

                # If all bots tried, wait and reset
                if len(tried_bots) >= len(self._bots):
                    wait_time = min(e.retry_after, 30)
                    await asyncio.sleep(wait_time)
                    tried_bots.clear()

            except TelegramBadRequest as e:
                logger.error(
                    f"Bad request (invalid format) for channel {message.channel_id}: {e}"
                )
                return False  # Don't retry bad format

            except TelegramForbiddenError as e:
                tried_bots.add(bot_id)
                logger.error(
                    f"Bot {bot_id} forbidden from channel {message.channel_id}: {e}"
                )
                self._rotate_bot()

            except Exception as e:
                tried_bots.add(bot_id)
                logger.error(
                    f"Unexpected error sending to channel {message.channel_id}: {e}"
                )
                self._rotate_bot()
                await asyncio.sleep(1)

        # All bots failed
        logger.error(
            f"All {len(self._bots)} bots failed to send to channel {message.channel_id}"
        )
        return False

    def _rotate_bot(self) -> None:
        """Rotate to next bot in round-robin fashion."""
        self._current_bot_index = (self._current_bot_index + 1) % len(self._bots)

    @property
    def queue_size(self) -> int:
        """Current queue size."""
        return len(self._queue)

    @property
    def bot_count(self) -> int:
        """Number of bots in the pool."""
        return len(self._bots)

    @property
    def is_running(self) -> bool:
        """Check if processing loop is running."""
        return self._is_running

    def get_min_profit_in_queue(self) -> Optional[float]:
        """
        Get the minimum profit in the queue.

        Returns:
            Minimum profit value, or None if queue is empty
        """
        if not self._queue:
            return None
        # Scan for minimum profit (highest priority value)
        return min(-msg.priority for msg in self._queue)

    async def close(self) -> None:
        """
        Close all bot sessions gracefully.

        Should be called during application shutdown.
        """
        await self.stop_processing()

        for bot in self._bots:
            try:
                await bot.session.close()
            except Exception as e:
                logger.warning(f"Error closing bot session: {e}")

        logger.info("TelegramGateway closed, all bot sessions terminated")
