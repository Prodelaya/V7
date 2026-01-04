"""Application settings with Pydantic Settings.

Centralized configuration for Retador v2.0 using pydantic-settings.
All settings are loaded from environment variables with sensible defaults.

Reference:
- docs/05-Implementation.md: Task 4.1
- docs/02-PDR.md: Section 6.1 (Variables de Entorno)
- .env.example for complete variable list
"""

import logging
from typing import List

from pydantic import Field, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


logger = logging.getLogger(__name__)


class APISettings(BaseSettings):
    """API connection settings.
    
    Reads from environment variables with prefix API_.
    Example: API_URL, API_TOKEN, API_TIMEOUT
    """
    
    model_config = SettingsConfigDict(
        env_prefix="API_",
        extra="ignore",
    )
    
    url: str = Field(
        default="https://api.apostasseguras.com/request",
        description="Surebet API endpoint URL",
    )
    token: str = Field(
        default="",
        description="API authentication token (required in production)",
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=120,
        description="Request timeout in seconds",
    )
    retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Number of retry attempts",
    )
    
    @field_validator("token")
    @classmethod
    def warn_empty_token(cls, v: str) -> str:
        """Warn if token is empty (should be set in production)."""
        if not v:
            logger.warning("API_TOKEN is not set - API requests will fail")
        return v


class RedisSettings(BaseSettings):
    """Redis connection settings.
    
    Reads from environment variables with prefix REDIS_.
    Example: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD
    """
    
    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        extra="ignore",
    )
    
    host: str = Field(default="localhost", description="Redis server hostname")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    password: str = Field(default="", description="Redis password")
    username: str = Field(default="", description="Redis username (Redis 6+)")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    max_connections: int = Field(
        default=500,
        ge=1,
        le=10000,
        description="Maximum connection pool size",
    )
    
    @property
    def url(self) -> str:
        """Generate Redis connection URL."""
        auth = ""
        if self.password:
            if self.username:
                auth = f"{self.username}:{self.password}@"
            else:
                auth = f":{self.password}@"
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"


class TelegramSettings(BaseSettings):
    """Telegram bot settings.
    
    Reads from environment variables with prefix TELEGRAM_.
    TELEGRAM_BOT_TOKENS should be comma-separated list of tokens.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="TELEGRAM_",
        extra="ignore",
    )
    
    # Store as string to avoid JSON parsing issues with List[str]
    # Uses validation_alias to map TELEGRAM_BOT_TOKENS env var
    bot_tokens_str: str = Field(
        default="",
        validation_alias="TELEGRAM_BOT_TOKENS",
        description="Comma-separated list of bot tokens",
    )
    log_channel: int = Field(
        default=0,
        description="Channel ID for error logs",
    )
    max_queue_size: int = Field(
        default=1000,
        ge=1,
        le=10000,
        description="Maximum messages in priority queue",
    )
    
    @property
    def bot_tokens(self) -> List[str]:
        """Parse comma-separated tokens string into list."""
        if not self.bot_tokens_str:
            return []
        return [t.strip() for t in self.bot_tokens_str.split(",") if t.strip()]
    
    @property
    def tokens(self) -> List[str]:
        """Alias for bot_tokens for backwards compatibility."""
        return self.bot_tokens


class PollingSettings(BaseSettings):
    """API polling settings (from ADR-010).
    
    Implements adaptive polling with exponential backoff.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="POLLING_",
        extra="ignore",
    )
    
    base_interval: float = Field(
        default=0.5,
        ge=0.1,
        le=10.0,
        description="Base polling interval in seconds",
    )
    max_interval: float = Field(
        default=5.0,
        ge=0.5,
        le=60.0,
        description="Maximum polling interval (backoff limit)",
    )
    requests_per_second: int = Field(
        default=2,
        ge=1,
        le=10,
        description="API rate limit (requests/second)",
    )
    
    @model_validator(mode="after")
    def validate_intervals(self) -> "PollingSettings":
        """Ensure base_interval < max_interval."""
        if self.base_interval >= self.max_interval:
            raise ValueError(
                f"base_interval ({self.base_interval}) must be less than "
                f"max_interval ({self.max_interval})"
            )
        return self


class ValidationSettings(BaseSettings):
    """Pick validation settings (from SRS RF-003).
    
    Defines acceptable ranges for odds, profit, and event timing.
    """
    
    model_config = SettingsConfigDict(extra="ignore")
    
    min_odds: float = Field(
        default=1.10,
        ge=1.01,
        le=100.0,
        description="Minimum acceptable odds",
    )
    max_odds: float = Field(
        default=9.99,
        ge=1.01,
        le=1000.0,
        description="Maximum acceptable odds",
    )
    min_profit: float = Field(
        default=-1.0,
        ge=-100.0,
        le=100.0,
        description="Minimum acceptable profit percentage",
    )
    max_profit: float = Field(
        default=25.0,
        ge=-100.0,
        le=100.0,
        description="Maximum acceptable profit percentage",
    )
    min_event_time: int = Field(
        default=0,
        ge=0,
        description="Minimum seconds until event start",
    )
    
    @model_validator(mode="after")
    def validate_ranges(self) -> "ValidationSettings":
        """Ensure min < max for odds and profit ranges."""
        if self.min_odds >= self.max_odds:
            raise ValueError(
                f"min_odds ({self.min_odds}) must be less than "
                f"max_odds ({self.max_odds})"
            )
        if self.min_profit >= self.max_profit:
            raise ValueError(
                f"min_profit ({self.min_profit}) must be less than "
                f"max_profit ({self.max_profit})"
            )
        return self


