# Revisión de Diseño Preliminar (PDR)
## Sistema Retador v2.0

**Versión**: 2.1  
**Fecha**: Diciembre 2024  
**Estado**: Aprobado  
**Última actualización**: Integración de optimizaciones V7

---

## 1. Resumen Ejecutivo

Este documento presenta el diseño preliminar del sistema Retador v2.0, una refactorización completa del sistema actual hacia una arquitectura profesional basada en principios de Clean Architecture y Domain-Driven Design, incorporando optimizaciones seleccionadas del análisis V7.

### 1.1 Decisión Arquitectónica Principal
**Monolito Modular** con Clean Architecture - Un único proceso con separación clara de capas (Domain, Application, Infrastructure), preparado para evolucionar a microservicios si el volumen lo requiere.

### 1.2 Optimizaciones Integradas de V7
- ✅ Cursor incremental para API
- ✅ Polling adaptativo con backoff exponencial
- ✅ Heap priorizado para envío Telegram
- ✅ Cache HTML de partes de mensaje
- ✅ Parámetros API optimizados
- ❌ Bloom Filter (rechazado - falsos positivos)
- ❌ Fire-and-forget Redis (rechazado - race conditions)

---

## 2. Arquitectura del Sistema

### 2.1 Diagrama de Contexto

```
┌─────────────────────────────────────────────────────────────────┐
│                         CONTEXTO EXTERNO                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   ┌──────────────┐         ┌──────────────┐                     │
│   │   API        │         │   Telegram   │                     │
│   │   Surebets   │         │   Bot API    │                     │
│   │  (Proveedor) │         │  (5 bots)    │                     │
│   └──────┬───────┘         └──────▲───────┘                     │
│          │                        │                              │
│          │ HTTPS/REST             │ HTTPS                        │
│          │ (cursor incremental)   │ (heap priorizado)            │
│          ▼                        │                              │
│   ┌──────────────────────────────────────────┐                  │
│   │                                          │                  │
│   │           RETADOR v2.0                   │                  │
│   │         (Monolito Modular)               │                  │
│   │                                          │                  │
│   └──────────────────┬───────────────────────┘                  │
│                      │                                          │
│                      │ TCP                                      │
│                      ▼                                          │
│               ┌──────────────┐                                  │
│               │    Redis     │                                  │
│               │  (Dedup +    │                                  │
│               │   Cursor)    │                                  │
│               └──────────────┘                                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 Arquitectura Interna (Clean Architecture)

```
┌─────────────────────────────────────────────────────────────────┐
│                 RETADOR v2.0 - CLEAN ARCHITECTURE               │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    INFRASTRUCTURE                          │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │ SurebetAPI  │ │   Redis     │ │ TelegramGateway     │  │  │
│  │  │ Client +    │ │ Repository  │ │ (Heap + Multi-bot)  │  │  │
│  │  │ RateLimiter │ │ (Pipeline)  │ │                     │  │  │
│  │  └──────┬──────┘ └──────┬──────┘ └──────────▲──────────┘  │  │
│  │         │               │                   │              │  │
│  │  ┌──────┴──────┐ ┌──────┴──────┐ ┌─────────┴───────────┐  │  │
│  │  │ Adaptive    │ │   Local     │ │ MessageFormatter    │  │  │
│  │  │ Polling     │ │   Cache     │ │ (HTML Cache)        │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                              │                                   │
│  ┌───────────────────────────▼───────────────────────────────┐  │
│  │                    APPLICATION                             │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                  PickHandler                         │  │  │
│  │  │  (Orquesta: fetch → validate → dedup → send)        │  │  │
│  │  │  Usa asyncio.gather para procesamiento paralelo     │  │  │
│  │  └─────────────────────────┬───────────────────────────┘  │  │
│  └─────────────────────────────┼─────────────────────────────┘  │
│                                │                                 │
│  ┌─────────────────────────────▼─────────────────────────────┐  │
│  │                      DOMAIN                                │  │
│  │  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐  │  │
│  │  │  Entities   │ │  Services   │ │    Validators       │  │  │
│  │  │  - Pick     │ │  - Stake    │ │  - OddsValidator    │  │  │
│  │  │  - Surebet  │ │  - MinOdds  │ │  - ProfitValidator  │  │  │
│  │  │  - Bookie   │ │  - Opposite │ │  - TimeValidator    │  │  │
│  │  └─────────────┘ └─────────────┘ └─────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │                 Value Objects                        │  │  │
│  │  │    Odds  │  Profit  │  MarketType  │  Timestamp     │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                      CONFIG                                │  │
│  │  Settings │ Bookmakers │ Logging │ APIParams │ Polling    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 2.3 Flujo de Datos Principal

