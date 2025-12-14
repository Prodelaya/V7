"""Application settings with environment variable support.

Implementation Requirements:
- Load from environment variables with defaults
- Use Pydantic or dataclasses
- Group related settings (API, Redis, Telegram, Polling, Validation)

Reference:
- docs/05-Implementation.md: Task 4.1
- docs/02-PDR.md: Section 6.1 (Variables de Entorno)
- .env.example for variable list

TODO: Implement Settings
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional


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
    max_queue_size: int = 1000


@dataclass
class PollingSettings:
    """API polling settings (from ADR-010)."""
    base_interval: float = 0.5
    max_interval: float = 5.0
    requests_per_second: int = 2


@dataclass
class ValidationSettings:
    """Pick validation settings (from SRS RF-003)."""
    min_odds: float = 1.10
    max_odds: float = 9.99
    min_profit: float = -1.0
    max_profit: float = 25.0
    min_event_time: int = 0


@dataclass
class APIQuerySettings:
    """
    API query parameters with origin filtering (from ADR-015).
    
    These parameters reduce data volume by ~60-70% by filtering at API level.
    """
    product: str = "surebets"
    outcomes: int = 2                      # Solo 2 patas
    min_profit: float = -1.0               # Profit mínimo aceptable
    max_profit: float = 25.0               # Profit máximo aceptable
    min_odds: float = 1.10                 # Cuota mínima aceptable
    max_odds: float = 9.99                 # Cuota máxima aceptable
    hide_different_rules: bool = True      # Excluir reglas conflictivas
    start_age: str = "PT10M"               # Surebets < 10 min antigüedad
    odds_format: str = "eu"                # Formato decimal explícito
    order: str = "created_at_desc"         # Ordenar por fecha descendente
    limit: int = 5000                      # Límite por request


@dataclass
class Settings:
    """
    Application settings container.
    
    Load from environment variables with fallback defaults.
    
    Environment variables (from docs/02-PDR.md Section 6.1):
    - API: API_URL, API_TOKEN, API_TIMEOUT
    - Redis: REDIS_HOST, REDIS_PORT, REDIS_PASSWORD, REDIS_USERNAME
    - Telegram: TELEGRAM_BOT_TOKENS, TELEGRAM_LOG_CHANNEL
    - Polling: POLLING_BASE_INTERVAL, POLLING_MAX_INTERVAL
    - Validation: MIN_ODDS, MAX_ODDS, MIN_PROFIT, MAX_PROFIT
    
    TODO: Implement based on:
    - Task 4.1 in docs/05-Implementation.md
    - Section 6.1 in docs/02-PDR.md
    - BotConfig in legacy/RetadorV6.py (line 250)
    """
    
    api: APISettings = field(default_factory=APISettings)
    redis: RedisSettings = field(default_factory=RedisSettings)
    telegram: TelegramSettings = field(default_factory=TelegramSettings)
    polling: PollingSettings = field(default_factory=PollingSettings)
    validation: ValidationSettings = field(default_factory=ValidationSettings)
    api_query: APIQuerySettings = field(default_factory=APIQuerySettings)
    
    # Processing settings
    concurrent_picks: int = 250
    concurrent_requests: int = 100
    cache_ttl: int = 10
    cache_max_size: int = 2000
    
    # Bookmakers and sports (moved from api_query for configuration flexibility)
    sports: List[str] = field(default_factory=lambda: [
        "AmericanFootball", "Badminton", "Baseball", "Basketball",
        "CounterStrike", "Cricket", "Darts", "E_Football", "Football",
        "Futsal", "Handball", "Hockey", "LeagueOfLegends", "Rugby",
        "Snooker", "TableTennis", "Tennis", "Valorant", "Volleyball",
        "WaterPolo"
    ])
    
    @classmethod
    def from_env(cls) -> "Settings":
        """
        Load settings from environment variables.
        
        Returns:
            Settings instance with env values
        """
        raise NotImplementedError("Settings.from_env not implemented")
