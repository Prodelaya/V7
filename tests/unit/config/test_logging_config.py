"""Unit tests for logging_config module.

Tests cover:
- TelegramLogHandler constructor and configuration
- Level filtering
- Duplicate message suppression
- setup_logging function
- LoggingSettings Pydantic model
"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest
from pydantic import ValidationError

from src.config.logging_config import (
    LoggingSettings,
    TelegramLogHandler,
    setup_logging,
    setup_logging_from_settings,
)


class TestTelegramLogHandler:
    """Tests for TelegramLogHandler."""

    @pytest.fixture
    def handler(self):
        """Create a handler for testing."""
        return TelegramLogHandler(
            bot_token="test:token123",
            chat_id=-1001234567890,
            min_level=logging.WARNING,
            duplicate_timeout=1800,
        )

    def test_constructor_stores_config(self):
        """Verify constructor stores configuration."""
        handler = TelegramLogHandler(
            bot_token="test:token",
            chat_id=-1001234567890,
            min_level=logging.ERROR,
            duplicate_timeout=600,
        )
        assert handler._bot_token == "test:token"
        assert handler._chat_id == -1001234567890
        assert handler._min_level == logging.ERROR
        assert handler._duplicate_timeout == 600

    def test_default_min_level_is_warning(self):
        """Verify default min_level is WARNING."""
        handler = TelegramLogHandler(
            bot_token="test:token",
            chat_id=-123,
        )
        assert handler._min_level == logging.WARNING

    def test_default_duplicate_timeout(self):
        """Verify default duplicate_timeout is 1800 seconds."""
        handler = TelegramLogHandler(
            bot_token="test:token",
            chat_id=-123,
        )
        assert handler._duplicate_timeout == 1800

    def test_get_emoji_for_error(self, handler):
        """Verify correct emoji for ERROR level."""
        assert handler._get_emoji("ERROR") == "🔴"

    def test_get_emoji_for_critical(self, handler):
        """Verify correct emoji for CRITICAL level."""
        assert handler._get_emoji("CRITICAL") == "🔴"

    def test_get_emoji_for_warning(self, handler):
        """Verify correct emoji for WARNING level."""
        assert handler._get_emoji("WARNING") == "🟡"

    def test_get_emoji_for_info(self, handler):
        """Verify correct emoji for INFO level."""
        assert handler._get_emoji("INFO") == "🔵"

    def test_get_emoji_for_unknown(self, handler):
        """Verify default emoji for unknown level."""
        assert handler._get_emoji("UNKNOWN") == "⚪"

    def test_filters_info_level(self, handler):
        """Verify INFO messages are ignored when min_level is WARNING."""
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Test info message",
            args=(),
            exc_info=None,
        )

        # emit should return early without sending
        with patch.object(handler, '_send_async') as mock_send:
            handler.emit(record)
            mock_send.assert_not_called()

    def test_processes_warning_level(self, handler):
        """Verify WARNING messages are processed."""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Test warning message",
            args=(),
            exc_info=None,
        )

        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()
            handler.emit(record)
            # Verify create_task was called (message was processed)
            mock_loop.return_value.create_task.assert_called_once()

    def test_processes_error_level(self, handler):
        """Verify ERROR messages are processed."""
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="",
            lineno=0,
            msg="Test error message",
            args=(),
            exc_info=None,
        )

        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()
            handler.emit(record)
            mock_loop.return_value.create_task.assert_called_once()

    def test_duplicate_suppression_within_timeout(self, handler):
        """Verify same message is suppressed within timeout."""
        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Duplicate test message",
            args=(),
            exc_info=None,
        )

        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()

            # First emit should send
            handler.emit(record)
            assert mock_loop.return_value.create_task.call_count == 1

            # Second emit (same message) should be suppressed
            handler.emit(record)
            assert mock_loop.return_value.create_task.call_count == 1  # Still 1

    def test_duplicate_allowed_after_timeout(self, handler):
        """Verify message is sent again after timeout expires."""
        handler._duplicate_timeout = 1  # 1 second for faster test

        record = logging.LogRecord(
            name="test",
            level=logging.WARNING,
            pathname="",
            lineno=0,
            msg="Timeout test message",
            args=(),
            exc_info=None,
        )

        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()

            # First emit
            handler.emit(record)
            assert mock_loop.return_value.create_task.call_count == 1

            # Wait for timeout
            time.sleep(1.1)

            # Second emit should send again
            handler.emit(record)
            assert mock_loop.return_value.create_task.call_count == 2

    def test_different_messages_not_suppressed(self, handler):
        """Verify different messages are not treated as duplicates."""
        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()

            record1 = logging.LogRecord(
                name="test", level=logging.WARNING, pathname="", lineno=0,
                msg="First message", args=(), exc_info=None,
            )
            record2 = logging.LogRecord(
                name="test", level=logging.WARNING, pathname="", lineno=0,
                msg="Second message", args=(), exc_info=None,
            )

            handler.emit(record1)
            handler.emit(record2)

            assert mock_loop.return_value.create_task.call_count == 2

    def test_cleans_old_messages(self, handler):
        """Verify old entries are cleaned from _last_messages."""
        handler._duplicate_timeout = 1  # 1 second

        # Add an old entry directly
        old_hash = hash("old:message")
        handler._last_messages[old_hash] = time.time() - 2  # 2 seconds ago

        # Emit a new message to trigger cleanup
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="New message", args=(), exc_info=None,
        )

        with patch('asyncio.get_running_loop') as mock_loop:
            mock_loop.return_value.create_task = MagicMock()
            handler.emit(record)

        # Old entry should be cleaned
        assert old_hash not in handler._last_messages

    def test_handles_no_event_loop_gracefully(self, handler):
        """Verify handler doesn't crash when no event loop is running."""
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="No loop test", args=(), exc_info=None,
        )

        # Mock get_running_loop to raise RuntimeError (no loop)
        with patch('asyncio.get_running_loop', side_effect=RuntimeError("no running loop")):
            with patch('asyncio.run') as mock_run:
                # Should not raise
                handler.emit(record)
                # asyncio.run should be called as fallback
                mock_run.assert_called_once()

    def test_format_message_contains_emoji_and_level(self, handler):
        """Verify formatted message contains emoji and level."""
        record = logging.LogRecord(
            name="test", level=logging.ERROR, pathname="", lineno=0,
            msg="Test message", args=(), exc_info=None,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))

        formatted = handler._format_message(record)

        assert "🔴" in formatted
        assert "<b>ERROR</b>" in formatted
        assert "Test message" in formatted
        assert "<pre>" in formatted

    def test_format_message_escapes_html(self, handler):
        """Verify HTML in messages is escaped."""
        record = logging.LogRecord(
            name="test", level=logging.WARNING, pathname="", lineno=0,
            msg="<script>alert('xss')</script>", args=(), exc_info=None,
        )
        handler.setFormatter(logging.Formatter("%(message)s"))

        formatted = handler._format_message(record)

        assert "<script>" not in formatted
        assert "&lt;script&gt;" in formatted


