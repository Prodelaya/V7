"""Unit tests for Settings with Pydantic.

Tests cover:
- Default values for all settings
- Loading from environment variables
- Validation of ranges (odds, profit, polling)
- Parsing of comma-separated token lists
- Redis URL generation
"""

import pytest
from pydantic import ValidationError

from src.config.settings import (
    APIQuerySettings,
    APISettings,
    PollingSettings,
    ProcessingSettings,
    RedisSettings,
    Settings,
    TelegramSettings,
    ValidationSettings,
)


class TestAPISettings:
    """Tests for APISettings."""

    def test_default_values(self):
        """Verify default values are set correctly."""
        settings = APISettings()

        assert settings.url == "https://api.apostasseguras.com/request"
        assert settings.token == ""
        assert settings.timeout == 30
        assert settings.retries == 3

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment variables."""
        monkeypatch.setenv("API_URL", "https://custom.api.com")
        monkeypatch.setenv("API_TOKEN", "secret_token")
        monkeypatch.setenv("API_TIMEOUT", "60")

        settings = APISettings()

        assert settings.url == "https://custom.api.com"
        assert settings.token == "secret_token"
        assert settings.timeout == 60

    def test_timeout_validation_min(self):
        """Verify timeout minimum bound."""
        with pytest.raises(ValidationError):
            APISettings(timeout=0)

    def test_timeout_validation_max(self):
        """Verify timeout maximum bound."""
        with pytest.raises(ValidationError):
            APISettings(timeout=121)

    def test_retries_validation(self):
        """Verify retries bounds."""
        with pytest.raises(ValidationError):
            APISettings(retries=0)
        with pytest.raises(ValidationError):
            APISettings(retries=11)


class TestRedisSettings:
    """Tests for RedisSettings."""

    def test_default_values(self):
        """Verify default values."""
        settings = RedisSettings()

        assert settings.host == "localhost"
        assert settings.port == 6379
        assert settings.password == ""
        assert settings.username == ""
        assert settings.db == 0
        assert settings.max_connections == 500

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment."""
        monkeypatch.setenv("REDIS_HOST", "redis.example.com")
        monkeypatch.setenv("REDIS_PORT", "6380")
        monkeypatch.setenv("REDIS_PASSWORD", "mypassword")

        settings = RedisSettings()

        assert settings.host == "redis.example.com"
        assert settings.port == 6380
        assert settings.password == "mypassword"

    def test_url_without_auth(self):
        """Verify URL generation without authentication."""
        settings = RedisSettings(host="localhost", port=6379, db=0)

        assert settings.url == "redis://localhost:6379/0"

    def test_url_with_password(self):
        """Verify URL generation with password only."""
        settings = RedisSettings(
            host="redis.example.com",
            port=6380,
            password="secret",
            db=1,
        )

        assert settings.url == "redis://:secret@redis.example.com:6380/1"

    def test_url_with_username_and_password(self):
        """Verify URL generation with username and password."""
        settings = RedisSettings(
            host="redis.example.com",
            port=6380,
            username="user",
            password="pass",
            db=2,
        )

        assert settings.url == "redis://user:pass@redis.example.com:6380/2"

    def test_port_validation(self):
        """Verify port bounds."""
        with pytest.raises(ValidationError):
            RedisSettings(port=0)
        with pytest.raises(ValidationError):
            RedisSettings(port=65536)


