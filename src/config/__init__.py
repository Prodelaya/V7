"""Config package - Application configuration.

Contains:
- settings: Environment-based configuration
- bookmakers: Bookmaker configuration and channels
- logging_config: Logging setup with Telegram handler

Reference: docs/05-Implementation.md Phase 4
"""

from .settings import Settings
from .bookmakers import BookmakerConfig

__all__ = ["Settings", "BookmakerConfig"]
