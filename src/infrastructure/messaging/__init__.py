"""Messaging package - Telegram integration.

Contains:
- telegram_gateway: Gateway with priority queue and bot rotation
- message_formatter: HTML formatter with cache

Reference: docs/05-Implementation.md Phase 5
"""

from .telegram_gateway import TelegramGateway
from .message_formatter import MessageFormatter

__all__ = ["TelegramGateway", "MessageFormatter"]