```
┌─────────────────────────────────────────────────────────────────┐
│                     FLUJO DE PROCESAMIENTO                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │   API    │───▶│  Parse   │───▶│ Validate │───▶│  Dedup   │  │
│  │  Fetch   │    │  + DTO   │    │  Chain   │    │  Redis   │  │
│  │ (cursor) │    │          │    │(fail-fast│    │(pipeline)│  │
│  └──────────┘    └──────────┘    └──────────┘    └────┬─────┘  │
│       │                                               │         │
│       │ Guardar cursor                                │         │
│       ▼                                               │         │
│  ┌──────────┐                     ┌───────────────────┘         │
│  │  Redis   │                     │                              │
│  │ (cursor) │                     ▼                              │
│  └──────────┘    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│                  │ Calculate│───▶│  Format  │───▶│  Enqueue │  │
│                  │Stake/Min │    │ (cached) │    │  (heap)  │  │
│                  └──────────┘    └──────────┘    └────┬─────┘  │
│                                                       │         │
│                                                       ▼         │
│                                               ┌──────────────┐  │
│                                               │  Send Loop   │  │
│                                               │ (priorizado) │  │
│                                               │  (5 bots)    │  │
│                                               └──────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘

Tiempos objetivo por etapa:
- API Fetch: ~100-300ms (dependiente del proveedor)
- Parse + Validate: <10ms
- Redis Dedup (batch): <10ms
- Calculate: <1ms
- Format (con cache): <3ms
- Enqueue heap: <1ms
- Telegram Send: ~50-100ms
- TOTAL: <500ms (objetivo <100ms sin contar API externa)
```

---

## 3. Diseño de Componentes

### 3.1 Capa de Dominio

#### 3.1.1 Value Objects

| Clase | Tipo interno | Validación | Comportamiento extra |
|-------|--------------|------------|---------------------|
| `Odds` | float | 1.01-1000 | `implied_probability()` |
| `Profit` | float | -100 a 100 | `is_acceptable()` |
| `MarketType` | Enum | Valores predefinidos | `get_opposite()` |
| `EventTime` | datetime | Futuro, timezone-aware | `seconds_until()` |

#### 3.1.2 Entidades

| Clase | Atributos Principales | Comportamiento |
|-------|----------------------|----------------|
| `Pick` | teams, odds, market, time, bookie | Inmutable, validado |
| `Surebet` | prong_sharp, prong_soft, profit | Calcula roles |
| `Bookmaker` | name, type (sharp/soft), config | Configuración |

#### 3.1.3 Servicios de Dominio

| Servicio | Responsabilidad | Patrón |
|----------|-----------------|--------|
| `StakeCalculator` | Calcular stake por profit | Strategy |
| `MinOddsCalculator` | Calcular cuota mínima | Strategy |
| `OppositeMarketResolver` | Resolver mercados opuestos | Lookup |
| `ValidationChain` | Pipeline de validación | Chain of Responsibility |

### 3.2 Capa de Aplicación

#### 3.2.1 Handlers

| Handler | Responsabilidad |
|---------|-----------------|
| `PickHandler` | Orquesta flujo completo con `asyncio.gather` |

#### 3.2.2 Procesamiento Paralelo (sin workers)

```python
# Reemplaza el modelo de workers/colas de V6
async def process_batch(self, picks: List[dict]) -> List[ProcessedPick]:
    tasks = [self._process_single(pick) for pick in picks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, ProcessedPick)]
```

