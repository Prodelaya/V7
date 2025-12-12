"""Application settings with environment variable support."""

import os
from dataclasses import dataclass, field
from typing import List


@dataclass
class APISettings:
    """API connection settings."""
    url: str = "https://api.apostasseguras.com/request"
    token: str = ""
    timeout: int = 30
    retries: int = 3


@dataclass
class RedisSettings:
    """Redis connection settings."""
    host: str = "localhost"
    port: int = 6379
    password: str = ""
    username: str = ""
    db: int = 0
    max_connections: int = 500


@dataclass
class TelegramSettings:
    """Telegram bot settings."""
    tokens: List[str] = field(default_factory=list)
    log_channel_id: int = 0


@dataclass
class PollingSettings:
    """API polling settings."""
    base_interval: float = 0.5
    max_interval: float = 5.0
    requests_per_second: int = 2


@dataclass
class ValidationSettings:
    """Pick validation settings."""
    min_odds: float = 1.10
    max_odds: float = 9.99
    min_profit: float = -1.0
    max_profit: float = 25.0
    min_event_time: int = 0


@dataclass
class Settings:
    """
    Application settings container.
    
    Load from environment variables with fallback defaults.
    """
    
    api: APISettings = field(default_factory=APISettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    polling: PollingSettings = field(default_factory=PollingSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)
    
    # Processing settings
    concurrent_picks: int = 250
    concurrent_requests: int = 100
    cache_ttl: int = 10
    cache_max_size: int = 2000
    
    # API query settings
    limit: int = 5000
    product: str = "surebets"
    sports: List[str] = field(default_factory=lambda: [
        "AmericanFootball", "Badminton", "Baseball", "Basketball",
        "CounterStrike", "Cricket", "Darts", "E_Football", "Football",
        "Futsal", "Handball", "Hockey", "LeagueOfLegends", "Rugby",
        "Snooker", "TableTennis", "Tennis", "Valorant", "Volleyball",
        "WaterPolo"
    ])
    
    @classmethod
    def from_env(cls) -> "Settings":
        """Load settings from environment variables."""
        settings = cls()
        
        # API settings
        settings.api.url = os.getenv("API_URL", settings.api.url)
        settings.api.token = os.getenv("API_TOKEN", "")
        settings.api.timeout = int(os.getenv("API_TIMEOUT", "30"))
        
        # Redis settings
        settings.redis.host = os.getenv("REDIS_HOST", "localhost")
        settings.redis.port = int(os.getenv("REDIS_PORT", "6379"))
        settings.redis.password = os.getenv("REDIS_PASSWORD", "")
        settings.redis.username = os.getenv("REDIS_USERNAME", "")
        
        # Telegram settings
        tokens = os.getenv("TELEGRAM_BOT_TOKENS", "")
        if tokens:
            settings.telegram.tokens = tokens.split(",")
        settings.telegram.log_channel_id = int(
            os.getenv("TELEGRAM_LOG_CHANNEL", "0")
        )
        
        # Polling settings
        settings.polling.base_interval = float(
            os.getenv("POLLING_BASE_INTERVAL", "0.5")
        )
        settings.polling.max_interval = float(
            os.getenv("POLLING_MAX_INTERVAL", "5.0")
        )
        
        # Validation settings
        settings.validation.min_odds = float(os.getenv("MIN_ODDS", "1.10"))
        settings.validation.max_odds = float(os.getenv("MAX_ODDS", "9.99"))
        settings.validation.min_profit = float(os.getenv("MIN_PROFIT", "-1.0"))
        settings.validation.max_profit = float(os.getenv("MAX_PROFIT", "25.0"))
        
        return settings
