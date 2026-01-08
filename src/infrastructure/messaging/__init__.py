"""Messaging package - Telegram integration.

Contains:
- telegram_gateway: Gateway with priority queue and bot rotation
- message_formatter: HTML formatter with cache

Reference: docs/05-Implementation.md Phase 5
"""

from .message_formatter import MessageFormatter
from .telegram_gateway import TelegramGateway

__all__ = ["TelegramGateway", "MessageFormatter"]