### 3.3 Capa de Infraestructura

#### 3.3.1 API Client con Cursor Incremental

```
┌─────────────────────────────────────────────────────────────┐
│                  SUREBET API CLIENT                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │                 SurebetApiClient                     │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ - last_cursor: Optional[str]                        │    │
│  │ - rate_limiter: AdaptiveRateLimiter                 │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ + fetch_picks() → List[dict]                        │    │
│  │ + _build_params() → dict                            │    │
│  │ + _update_cursor(picks)                             │    │
│  │ + _persist_cursor()                                 │    │
│  │ + _load_cursor()                                    │    │
│  └─────────────────────────────────────────────────────┘    │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              AdaptiveRateLimiter                     │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ - base_interval: 0.5                                │    │
│  │ - max_interval: 5.0                                 │    │
│  │ - consecutive_429: int                              │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ + wait_if_needed()                                  │    │
│  │ + report_success()                                  │    │
│  │ + report_rate_limit()                               │    │
│  │ + current_interval → float                          │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Parámetros API optimizados:                                │
│  - cursor: {sort_by}:{id}                                   │
│  - order: created_at_desc                                   │
│  - min-profit: -1                                           │
│  - limit: 5000                                              │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.2 Telegram Gateway con Heap Priorizado

```
┌─────────────────────────────────────────────────────────────┐
│                 TELEGRAM GATEWAY                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              TelegramGateway                         │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ - bots: List[Bot]  (5 bots)                         │    │
│  │ - heap: List[Tuple]  (max 1000)                     │    │
│  │ - current_bot_index: int                            │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ + enqueue(message, channel, profit) → bool          │    │
│  │ + start_sending()                                   │    │
│  │ + _send_loop()                                      │    │
│  │ + _send_message(channel, message)                   │    │
│  │ + _rotate_bot()                                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Heap structure: (-profit, timestamp, channel_id, message)  │
│                                                              │
│  Comportamiento cola llena:                                 │
│  - Si nuevo profit > min en cola → reemplazar              │
│  - Si nuevo profit <= min en cola → rechazar               │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.3 Message Formatter con Cache HTML

```
┌─────────────────────────────────────────────────────────────┐
│                 MESSAGE FORMATTER                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              MessageFormatter                        │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ - html_cache: Dict[str, Tuple[float, dict]]         │    │
│  │ - cache_ttl: 60 seconds                             │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ + format_message(apuesta, contra, profit) → str     │    │
│  │ + _get_event_key(apuesta) → str                     │    │
│  │ + _get_cached_parts(apuesta) → Optional[dict]       │    │
│  │ + _cache_parts(apuesta, parts)                      │    │
│  │ + _format_teams(apuesta) → str                      │    │
│  │ + _format_tournament(apuesta) → str                 │    │
│  │ + _format_date(apuesta) → str                       │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  Cache key: {team1}:{team2}:{timestamp}:{bookie}            │
│  Cached parts: teams, tournament, date (no cambian)         │
│  No cached: stake emoji, odds, min_odds (cambian)           │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

#### 3.3.4 Redis Repository (sin Bloom Filter)

```
┌─────────────────────────────────────────────────────────────┐
│                 REDIS REPOSITORY                             │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              RedisPickRepository                     │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ - redis: Redis                                      │    │
│  │ - local_cache: Dict (first-level cache)             │    │
│  ├─────────────────────────────────────────────────────┤    │
│  │ + exists(key) → bool                                │    │
│  │ + exists_batch(keys) → Dict[str, bool]              │    │
│  │ + save(key, ttl) → bool                             │    │
│  │ + save_with_opposites(pick, ttl) → bool             │    │
│  │ + save_cursor(cursor) → bool                        │    │
│  │ + load_cursor() → Optional[str]                     │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                              │
│  ⚠️ SIN Bloom Filter (rechazado por falsos positivos)       │
│  ⚠️ SIN fire-and-forget (rechazado por race conditions)     │
│                                                              │
│  Flujo de verificación:                                     │
│  1. Check local_cache (O(1), ~0ms)                          │
│  2. Check Redis con pipeline batch (~10ms para 50 keys)     │
│  3. Await confirmación antes de continuar                   │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Patrones de Diseño Aplicados

