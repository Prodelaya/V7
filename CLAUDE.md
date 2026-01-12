# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Retador v2.0** is a professional betting value detection system that identifies arbitrage opportunities between sharp bookmakers (Pinnacle) and soft bookmakers, then distributes picks to professional bettors via Telegram.

- **Language**: Python 3.10+ (compatible with 3.10, 3.11, 3.12)
- **Type**: Async application (asyncio)
- **Status**: **88% implemented** (49/56 tasks complete) - Phase 7 (Integration) pending

## Build & Development Commands

```bash
# Setup
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -e ".[dev]"   # Install with dev dependencies

# Run tests
pytest                              # All tests
pytest tests/ -v --cov=src/domain   # With coverage
pytest tests/unit/domain/ -k "validator or calculator"  # Specific tests

# Linting & formatting
black src/ tests/
ruff check src/ tests/              # Lint check
ruff check --fix src/ tests/        # Auto-fix issues
mypy src/ --strict                  # Type checking

# Docker (when implemented)
docker-compose up -d                # Production
docker-compose -f docker-compose.dev.yml up  # Development
```

## Architecture

The system follows **Clean Architecture** as a modular monolith:

```
src/
├── domain/                    # Pure business logic (NO external dependencies)
│   ├── entities/              # Pick, Surebet, Bookmaker
│   ├── value_objects/         # Odds, Profit, MarketType
│   ├── services/              # CalculationService, OppositeMarketService
│   │   └── calculators/       # Factory pattern for sharp bookmaker calculators
│   └── rules/                 # Validation chain
│       └── validators/        # OddsValidator, ProfitValidator, TimeValidator, etc.
├── application/               # Use cases and orchestration
│   ├── dto/                   # PickDTO for data transfer
│   └── handlers/              # PickHandler (orchestrates entire flow)
├── infrastructure/            # External integrations
│   ├── api/                   # SurebetClient, RateLimiter
│   ├── cache/                 # LocalCache
│   ├── messaging/             # TelegramGateway, MessageFormatter
│   └── repositories/          # RedisRepository, base interfaces
├── config/                    # Settings, bookmakers, logging
├── shared/                    # Exceptions, constants
├── subscriptions/             # Subscription system module (future)
└── web/                       # Landing page and webhooks (future)
```

### Key External Dependencies
- **aiohttp** - Async HTTP client for API polling
- **aiogram** - Telegram Bot API wrapper
- **redis** (async) - Deduplication and cursor persistence
- **orjson** - Optimized JSON serialization
- **pytz** - Timezone handling
- **pydantic** - Settings and validation

### Core Data Flow
1. **API Polling** → Fetch surebets with cursor-based incremental polling and origin filtering (ADR-015)
2. **Validation Chain** (fail-fast): OddsValidator → ProfitValidator → TimeValidator → DuplicateValidator (Redis) → OppositeMarketValidator
3. **Message Formatting** → Cache static parts (teams, tournament, date), compute dynamic parts (stake emoji, min_odds)
4. **Telegram Delivery** → Priority heap queue with 5-bot rotation for throughput

## Critical Architecture Decisions (ADRs)

| Decision                             | Rationale                                                |
| ------------------------------------ | -------------------------------------------------------- |
| NO Bloom Filter (ADR-012)            | 1% false positives = lost picks = lost money for bettors |
| NO fire-and-forget Redis (ADR-013)   | Race conditions cause duplicates                         |
| Redis pipeline batch (ADR-004)       | Balance latency vs reliability for dedup                 |
| asyncio.gather, no workers (ADR-014) | Internal queues add latency; gather is sufficient        |
| Cursor incremental (ADR-009)         | Avoid reprocessing already-handled picks                 |
| Adaptive polling backoff (ADR-010)   | Auto-recovery from rate limits (0.5s base, 5.0s max)     |
| Priority heap for Telegram (ADR-006) | Higher-value picks sent first; graceful degradation      |
| Origin filtering (ADR-015)           | Filter at API level reduces data volume ~60-70%          |

## Domain-Specific Calculations

**Min Odds Formula** (Pinnacle-specific, **CORRECTED** in v2.0):
```python
min_odds = 1 / (1.01 - 1/odd_pinnacle)  # Exact cutoff at -1% profit
```
⚠️ **IMPORTANT**: The legacy V6 formula was incorrect (ADR-003). Always use this corrected formula.

**Stake Confidence by Profit**:
- `-1% to -0.5%` → 🔴 Low
- `-0.5% to 1.5%` → 🟠 Medium-low
- `1.5% to 4%` → 🟡 Medium-high
- `>4%` → 🟢 High

## Implementation Status

**Current State**: Phase 6 (Application Layer) at 100% - All components complete. Next: Phase 7 (Integration).