class TestTelegramSettings:
    """Tests for TelegramSettings."""

    def test_default_values(self):
        """Verify default values."""
        settings = TelegramSettings()

        assert settings.bot_tokens == []
        assert settings.tokens == []  # Alias
        assert settings.log_channel == 0
        assert settings.max_queue_size == 1000

    def test_parse_tokens_from_string(self, monkeypatch):
        """Verify parsing tokens from comma-separated string."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKENS", "token1,token2,token3")

        settings = TelegramSettings()

        assert settings.bot_tokens == ["token1", "token2", "token3"]
        assert settings.tokens == ["token1", "token2", "token3"]

    def test_parse_tokens_with_spaces(self, monkeypatch):
        """Verify tokens are trimmed."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKENS", "  token1  , token2 ,token3  ")

        settings = TelegramSettings()

        assert settings.bot_tokens == ["token1", "token2", "token3"]

    def test_parse_tokens_empty_entries(self, monkeypatch):
        """Verify empty entries are filtered out."""
        monkeypatch.setenv("TELEGRAM_BOT_TOKENS", "token1,,token2,  ,token3")

        settings = TelegramSettings()

        assert settings.bot_tokens == ["token1", "token2", "token3"]

    def test_log_channel_from_env(self, monkeypatch):
        """Verify log channel loading."""
        monkeypatch.setenv("TELEGRAM_LOG_CHANNEL", "-123456789")

        settings = TelegramSettings()

        assert settings.log_channel == -123456789


class TestPollingSettings:
    """Tests for PollingSettings."""

    def test_default_values(self):
        """Verify default values."""
        settings = PollingSettings()

        assert settings.base_interval == 0.5
        assert settings.max_interval == 5.0
        assert settings.requests_per_second == 2

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment."""
        monkeypatch.setenv("POLLING_BASE_INTERVAL", "1.0")
        monkeypatch.setenv("POLLING_MAX_INTERVAL", "10.0")

        settings = PollingSettings()

        assert settings.base_interval == 1.0
        assert settings.max_interval == 10.0

    def test_intervals_valid_relationship(self):
        """Verify base < max is accepted."""
        settings = PollingSettings(base_interval=0.5, max_interval=5.0)

        assert settings.base_interval < settings.max_interval

    def test_intervals_invalid_equal(self):
        """Verify base == max raises error."""
        with pytest.raises(ValidationError) as exc_info:
            PollingSettings(base_interval=5.0, max_interval=5.0)

        assert "base_interval" in str(exc_info.value)

    def test_intervals_invalid_greater(self):
        """Verify base > max raises error."""
        with pytest.raises(ValidationError) as exc_info:
            PollingSettings(base_interval=10.0, max_interval=5.0)

        assert "base_interval" in str(exc_info.value)


class TestValidationSettings:
    """Tests for ValidationSettings."""

    def test_default_values(self):
        """Verify default values from SRS RF-003."""
        settings = ValidationSettings()

        assert settings.min_odds == 1.10
        assert settings.max_odds == 9.99
        assert settings.min_profit == -1.0
        assert settings.max_profit == 25.0
        assert settings.min_event_time == 0

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment."""
        monkeypatch.setenv("MIN_ODDS", "1.5")
        monkeypatch.setenv("MAX_ODDS", "5.0")
        monkeypatch.setenv("MIN_PROFIT", "0.0")
        monkeypatch.setenv("MAX_PROFIT", "10.0")

        settings = ValidationSettings()

        assert settings.min_odds == 1.5
        assert settings.max_odds == 5.0
        assert settings.min_profit == 0.0
        assert settings.max_profit == 10.0

    def test_odds_range_valid(self):
        """Verify valid odds range is accepted."""
        settings = ValidationSettings(min_odds=1.5, max_odds=5.0)

        assert settings.min_odds < settings.max_odds

    def test_odds_range_invalid_equal(self):
        """Verify min_odds == max_odds raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationSettings(min_odds=5.0, max_odds=5.0)

        assert "min_odds" in str(exc_info.value)

    def test_odds_range_invalid_greater(self):
        """Verify min_odds > max_odds raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationSettings(min_odds=10.0, max_odds=5.0)

        assert "min_odds" in str(exc_info.value)

    def test_profit_range_valid(self):
        """Verify valid profit range is accepted."""
        settings = ValidationSettings(min_profit=-1.0, max_profit=25.0)

        assert settings.min_profit < settings.max_profit

    def test_profit_range_invalid(self):
        """Verify invalid profit range raises error."""
        with pytest.raises(ValidationError) as exc_info:
            ValidationSettings(min_profit=30.0, max_profit=25.0)

        assert "min_profit" in str(exc_info.value)