class TestSetupLogging:
    """Tests for setup_logging function."""

    @pytest.fixture(autouse=True)
    def cleanup_handlers(self):
        """Clean up handlers after each test."""
        yield
        # Clear all handlers from root logger
        logging.getLogger().handlers.clear()

    def test_returns_root_logger(self):
        """Verify function returns root logger."""
        logger = setup_logging()
        assert logger == logging.getLogger()

    def test_adds_console_handler(self):
        """Verify console handler is added."""
        setup_logging()
        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

    def test_sets_log_level(self):
        """Verify log level is set correctly."""
        logger = setup_logging(level=logging.DEBUG)
        assert logger.level == logging.DEBUG

    def test_sets_warning_level(self):
        """Verify WARNING level is set correctly."""
        logger = setup_logging(level=logging.WARNING)
        assert logger.level == logging.WARNING

    def test_adds_telegram_handler_when_configured(self):
        """Verify Telegram handler added with valid credentials."""
        setup_logging(
            telegram_token="test:token",
            telegram_chat_id=-1001234567890,
        )
        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]
        assert len(telegram_handlers) == 1

    def test_telegram_handler_has_correct_config(self):
        """Verify Telegram handler has correct configuration."""
        setup_logging(
            telegram_token="my:token",
            telegram_chat_id=-999,
            telegram_min_level=logging.ERROR,
            duplicate_timeout=600,
        )
        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]

        assert len(telegram_handlers) == 1
        handler = telegram_handlers[0]
        assert handler._bot_token == "my:token"
        assert handler._chat_id == -999
        assert handler._min_level == logging.ERROR
        assert handler._duplicate_timeout == 600

    def test_no_telegram_handler_without_token(self):
        """Verify no Telegram handler without token."""
        setup_logging(telegram_token=None, telegram_chat_id=-123)
        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]
        assert len(telegram_handlers) == 0

    def test_no_telegram_handler_without_chat_id(self):
        """Verify no Telegram handler without chat_id."""
        setup_logging(telegram_token="test:token", telegram_chat_id=None)
        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]
        assert len(telegram_handlers) == 0

    def test_clears_existing_handlers(self):
        """Verify existing handlers are cleared before setup."""
        # Add a handler manually
        root = logging.getLogger()
        dummy_handler = logging.StreamHandler()
        root.addHandler(dummy_handler)

        # Call setup_logging
        setup_logging()

        # Dummy handler should be gone
        assert dummy_handler not in root.handlers

    def test_custom_format(self):
        """Verify custom format is applied."""
        custom_format = "%(levelname)s: %(message)s"
        setup_logging(log_format=custom_format)

        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert len(stream_handlers) >= 1

        # Check formatter
        fmt = stream_handlers[0].formatter._fmt
        assert fmt == custom_format


