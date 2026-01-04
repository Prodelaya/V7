"""Config package - Application configuration.

Contains:
- settings: Environment-based configuration with Pydantic
- bookmakers: Bookmaker configuration and channels
- logging_config: Logging setup with Telegram handler

Reference: docs/05-Implementation.md Phase 4
"""

from .settings import (
    Settings,
    APISettings,
    RedisSettings,
    TelegramSettings,
    PollingSettings,
    ValidationSettings,
    APIQuerySettings,
    ProcessingSettings,
)
from .bookmakers import BookmakerConfig

__all__ = [
    "Settings",
    "APISettings",
    "RedisSettings",
    "TelegramSettings",
    "PollingSettings",
    "ValidationSettings",
    "APIQuerySettings",
    "ProcessingSettings",
    "BookmakerConfig",
]
