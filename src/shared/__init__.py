"""Shared package - Common utilities.

Contains:
- exceptions: Custom exception classes
- constants: Global constants

Reference: docs/04-Structure.md
"""

from .exceptions import (
    RetadorError,
    InvalidOddsError,
    InvalidProfitError,
    ValidationError,
    ApiError,
    RedisError,
)
from .constants import (
    STAKE_EMOJIS,
)

__all__ = [
    "RetadorError",
    "InvalidOddsError",
    "InvalidProfitError",
    "ValidationError",
    "ApiError",
    "RedisError",
    "STAKE_EMOJIS",
]