### 4.1 Strategy Pattern - Calculadores
(Sin cambios respecto a versión anterior)

### 4.2 Chain of Responsibility - Validación
(Sin cambios respecto a versión anterior)

### 4.3 Repository Pattern - Abstracción de Datos
(Sin cambios respecto a versión anterior)

### 4.4 NUEVO: Adaptive Rate Limiter

```
┌─────────────────────────────────────────────────────────────┐
│              ADAPTIVE RATE LIMITER                           │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Estado: consecutive_429 = 0                                │
│  Intervalo: 0.5s (base)                                     │
│                                                              │
│  ┌─────────┐    ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│  │ Request │───▶│ Success │───▶│ Decrement│───▶│ 0.5s    │  │
│  └─────────┘    └─────────┘    │ counter  │    │ (base)  │  │
│       │                        └─────────┘    └─────────┘  │
│       │                                                      │
│       │         ┌─────────┐    ┌─────────┐    ┌─────────┐  │
│       └────────▶│  429    │───▶│Increment│───▶│ Backoff │  │
│                 │ Error   │    │ counter │    │ 2^n * 0.5│  │
│                 └─────────┘    └─────────┘    └─────────┘  │
│                                                              │
│  Fórmula: interval = min(5.0, 0.5 * 2^consecutive_429)      │
│                                                              │
│  Ejemplo:                                                   │
│  - 0 errores: 0.5s                                          │
│  - 1 error:   1.0s                                          │
│  - 2 errores: 2.0s                                          │
│  - 3 errores: 4.0s                                          │
│  - 4+ errores: 5.0s (máximo)                                │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 4.5 NUEVO: Priority Queue (Heap) para Telegram

```
┌─────────────────────────────────────────────────────────────┐
│              PRIORITY HEAP SENDER                            │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Heap: [(-4.5, t1, ch, msg), (-2.1, t2, ch, msg), ...]      │
│         ▲ Mayor profit primero (negativo para max-heap)     │
│                                                              │
│  ┌──────────────┐                                           │
│  │   Enqueue    │                                           │
│  │  profit=4.5  │                                           │
│  └──────┬───────┘                                           │
│         │                                                    │
│         ▼                                                    │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │ len < 1000?  │─No─▶│ profit > min?│─No─▶ Rechazar        │
│  └──────┬───────┘    └──────┬───────┘                       │
│         │ Sí                │ Sí                             │
│         ▼                   ▼                                │
│  ┌──────────────┐    ┌──────────────┐                       │
│  │  heappush    │    │  heappop +   │                       │
│  │              │    │  heappush    │                       │
│  └──────────────┘    └──────────────┘                       │
│                                                              │
│  Send Loop:                                                 │
│  1. heappop() → mensaje de mayor profit                     │
│  2. rate_limit.wait()                                       │
│  3. send_message() con rotación de bots                     │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Estructura de Proyecto (Actualizada)

