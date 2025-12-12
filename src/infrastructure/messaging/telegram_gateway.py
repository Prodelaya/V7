"""Telegram gateway with priority queue and bot rotation."""

import asyncio
import heapq
import logging
from dataclasses import dataclass, field
from typing import List, Optional

from aiogram import Bot
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramRetryAfter, TelegramForbiddenError

from ...domain.entities.pick import Pick
from .message_formatter import MessageFormatter


logger = logging.getLogger(__name__)


@dataclass(order=True)
class PriorityMessage:
    """Message with priority for heap queue."""
    priority: float  # Negative profit for max-heap behavior
    pick: Pick = field(compare=False)
    channel_id: int = field(compare=False)
    formatted: str = field(compare=False)


class TelegramGateway:
    """
    Gateway for sending picks to Telegram.
    
    Features:
    - Priority queue (heap) ordered by profit
    - Bot rotation for rate limiting
    - Automatic retry with backoff
    """
    
    MAX_QUEUE_SIZE = 1000
    
    def __init__(
        self,
        bot_tokens: List[str],
        formatter: MessageFormatter,
        max_retries: int = 3,
    ):
        self._bots = [Bot(token=token) for token in bot_tokens]
        self._current_bot_index = 0
        self._formatter = formatter
        self._max_retries = max_retries
        
        # Priority queue (min-heap, use negative profit for max behavior)
        self._queue: List[PriorityMessage] = []
        self._queue_lock = asyncio.Lock()
        
        # Processing
        self._is_running = False
        self._process_task: Optional[asyncio.Task] = None
    
    async def send(self, pick: Pick, channel_id: int) -> bool:
        """
        Add pick to priority queue for sending.
        
        Higher profit picks are sent first.
        """
        async with self._queue_lock:
            # Check queue size
            if len(self._queue) >= self.MAX_QUEUE_SIZE:
                # Reject if lower priority than minimum in queue
                min_priority = -self._queue[0].priority if self._queue else 0
                if pick.profit.value <= min_priority:
                    logger.debug(f"Queue full, rejecting low priority pick")
                    return False
                # Remove lowest priority item
                heapq.heappop(self._queue)
            
            # Format message
            formatted = await self._formatter.format(pick)
            
            # Add to queue (negative priority for max-heap)
            message = PriorityMessage(
                priority=-pick.profit.value,
                pick=pick,
                channel_id=channel_id,
                formatted=formatted,
            )
            heapq.heappush(self._queue, message)
            
        return True
    
    async def start_processing(self) -> None:
        """Start background processing task."""
        self._is_running = True
        self._process_task = asyncio.create_task(self._process_loop())
    
    async def stop_processing(self) -> None:
        """Stop background processing."""
        self._is_running = False
        if self._process_task:
            self._process_task.cancel()
            try:
                await self._process_task
            except asyncio.CancelledError:
                pass
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        while self._is_running:
            try:
                message = await self._get_next_message()
                if message:
                    await self._send_message(message)
                else:
                    await asyncio.sleep(0.01)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in process loop: {e}")
                await asyncio.sleep(0.1)
    
    async def _get_next_message(self) -> Optional[PriorityMessage]:
        """Get highest priority message from queue."""
        async with self._queue_lock:
            if self._queue:
                return heapq.heappop(self._queue)
        return None
    
    async def _send_message(self, message: PriorityMessage) -> bool:
        """Send message with retries and bot rotation."""
        for attempt in range(self._max_retries):
            bot = self._get_next_bot()
            try:
                await bot.send_message(
                    chat_id=message.channel_id,
                    text=message.formatted,
                    parse_mode=ParseMode.HTML,
                    disable_web_page_preview=True,
                )
                return True
                
            except TelegramRetryAfter as e:
                logger.warning(f"Rate limited, waiting {e.retry_after}s")
                await asyncio.sleep(e.retry_after)
                self._rotate_bot()
                
            except TelegramForbiddenError:
                logger.error(f"Bot forbidden from channel {message.channel_id}")
                return False
                
            except Exception as e:
                logger.error(f"Send error (attempt {attempt + 1}): {e}")
                await asyncio.sleep(0.5 * (2 ** attempt))
                self._rotate_bot()
        
        return False
    
    def _get_next_bot(self) -> Bot:
        """Get current bot."""
        return self._bots[self._current_bot_index]
    
    def _rotate_bot(self) -> None:
        """Rotate to next bot."""
        self._current_bot_index = (self._current_bot_index + 1) % len(self._bots)
    
    @property
    def queue_size(self) -> int:
        """Current queue size."""
        return len(self._queue)
    
    async def close(self) -> None:
        """Close all bot sessions."""
        await self.stop_processing()
        for bot in self._bots:
            await bot.session.close()