class TestLoggingSettings:
    """Tests for LoggingSettings Pydantic model."""

    def test_default_values(self):
        """Verify default configuration."""
        settings = LoggingSettings()
        assert settings.level == "INFO"
        assert settings.telegram_enabled is True
        assert settings.telegram_min_level == "WARNING"
        assert settings.duplicate_timeout == 1800

    def test_level_validation_valid_uppercase(self):
        """Verify uppercase levels are accepted."""
        for level in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
            settings = LoggingSettings(level=level)
            assert settings.level == level

    def test_level_validation_case_insensitive(self):
        """Verify level is case-insensitive."""
        settings = LoggingSettings(level="debug")
        assert settings.level == "DEBUG"

    def test_level_validation_invalid(self):
        """Verify invalid level raises error."""
        with pytest.raises(ValidationError):
            LoggingSettings(level="TRACE")

    def test_telegram_min_level_validation(self):
        """Verify telegram_min_level validation."""
        settings = LoggingSettings(telegram_min_level="error")
        assert settings.telegram_min_level == "ERROR"

    def test_get_level_int_info(self):
        """Verify INFO level is converted correctly."""
        settings = LoggingSettings(level="INFO")
        assert settings.get_level_int() == logging.INFO

    def test_get_level_int_warning(self):
        """Verify WARNING level is converted correctly."""
        settings = LoggingSettings(level="WARNING")
        assert settings.get_level_int() == logging.WARNING

    def test_get_telegram_min_level_int(self):
        """Verify telegram_min_level is converted correctly."""
        settings = LoggingSettings(telegram_min_level="ERROR")
        assert settings.get_telegram_min_level_int() == logging.ERROR

    def test_duplicate_timeout_min_bound(self):
        """Verify duplicate_timeout minimum bound (60)."""
        with pytest.raises(ValidationError):
            LoggingSettings(duplicate_timeout=30)

    def test_duplicate_timeout_max_bound(self):
        """Verify duplicate_timeout maximum bound (86400)."""
        with pytest.raises(ValidationError):
            LoggingSettings(duplicate_timeout=100000)

    def test_duplicate_timeout_valid_range(self):
        """Verify valid duplicate_timeout values are accepted."""
        settings = LoggingSettings(duplicate_timeout=3600)
        assert settings.duplicate_timeout == 3600

    def test_telegram_enabled_false(self):
        """Verify telegram_enabled can be set to False."""
        settings = LoggingSettings(telegram_enabled=False)
        assert settings.telegram_enabled is False

    def test_custom_format(self):
        """Verify custom format is stored."""
        custom = "%(message)s"
        settings = LoggingSettings(format=custom)
        assert settings.format == custom


class TestSetupLoggingFromSettings:
    """Tests for setup_logging_from_settings function."""

    @pytest.fixture(autouse=True)
    def cleanup_handlers(self):
        """Clean up handlers after each test."""
        yield
        logging.getLogger().handlers.clear()

    def test_uses_settings_level(self):
        """Verify level from settings is used."""
        settings = LoggingSettings(level="DEBUG")
        logger = setup_logging_from_settings(settings)
        assert logger.level == logging.DEBUG

    def test_uses_settings_format(self):
        """Verify format from settings is used."""
        custom_format = "%(levelname)s: %(message)s"
        settings = LoggingSettings(format=custom_format)
        setup_logging_from_settings(settings)

        root = logging.getLogger()
        stream_handlers = [h for h in root.handlers if isinstance(h, logging.StreamHandler)]
        assert stream_handlers[0].formatter._fmt == custom_format

    def test_telegram_disabled(self):
        """Verify Telegram handler not added when disabled in settings."""
        settings = LoggingSettings(telegram_enabled=False)
        setup_logging_from_settings(
            settings,
            telegram_token="test:token",
            telegram_chat_id=-123,
        )

        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]
        assert len(telegram_handlers) == 0

    def test_telegram_enabled(self):
        """Verify Telegram handler added when enabled in settings."""
        settings = LoggingSettings(telegram_enabled=True)
        setup_logging_from_settings(
            settings,
            telegram_token="test:token",
            telegram_chat_id=-123,
        )

        root = logging.getLogger()
        telegram_handlers = [h for h in root.handlers if isinstance(h, TelegramLogHandler)]
        assert len(telegram_handlers) == 1