```
Fase 0:  Setup          [████] 100%
Fasa 1:  Domain Core    [████] 100%  (9/9)
Fase 2:  Calculators    [████] 100%  (5/5: 46 tests)
Fase 3:  Validators     [████] 100%  (6/6: 76 tests)
Fase 4:  Config         [████] 100%  (4/4: 108 tests)
Fase 5A: Redis          [████] 100%  (3/3: 26 tests)
Fase 5B: API Client     [████] 100%  (3/3: 36 tests)
Fase 5C: Messaging      [████] 100%  (5/5: 31 tests)
Fase 6:  Application    [████] 100%  (5/5: PickDTO, DuplicateValidator, OppositeMarketService, PickHandler, Tests)
Fase 7:  Integración    [____] 0%

Total: 49/56 tareas completadas (88%)
```

**Next tasks** (Fase 6):
- [x] 6.2 DuplicateValidator
- [x] 6.3 OppositeMarketService  
- [x] 6.4 PickHandler
- [x] 6.5 Tests Handler

**See** `docs/05-Implementation.md` for detailed task breakdown.

## Key Configuration Parameters

| Parameter               | Default | Description                |
| ----------------------- | ------- | -------------------------- |
| `MIN_ODDS`              | 1.10    | Minimum acceptable odds    |
| `MAX_ODDS`              | 9.99    | Maximum acceptable odds    |
| `MIN_PROFIT`            | -1.0    | Minimum profit threshold   |
| `MAX_PROFIT`            | 25.0    | Maximum profit threshold   |
| `POLLING_BASE_INTERVAL` | 0.5s    | Base API poll interval     |
| `POLLING_MAX_INTERVAL`  | 5.0s    | Max interval under backoff |

## Implementation Guidelines

When implementing code from placeholders:

1. **Read documentation first**: Each placeholder references relevant docs
2. **Follow dependencies**: Implement in order (domain → application → infrastructure)
3. **Test immediately**: Don't move to next component without tests
4. **Consult legacy**: `legacy/RetadorV6.py` for reference (but use corrected formulas)
5. **ADR-012 & ADR-013**: **Never** implement Bloom Filter or fire-and-forget Redis
6. **ADR-003**: Always use the **corrected** min_odds formula

## Critical Rules

❌ **DO NOT**:
- Implement Bloom Filter for Redis deduplication (ADR-012)
- Use fire-and-forget pattern for Redis writes (ADR-013)
- Use the legacy V6 min_odds formula (ADR-003)
- Add workers/queues for processing (ADR-014)
- Skip validation in favor of speed

✅ **DO**:
- Use Redis pipeline batch for deduplication
- Always await Redis operations
- Use corrected min_odds formula from ADR-003
- Use asyncio.gather for parallel processing
- Filter at API origin with optimized parameters

## Environment Variables

Configuration via `.env` file (see `.env.example`):

| Variable               | Default            | Description                    |
| ---------------------- | ------------------ | ------------------------------ |
| `API_URL`              | apostasseguras.com | Surebet API endpoint           |
| `API_TOKEN`            | -                  | API authentication token       |
| `REDIS_HOST`           | localhost          | Redis server host              |
| `REDIS_PORT`           | 6379               | Redis server port              |
| `TELEGRAM_BOT_TOKENS`  | -                  | Comma-separated bot tokens     |
| `TELEGRAM_LOG_CHANNEL` | 0                  | Channel ID for logging         |
| `CONCURRENT_PICKS`     | 250                | Max concurrent pick processing |
| `CACHE_TTL`            | 10                 | Local cache TTL in seconds     |

## Documentation

- `/docs/01-SRS.md` - Software Requirements Specification
- `/docs/02-PDR.md` - Preliminary Design Review (architecture diagrams)
- `/docs/03-ADRs.md` - Architecture Decision Records (16 critical decisions)
- `/docs/04-Structure.md` - Project structure guide for developers
- `/docs/05-Implementation.md` - Implementation tasks and phase breakdown
- `/legacy/RetadorV6.py` - Previous implementation (reference only, formulas may be incorrect)

## Quick Reference: Where to Implement What

| Feature                    | File(s) to Implement                                                     |
| -------------------------- | ------------------------------------------------------------------------ |
| Change stake profit ranges | `src/domain/services/calculators/pinnacle.py`                            |
| Add new bookmaker          | `src/config/bookmakers.py`                                               |
| Change message format      | `src/infrastructure/messaging/message_formatter.py`                      |
| Add new validation         | `src/domain/rules/validators/` (new file) + update `validation_chain.py` |
| Change API parameters      | `src/infrastructure/api/surebet_client.py`                               |
| Change polling behavior    | `src/infrastructure/api/rate_limiter.py`                                 |
| Add new sharp calculator   | `src/domain/services/calculators/` (new file) + update `factory.py`      |

## Common Development Patterns

### Creating a Value Object
```python
# All value objects must:
# - Be immutable (frozen dataclass)
# - Validate in __post_init__
# - Raise appropriate domain exception if invalid
# - Be in src/domain/value_objects/
```

### Creating a Validator
```python
# All validators must:
# - Inherit from BaseValidator
# - Implement validate() returning ValidationResult
# - Be chainable (set_next pattern)
# - Have tests covering edge cases
```

### Creating a Calculator Strategy
```python
# All calculators must:
# - Implement BaseCalculator interface
# - Be registered in CalculatorFactory
# - Have comprehensive tests with reference values
# - Document formulas with ADR references
```
