"""Logging configuration with Telegram handler.

Provides structured logging with optional Telegram alerts for WARNING+ messages.
Implements duplicate message suppression to avoid spam.

Reference:
- docs/05-Implementation.md: Task 4.3
- docs/01-SRS.md: RNF-005 (Observabilidad)
- legacy/RetadorV6.py: TelegramLogHandler (line 177)
"""

import asyncio
import html
import logging
import time
from typing import Dict, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Lazy import to avoid circular dependencies and allow testing without aiogram
Bot = None
ParseMode = None


def _get_aiogram():
    """Lazy load aiogram to avoid import issues in tests."""
    global Bot, ParseMode
    if Bot is None:
        from aiogram import Bot as AiogramBot
        from aiogram.enums import ParseMode as AiogramParseMode
        Bot = AiogramBot
        ParseMode = AiogramParseMode
    return Bot, ParseMode


class TelegramLogHandler(logging.Handler):
    """
    Logging handler that sends messages to Telegram.

    Features:
    - Only sends WARNING and above by default
    - Suppresses duplicate messages for configurable timeout period
    - Async-safe (uses asyncio.create_task for non-blocking sends)
    - HTML formatting with emoji indicators

    Usage:
        handler = TelegramLogHandler(
            bot_token="123:ABC",
            chat_id=-1001234567890,
        )
        logging.getLogger().addHandler(handler)
    """

    # Emoji mapping for log levels
    LEVEL_EMOJIS = {
        "CRITICAL": "🔴",
        "ERROR": "🔴",
        "WARNING": "🟡",
        "INFO": "🔵",
        "DEBUG": "⚪",
    }

    def __init__(
        self,
        bot_token: str,
        chat_id: int,
        min_level: int = logging.WARNING,
        duplicate_timeout: int = 1800,  # 30 minutes
    ):
        """
        Initialize handler.

        Args:
            bot_token: Telegram bot token
            chat_id: Chat/channel ID for logs
            min_level: Minimum level to send (default WARNING)
            duplicate_timeout: Seconds to suppress duplicate messages
        """
        super().__init__()
        self._bot_token = bot_token
        self._chat_id = chat_id
        self._min_level = min_level
        self._duplicate_timeout = duplicate_timeout
        self._last_messages: Dict[int, float] = {}  # {hash: timestamp}

    def _get_emoji(self, level_name: str) -> str:
        """Get emoji for log level."""
        return self.LEVEL_EMOJIS.get(level_name, "⚪")

    def _is_duplicate(self, msg_hash: int, current_time: float) -> bool:
        """
        Check if message is a duplicate within timeout.

        Also cleans up old entries from the cache.
        """
        # Clean old entries
        self._last_messages = {
            k: v for k, v in self._last_messages.items()
            if current_time - v < self._duplicate_timeout
        }

        # Check if duplicate
        if msg_hash in self._last_messages:
            last_time = self._last_messages[msg_hash]
            if current_time - last_time < self._duplicate_timeout:
                return True

        return False

    def _format_message(self, record: logging.LogRecord) -> str:
        """Format log record as HTML for Telegram."""
        emoji = self._get_emoji(record.levelname)
        message = self.format(record)
        escaped_message = html.escape(message)
        return f"{emoji} <b>{record.levelname}</b>\n<pre>{escaped_message}</pre>"

    async def _send_async(self, message: str) -> None:
        """Send message to Telegram asynchronously."""
        try:
            BotClass, ParseModeEnum = _get_aiogram()
            bot = BotClass(token=self._bot_token)
            try:
                await bot.send_message(
                    chat_id=self._chat_id,
                    text=message,
                    parse_mode=ParseModeEnum.HTML,
                    disable_web_page_preview=True,
                )
            finally:
                await bot.session.close()
        except Exception as e:
            # Print to stderr but don't propagate - logs should never break the app
            print(f"[TelegramLogHandler] Failed to send: {e}")

    def emit(self, record: logging.LogRecord) -> None:
        """
        Send log record to Telegram if level >= min_level.

        Suppresses duplicates within the configured timeout.
        """
        # Filter by level
        if record.levelno < self._min_level:
            return

        try:
            current_time = time.time()

            # Create hash from level + message for duplicate detection
            msg_base = f"{record.levelname}:{record.getMessage()}"
            msg_hash = hash(msg_base)

            # Check for duplicates
            if self._is_duplicate(msg_hash, current_time):
                return

            # Record this message
            self._last_messages[msg_hash] = current_time

            # Format and send
            formatted_message = self._format_message(record)

            # Schedule async send (fire-and-forget for logging)
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(self._send_async(formatted_message))
            except RuntimeError:
                # No running loop - we're in sync context
                # Try to create a new loop and run it
                try:
                    asyncio.run(self._send_async(formatted_message))
                except Exception:
                    # If all else fails, just print the error
                    print(f"[TelegramLogHandler] Cannot send (no event loop): {formatted_message[:100]}...")

        except Exception as e:
            # Never let logging handler raise - print to stderr instead
            print(f"[TelegramLogHandler] Error in emit: {e}")


