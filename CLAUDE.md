# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Retador v2.0** is a professional betting value detection system that identifies arbitrage opportunities between sharp bookmakers (Pinnacle) and soft bookmakers, then distributes picks to professional bettors via Telegram.

- **Language**: Python 3.10+ (compatible with 3.10, 3.11, 3.12)
- **Type**: Async application (asyncio)
- **Status**: Implementation in progress - core structures defined, some components pending

## Build & Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"   # Install with dev dependencies

# Run application
python -m scripts.run

# Run tests
pytest                              # All tests
pytest tests/ -v --cov=src/domain   # With coverage
pytest tests/unit/domain/ -k "validator or calculator"

# Linting & formatting
black src/ tests/
ruff check src/ tests/              # Replaced flake8
ruff check --fix src/ tests/        # Auto-fix issues
mypy src/ --strict
```

## Architecture

The system follows **Clean Architecture** as a modular monolith:

```
src/
├── domain/                    # Pure business logic
│   ├── entities/              # Pick, Surebet, Bookmaker
│   ├── value_objects/         # Odds, Profit, MarketType
│   ├── services/              # CalculationService, OppositeMarketService
│   │   └── calculators/       # Factory pattern for sharp bookmaker calculators
│   └── rules/                 # Validation chain
│       └── validators/        # OddsValidator, ProfitValidator, TimeValidator, etc.
├── application/               # Use cases and orchestration
│   ├── dto/                   # PickDTO for data transfer
│   └── handlers/              # PickHandler
├── infrastructure/            # External integrations
│   ├── api/                   # SurebetClient, RateLimiter
│   ├── cache/                 # LocalCache
│   ├── messaging/             # TelegramGateway, MessageFormatter
│   └── repositories/          # RedisRepository, base interfaces
├── config/                    # Settings, bookmakers, logging
└── shared/                    # Exceptions, constants
```

### Key External Dependencies
- **aiohttp** - Async HTTP client for API polling
- **aiogram** - Telegram Bot API wrapper
- **redis** (async) - Deduplication and cursor persistence
- **asyncpg** - PostgreSQL async driver (optional persistence)
- **orjson** - Optimized JSON serialization
- **pytz** - Timezone handling

### Core Data Flow
1. **API Polling** → Fetch surebets from apostasseguras.com with cursor-based incremental polling
2. **Validation Chain** (fail-fast order): OddsValidator → ProfitValidator → TimeValidator → DuplicateValidator (Redis) → OppositeMarketValidator
3. **Message Formatting** → Cache static parts (teams, tournament, date), compute dynamic parts (stake emoji, min_odds)
4. **Telegram Delivery** → Priority heap queue with 5-bot rotation for throughput

## Critical Architecture Decisions (from docs/03-ADRs.md)

| Decision | Rationale |
|----------|-----------|
| NO Bloom Filter | 1% false positives = lost picks = lost money for bettors |
| NO fire-and-forget Redis | Race conditions cause duplicates |
| Redis pipeline batch | Balance latency vs reliability for dedup |
| asyncio.gather (no workers) | Internal queues add latency; gather is sufficient for volume |
| Cursor incremental | Avoid reprocessing already-handled picks |
| Adaptive polling backoff | Auto-recovery from rate limits (0.5s base, 5.0s max) |
| Priority heap for Telegram | Higher-value picks sent first; graceful degradation under load |

## Domain-Specific Calculations

**Min Odds Formula** (Pinnacle-specific):
```python
min_odds = 1 / (1.01 - 1/odd_pinnacle)  # Exact cutoff at -1% profit
```

**Stake Confidence by Profit**:
- `-1% to -0.5%` → 🔴 Low
- `-0.5% to 1.5%` → 🟠 Medium-low
- `1.5% to 4%` → 🟡 Medium-high
- `>4%` → 🟢 High

## Key Configuration Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `MIN_ODDS` | 1.10 | Minimum acceptable odds |
| `MAX_ODDS` | 9.99 | Maximum acceptable odds |
| `MIN_PROFIT` | -1.0 | Minimum profit threshold |
| `MAX_PROFIT` | 25.0 | Maximum profit threshold |
| `POLLING_BASE_INTERVAL` | 0.5s | Base API poll interval |
| `POLLING_MAX_INTERVAL` | 5.0s | Max interval under backoff |

## Environment Variables

Configuration via `.env` file (see `.env.example`):

| Variable | Default | Description |
|----------|---------|-------------|
| `API_URL` | apostasseguras.com | Surebet API endpoint |
| `API_TOKEN` | - | API authentication token |
| `REDIS_HOST` | localhost | Redis server host |
| `REDIS_PORT` | 6379 | Redis server port |
| `TELEGRAM_BOT_TOKENS` | - | Comma-separated bot tokens |
| `TELEGRAM_LOG_CHANNEL` | 0 | Channel ID for logging |
| `CONCURRENT_PICKS` | 250 | Max concurrent pick processing |
| `CACHE_TTL` | 10 | Local cache TTL in seconds |

## Documentation

- `/docs/01-SRS.md` - Software Requirements Specification
- `/docs/02-PDR.md` - Preliminary Design Review
- `/docs/03-ADRs.md` - Architecture Decision Records (14 decisions)
- `/docs/04-Structure.md` - Project structure and module organization
- `/docs/05-Implemetation.md` - Implementation tasks and guidelines
- `/legacy/RetadorV6.py` - Previous implementation for reference