class APIQuerySettings(BaseSettings):
    """API query parameters with origin filtering (from ADR-015).
    
    These parameters reduce data volume by ~60-70% by filtering at API level.
    """
    
    model_config = SettingsConfigDict(
        env_prefix="API_",
        extra="ignore",
    )
    
    product: str = Field(default="surebets", description="API product type")
    outcomes: int = Field(default=2, ge=2, le=10, description="Number of prongs (2=surebet)")
    limit: int = Field(default=5000, ge=1, le=10000, description="Records per request")
    
    # Filtering parameters (use validation settings as defaults)
    min_profit: float = Field(default=-1.0, description="Minimum profit filter")
    max_profit: float = Field(default=25.0, description="Maximum profit filter")
    min_odds: float = Field(default=1.10, description="Minimum odds filter")
    max_odds: float = Field(default=9.99, description="Maximum odds filter")
    
    # Static parameters
    hide_different_rules: bool = Field(
        default=True,
        description="Exclude surebets with conflicting sport rules",
    )
    start_age: str = Field(
        default="PT10M",
        description="Maximum age of surebets (ISO 8601 duration)",
    )
    odds_format: str = Field(default="eu", description="Odds format (eu=decimal)")
    order: str = Field(default="created_at_desc", description="Sort order")


class ProcessingSettings(BaseSettings):
    """Processing and concurrency settings."""
    
    model_config = SettingsConfigDict(extra="ignore")
    
    concurrent_picks: int = Field(
        default=250,
        ge=1,
        le=1000,
        description="Parallel pick processing limit",
    )
    concurrent_requests: int = Field(
        default=100,
        ge=1,
        le=500,
        description="Concurrent HTTP request limit",
    )
    cache_ttl: int = Field(
        default=10,
        ge=1,
        le=3600,
        description="Cache TTL in seconds",
    )
    cache_max_size: int = Field(
        default=2000,
        ge=100,
        le=100000,
        description="Maximum cache entries",
    )


class Settings(BaseSettings):
    """Main application settings container.
    
    Aggregates all sub-settings and loads from environment variables.
    
    Usage:
        settings = Settings()
        print(settings.api.url)
        print(settings.redis.host)
        print(settings.telegram.tokens)
    
    Environment variables (from docs/02-PDR.md Section 6.1):
    - API: API_URL, API_TOKEN, API_TIMEOUT
    - Redis: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_USERNAME
    - Telegram: TELEGRAM_BOT_TOKENS, TELEGRAM_LOG_CHANNEL
    - Polling: POLLING_BASE_INTERVAL, POLLING_MAX_INTERVAL
    - Validation: MIN_ODDS, MAX_ODDS, MIN_PROFIT, MAX_PROFIT
    """
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )
    
    # Sub-settings (loaded automatically from their respective env vars)
    api: APISettings = Field(default_factory=APISettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    telegram: TelegramSettings = Field(default_factory=TelegramSettings)
    polling: PollingSettings = Field(default_factory=PollingSettings)
    validation: ValidationSettings = Field(default_factory=ValidationSettings)
    api_query: APIQuerySettings = Field(default_factory=APIQuerySettings)
    processing: ProcessingSettings = Field(default_factory=ProcessingSettings)
    
    # Sports list (rarely changes, loaded from .env if needed)
    sports: List[str] = Field(
        default_factory=lambda: [
            "AmericanFootball", "Badminton", "Baseball", "Basketball",
            "CounterStrike", "Cricket", "Darts", "E_Football", "Football",
            "Futsal", "Handball", "Hockey", "LeagueOfLegends", "Rugby",
            "Snooker", "TableTennis", "Tennis", "Valorant", "Volleyball",
            "WaterPolo",
        ]
    )
    
    # Backward compatibility aliases
    @property
    def concurrent_picks(self) -> int:
        """Alias for processing.concurrent_picks."""
        return self.processing.concurrent_picks
    
    @property
    def concurrent_requests(self) -> int:
        """Alias for processing.concurrent_requests."""
        return self.processing.concurrent_requests
    
    @property
    def cache_ttl(self) -> int:
        """Alias for processing.cache_ttl."""
        return self.processing.cache_ttl
    
    @property
    def cache_max_size(self) -> int:
        """Alias for processing.cache_max_size."""
        return self.processing.cache_max_size