class LoggingSettings(BaseSettings):
    """Logging configuration settings."""

    model_config = SettingsConfigDict(
        env_prefix="LOG_",
        extra="ignore",
    )

    level: str = Field(
        default="INFO",
        description="Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
    )
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string",
    )
    telegram_enabled: bool = Field(
        default=True,
        description="Enable Telegram alerts for errors",
    )
    telegram_min_level: str = Field(
        default="WARNING",
        description="Minimum level to send to Telegram",
    )
    duplicate_timeout: int = Field(
        default=1800,
        ge=60,
        le=86400,
        description="Seconds to suppress duplicate log messages",
    )

    @field_validator("level", "telegram_min_level")
    @classmethod
    def validate_level(cls, v: str) -> str:
        """Validate and normalize log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        upper = v.upper()
        if upper not in valid:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid}")
        return upper

    def get_level_int(self) -> int:
        """Convert level string to logging constant."""
        return getattr(logging, self.level)

    def get_telegram_min_level_int(self) -> int:
        """Convert telegram_min_level string to logging constant."""
        return getattr(logging, self.telegram_min_level)


def setup_logging(
    level: int = logging.INFO,
    log_format: Optional[str] = None,
    telegram_token: Optional[str] = None,
    telegram_chat_id: Optional[int] = None,
    telegram_min_level: int = logging.WARNING,
    duplicate_timeout: int = 1800,
) -> logging.Logger:
    """
    Configure application logging.

    Sets up:
    - Console handler with structured format
    - Optional Telegram handler for alerts (WARNING+)

    Args:
        level: Base logging level (default INFO)
        log_format: Log format string (default includes timestamp, name, level, message)
        telegram_token: Bot token for Telegram alerts (optional)
        telegram_chat_id: Chat ID for Telegram alerts (optional)
        telegram_min_level: Minimum level to send to Telegram (default WARNING)
        duplicate_timeout: Seconds to suppress duplicate Telegram messages

    Returns:
        Configured root logger
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Get root logger
    root_logger = logging.getLogger()

    # Clear existing handlers to avoid duplicates (especially important in tests)
    root_logger.handlers.clear()

    # Set base level
    root_logger.setLevel(level)

    # Create formatter
    formatter = logging.Formatter(log_format)

    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add Telegram handler if configured
    if telegram_token and telegram_chat_id:
        telegram_handler = TelegramLogHandler(
            bot_token=telegram_token,
            chat_id=telegram_chat_id,
            min_level=telegram_min_level,
            duplicate_timeout=duplicate_timeout,
        )
        telegram_handler.setFormatter(formatter)
        root_logger.addHandler(telegram_handler)

    return root_logger


def setup_logging_from_settings(
    settings: LoggingSettings,
    telegram_token: Optional[str] = None,
    telegram_chat_id: Optional[int] = None,
) -> logging.Logger:
    """
    Configure logging from LoggingSettings.

    Convenience wrapper around setup_logging() that uses LoggingSettings.

    Args:
        settings: LoggingSettings instance
        telegram_token: Bot token (from TelegramSettings.bot_tokens[0])
        telegram_chat_id: Chat ID (from TelegramSettings.log_channel)

    Returns:
        Configured root logger
    """
    # Only enable Telegram if settings allow and credentials provided
    effective_token = telegram_token if settings.telegram_enabled else None
    effective_chat_id = telegram_chat_id if settings.telegram_enabled else None

    return setup_logging(
        level=settings.get_level_int(),
        log_format=settings.format,
        telegram_token=effective_token,
        telegram_chat_id=effective_chat_id,
        telegram_min_level=settings.get_telegram_min_level_int(),
        duplicate_timeout=settings.duplicate_timeout,
    )
