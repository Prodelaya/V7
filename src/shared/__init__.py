"""Shared package - Common utilities.

Contains:
- exceptions: Custom exception classes (PDR Section 7.1)
- constants: Global constants

Reference: docs/04-Structure.md
"""

from .exceptions import (
    # Base
    RetadorError,
    # Domain
    DomainError,
    InvalidOddsError,
    InvalidProfitError,
    InvalidMarketError,
    # Infrastructure
    InfrastructureError,
    ApiError,
    ApiConnectionError,
    ApiRateLimitError,
    RedisError,
    RedisConnectionError,
    TelegramError,
    TelegramSendError,
    # Application
    ApplicationError,
    ValidationError,
    ProcessingError,
)
from .constants import (
    STAKE_EMOJIS,
)

__all__ = [
    # Base
    "RetadorError",
    # Domain
    "DomainError",
    "InvalidOddsError",
    "InvalidProfitError",
    "InvalidMarketError",
    # Infrastructure
    "InfrastructureError",
    "ApiError",
    "ApiConnectionError",
    "ApiRateLimitError",
    "RedisError",
    "RedisConnectionError",
    "TelegramError",
    "TelegramSendError",
    # Application
    "ApplicationError",
    "ValidationError",
    "ProcessingError",
    # Constants
    "STAKE_EMOJIS",
]