```
retador/
├── src/
│   ├── domain/                      # Lógica de negocio pura
│   │   ├── entities/
│   │   │   ├── __init__.py
│   │   │   ├── pick.py
│   │   │   ├── surebet.py
│   │   │   └── bookmaker.py
│   │   ├── value_objects/
│   │   │   ├── __init__.py
│   │   │   ├── odds.py
│   │   │   ├── profit.py
│   │   │   └── market_type.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   ├── calculation_service.py
│   │   │   ├── opposite_market_service.py
│   │   │   └── calculators/
│   │   │       ├── __init__.py
│   │   │       ├── base.py
│   │   │       ├── factory.py
│   │   │       └── pinnacle.py
│   │   └── rules/
│   │       ├── __init__.py
│   │       ├── validation_chain.py
│   │       └── validators/
│   │           ├── __init__.py
│   │           ├── base.py
│   │           ├── odds_validator.py
│   │           ├── profit_validator.py
│   │           ├── time_validator.py
│   │           └── duplicate_validator.py
│   │
│   ├── application/
│   │   ├── __init__.py
│   │   ├── handlers/
│   │   │   ├── __init__.py
│   │   │   └── pick_handler.py      # Usa asyncio.gather
│   │   └── dto/
│   │       ├── __init__.py
│   │       └── pick_dto.py
│   │
│   ├── infrastructure/
│   │   ├── __init__.py
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── surebet_client.py    # + Cursor incremental
│   │   │   └── rate_limiter.py      # + Polling adaptativo
│   │   ├── repositories/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── redis_repository.py  # SIN Bloom Filter
│   │   │   └── _postgres_repository.py
│   │   ├── messaging/
│   │   │   ├── __init__.py
│   │   │   ├── telegram_gateway.py  # + Heap priorizado
│   │   │   └── message_formatter.py # + Cache HTML
│   │   └── cache/
│   │       ├── __init__.py
│   │       └── local_cache.py
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py              # + Parámetros API/Polling
│   │   ├── bookmakers.py
│   │   └── logging_config.py
│   │
│   └── shared/
│       ├── __init__.py
│       ├── exceptions.py
│       └── constants.py
│
├── tests/
│   ├── unit/
│   │   └── domain/
│   │       ├── test_calculators.py
│   │       ├── test_validators.py
│   │       └── test_rate_limiter.py  # NUEVO
│   └── integration/
│       ├── test_redis_repository.py
│       └── test_api_client.py        # NUEVO
│
├── scripts/
│   └── run.py
│
├── pyproject.toml
├── .env.example
└── README.md
```

---

## 6. Configuración Actualizada

### 6.1 Variables de Entorno

```env
# API
SUREBET_API_URL=https://api.apostasseguras.com/request
SUREBET_API_TOKEN=xxx

# API Params (optimizados)
API_ORDER=created_at_desc
API_MIN_PROFIT=-1
API_LIMIT=5000

# Polling (adaptativo)
POLLING_BASE_INTERVAL=0.5
POLLING_MAX_INTERVAL=5.0

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=xxx
REDIS_DB=0

# Telegram
TELEGRAM_TOKENS=token1,token2,token3,token4,token5
TELEGRAM_MAX_QUEUE_SIZE=1000
LOG_CHANNEL_ID=-123456789

# App
MIN_PROFIT=-1.0
MAX_PROFIT=25.0
MIN_ODDS=1.10
MAX_ODDS=9.99

# Cache
HTML_CACHE_TTL=60
```

---

## 7. Plan de Migración (Actualizado)

### Fase 1: Fundamentos (Semana 1-2)
- [ ] Estructura de proyecto
- [ ] Value Objects
- [ ] Entidades básicas
- [ ] Tests unitarios de dominio

### Fase 2: Infraestructura Core (Semana 3)
- [ ] Redis Repository (con pipeline, SIN Bloom)
- [ ] API Client con cursor incremental
- [ ] Rate Limiter adaptativo
- [ ] Tests de integración

### Fase 3: Mensajería (Semana 4)
- [ ] Message Formatter con cache HTML
- [ ] Telegram Gateway con heap priorizado
- [ ] Tests de mensajería

### Fase 4: Integración (Semana 5)
- [ ] Validation Chain
- [ ] Pick Handler con asyncio.gather
- [ ] Tests end-to-end

### Fase 5: Migración (Semana 6)
- [ ] Ejecutar en paralelo con V6
- [ ] Comparar resultados
- [ ] Cutover a v2.0

---

## 8. Métricas Objetivo

| Métrica | V6 (actual) | V2.0 (objetivo) | Mejora |
|---------|-------------|-----------------|--------|
| Latencia p50 | ~150ms | ~60ms | 60% |
| Latencia p95 | ~250ms | ~100ms | 60% |
| Throughput | ~300 picks/s | ~500 picks/s | 67% |
| Duplicados | <0.01% | <0.01% | = |
| Picks perdidos | 0% | 0% | = |

**Nota**: No se acepta degradación en duplicados ni picks perdidos (rechazamos Bloom Filter y fire-and-forget por estas razones).