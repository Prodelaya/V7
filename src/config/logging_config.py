"""Logging configuration."""

import logging
import logging.handlers
import sys
from typing import Optional

from aiogram import Bot
from aiogram.enums import ParseMode


def setup_logging(
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    telegram_bot_token: Optional[str] = None,
    telegram_chat_id: Optional[int] = None,
) -> logging.Logger:
    """
    Configure application logging.
    
    Args:
        level: Logging level
        log_file: Optional file path for file logging
        telegram_bot_token: Optional bot token for Telegram alerts
        telegram_chat_id: Optional chat ID for Telegram alerts
        
    Returns:
        Configured root logger
    """
    # Format
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    # Root logger
    logger = logging.getLogger()
    logger.setLevel(level)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler (optional)
    if log_file:
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when="midnight",
            interval=1,
            backupCount=7,
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Telegram handler (optional)
    if telegram_bot_token and telegram_chat_id:
        telegram_handler = TelegramLogHandler(
            bot_token=telegram_bot_token,
            chat_id=telegram_chat_id,
        )
        telegram_handler.setLevel(logging.WARNING)
        telegram_handler.setFormatter(formatter)
        logger.addHandler(telegram_handler)
    
    return logger


class TelegramLogHandler(logging.Handler):
    """
    Logging handler that sends warnings and errors to Telegram.
    
    Features:
    - Deduplication (same message not sent within 30 minutes)
    - HTML formatting
    - Async sending
    """
    
    def __init__(self, bot_token: str, chat_id: int):
        super().__init__()
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.duplicate_timeout = 1800  # 30 minutes
        self._last_messages: dict = {}
    
    def emit(self, record: logging.LogRecord) -> None:
        """Send log record to Telegram."""
        import asyncio
        import html
        import time
        
        try:
            msg = self.format(record)
            current_time = time.time()
            
            # Deduplicate
            msg_hash = hash(f"{record.levelname}:{record.message}")
            if msg_hash in self._last_messages:
                if current_time - self._last_messages[msg_hash] < self.duplicate_timeout:
                    return
            
            self._last_messages[msg_hash] = current_time
            
            # Clean old entries
            self._last_messages = {
                k: v for k, v in self._last_messages.items()
                if current_time - v < self.duplicate_timeout
            }
            
            # Send async
            asyncio.create_task(self._send(msg, record.levelname))
            
        except Exception:
            self.handleError(record)
    
    async def _send(self, msg: str, level: str) -> None:
        """Send message to Telegram."""
        import html
        
        bot = Bot(token=self.bot_token)
        try:
            emoji = "🔴" if level == "ERROR" else "🟡"
            formatted = f"{emoji} <b>{level}</b>\n<pre>{html.escape(msg)}</pre>"
            
            await bot.send_message(
                chat_id=self.chat_id,
                text=formatted,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        finally:
            await bot.session.close()
