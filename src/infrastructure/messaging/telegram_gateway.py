"""Telegram gateway with priority queue and bot rotation.

Implementation Requirements:
- Priority queue (heap) ordered by profit descending
- Multi-bot rotation for rate limiting (5 bots)
- Max queue size: 1000 (reject low priority if full)
- Retry with backoff

Reference:
- docs/05-Implementation.md: Task 5.8
- docs/02-PDR.md: Section 3.3.2 (Telegram Gateway)
- docs/03-ADRs.md: ADR-006 (Heap Priorizado)
- docs/01-SRS.md: RF-008

TODO: Implement TelegramGateway
"""

import heapq
from typing import List, Optional
from dataclasses import dataclass, field

from aiogram import Bot


@dataclass(order=True)
class PriorityMessage:
    """
    Message with priority for heap queue.
    
    Uses negative profit for max-heap behavior
    (heapq is a min-heap).
    """
    priority: float  # Negative profit for max-heap
    pick: object = field(compare=False)
    channel_id: int = field(compare=False)
    formatted: str = field(compare=False)


class TelegramGateway:
    """
    Gateway for sending picks to Telegram.
    
    Features:
    - Priority queue (heap) ordered by profit
    - Higher profit picks sent first
    - Multi-bot rotation (5 bots, 30 msg/s each)
    - Graceful degradation when queue full
    
    Heap structure (from ADR-006):
        (-profit, timestamp, channel_id, message)
        Negative profit for max-heap behavior
    
    Queue behavior (from SRS RF-008):
        - Max size: 1000 messages
        - If full and new profit > min in queue: replace
        - If full and new profit <= min: reject
    
    TODO: Implement based on:
    - Task 5.8 in docs/05-Implementation.md
    - ADR-006 in docs/03-ADRs.md
    - RF-008 in docs/01-SRS.md
    - TelegramSender in legacy/RetadorV6.py (line 1477)
    """
    
    MAX_QUEUE_SIZE = 1000
    
    def __init__(
        self,
        bot_tokens: List[str],
        formatter,  # MessageFormatter
        max_retries: int = 3,
    ):
        """
        Initialize gateway.
        
        Args:
            bot_tokens: List of Telegram bot tokens (5 recommended)
            formatter: MessageFormatter for formatting messages
            max_retries: Max send attempts per message
        """
        self._bots = [Bot(token=token) for token in bot_tokens]
        self._current_bot_index = 0
        self._formatter = formatter
        self._max_retries = max_retries
        self._queue: List[PriorityMessage] = []
        self._is_running = False
    
    async def send(self, pick, channel_id: int) -> bool:
        """
        Add pick to priority queue for sending.
        
        Higher profit picks are sent first.
        
        Args:
            pick: Pick entity
            channel_id: Telegram channel ID
            
        Returns:
            True if queued, False if rejected (queue full, low priority)
        """
        raise NotImplementedError("TelegramGateway.send not implemented")
    
    async def start_processing(self) -> None:
        """Start background processing task."""
        raise NotImplementedError("TelegramGateway.start_processing not implemented")
    
    async def stop_processing(self) -> None:
        """Stop background processing."""
        raise NotImplementedError("TelegramGateway.stop_processing not implemented")
    
    async def _process_loop(self) -> None:
        """Main processing loop."""
        raise NotImplementedError("TelegramGateway._process_loop not implemented")
    
    async def _send_message(self, message: PriorityMessage) -> bool:
        """Send message with retries and bot rotation."""
        raise NotImplementedError("TelegramGateway._send_message not implemented")
    
    def _rotate_bot(self) -> None:
        """Rotate to next bot."""
        raise NotImplementedError("TelegramGateway._rotate_bot not implemented")
    
    @property
    def queue_size(self) -> int:
        """Current queue size."""
        return len(self._queue)
    
    async def close(self) -> None:
        """Close all bot sessions."""
        raise NotImplementedError("TelegramGateway.close not implemented")
