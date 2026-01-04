"""Config package - Application configuration.

Contains:
- settings: Environment-based configuration with Pydantic
- bookmakers: Bookmaker configuration and channels
- logging_config: Logging setup with Telegram handler

Reference: docs/05-Implementation.md Phase 4
"""

from .bookmakers import BookmakerConfig
from .logging_config import (
    LoggingSettings,
    TelegramLogHandler,
    setup_logging,
    setup_logging_from_settings,
)
from .settings import (
    APIQuerySettings,
    APISettings,
    PollingSettings,
    ProcessingSettings,
    RedisSettings,
    Settings,
    TelegramSettings,
    ValidationSettings,
)

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
    "TelegramLogHandler",
    "LoggingSettings",
    "setup_logging",
    "setup_logging_from_settings",
]