class TestAPIQuerySettings:
    """Tests for APIQuerySettings."""

    def test_default_values(self):
        """Verify default values from ADR-015."""
        settings = APIQuerySettings()

        assert settings.product == "surebets"
        assert settings.outcomes == 2
        assert settings.limit == 5000
        assert settings.min_profit == -1.0
        assert settings.max_profit == 25.0
        assert settings.min_odds == 1.10
        assert settings.max_odds == 9.99
        assert settings.hide_different_rules is True
        assert settings.start_age == "PT10M"
        assert settings.odds_format == "eu"
        assert settings.order == "created_at_desc"

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment."""
        monkeypatch.setenv("API_LIMIT", "1000")
        monkeypatch.setenv("API_PRODUCT", "valuebets")

        settings = APIQuerySettings()

        assert settings.limit == 1000
        assert settings.product == "valuebets"


class TestProcessingSettings:
    """Tests for ProcessingSettings."""

    def test_default_values(self):
        """Verify default values."""
        settings = ProcessingSettings()

        assert settings.concurrent_picks == 250
        assert settings.concurrent_requests == 100
        assert settings.cache_ttl == 10
        assert settings.cache_max_size == 2000

    def test_load_from_env(self, monkeypatch):
        """Verify loading from environment."""
        monkeypatch.setenv("CONCURRENT_PICKS", "500")
        monkeypatch.setenv("CACHE_TTL", "30")

        settings = ProcessingSettings()

        assert settings.concurrent_picks == 500
        assert settings.cache_ttl == 30


class TestSettings:
    """Tests for main Settings container."""

    def test_all_subsettings_loaded(self):
        """Verify all sub-settings are instantiated."""
        settings = Settings()

        assert isinstance(settings.api, APISettings)
        assert isinstance(settings.redis, RedisSettings)
        assert isinstance(settings.telegram, TelegramSettings)
        assert isinstance(settings.polling, PollingSettings)
        assert isinstance(settings.validation, ValidationSettings)
        assert isinstance(settings.api_query, APIQuerySettings)
        assert isinstance(settings.processing, ProcessingSettings)

    def test_sports_list_default(self):
        """Verify sports list has expected defaults."""
        settings = Settings()

        assert "Football" in settings.sports
        assert "Tennis" in settings.sports
        assert "Basketball" in settings.sports
        assert len(settings.sports) == 20

    def test_backward_compatibility_aliases(self):
        """Verify backward compatibility properties work."""
        settings = Settings()

        assert settings.concurrent_picks == settings.processing.concurrent_picks
        assert settings.concurrent_requests == settings.processing.concurrent_requests
        assert settings.cache_ttl == settings.processing.cache_ttl
        assert settings.cache_max_size == settings.processing.cache_max_size

    def test_subsettings_load_from_env(self, monkeypatch):
        """Verify sub-settings load their env vars correctly."""
        monkeypatch.setenv("API_URL", "https://test.api.com")
        monkeypatch.setenv("REDIS_HOST", "redis.test.com")
        monkeypatch.setenv("TELEGRAM_BOT_TOKENS", "bot1,bot2")

        settings = Settings()

        assert settings.api.url == "https://test.api.com"
        assert settings.redis.host == "redis.test.com"
        assert settings.telegram.tokens == ["bot1", "bot2"]

    def test_instantiation_without_file(self, monkeypatch, tmp_path):
        """Verify settings work without .env file."""
        # Change to a temp directory without .env
        monkeypatch.chdir(tmp_path)

        # Should work with defaults
        settings = Settings()

        assert settings.api.url == "https://api.apostasseguras.com/request"
