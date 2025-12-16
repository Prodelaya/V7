# Revisión de Diseño Preliminar (PDR)
## Sistema Retador v2.0

**Versión**: 2.1  
**Fecha**: Diciembre 2025  
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

| Clase        | Tipo interno | Validación             | Comportamiento extra    |
| ------------ | ------------ | ---------------------- | ----------------------- |
| `Odds`       | float        | 1.01-1000              | `implied_probability()` |
| `Profit`     | float        | -100 a 100             | `is_acceptable()`       |
| `MarketType` | Enum         | Valores predefinidos   | `get_opposite()`        |
| `EventTime`  | datetime     | Futuro, timezone-aware | `seconds_until()`       |

#### 3.1.2 Entidades

| Clase       | Atributos Principales             | Comportamiento      |
| ----------- | --------------------------------- | ------------------- |
| `Pick`      | teams, odds, market, time, bookie | Inmutable, validado |
| `Surebet`   | prong_sharp, prong_soft, profit   | Calcula roles       |
| `Bookmaker` | name, type (sharp/soft), config   | Configuración       |

#### 3.1.3 Servicios de Dominio

| Servicio                 | Responsabilidad            | Patrón                  |
| ------------------------ | -------------------------- | ----------------------- |
| `StakeCalculator`        | Calcular stake por profit  | Strategy                |
| `MinOddsCalculator`      | Calcular cuota mínima      | Strategy                |
| `OppositeMarketResolver` | Resolver mercados opuestos | Lookup                  |
| `ValidationChain`        | Pipeline de validación     | Chain of Responsibility |

### 3.2 Capa de Aplicación

#### 3.2.1 Handlers

| Handler       | Responsabilidad                              |
| ------------- | -------------------------------------------- |
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

```
┌─────────────────────────────────────────────────────────────┐
│                    STRATEGY PATTERN                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐                                    │
│  │CalculatorStrategy   │◀─────────────────┐                 │
│  │  (Interface)        │                  │                 │
│  ├─────────────────────┤                  │                 │
│  │+ calculate_stake()  │     ┌────────────┴────────────┐   │
│  │+ calculate_min_odds()│     │                         │   │
│  └─────────────────────┘     │                         │   │
│            ▲                  │                         │   │
│            │                  │                         │   │
│  ┌─────────┴─────────┐  ┌────┴────────┐  ┌────────────┐│   │
│  │PinnacleStrategy   │  │Bet365Strategy│  │FutureSharp ││   │
│  │                   │  │ (futuro)    │  │ (futuro)   ││   │
│  └───────────────────┘  └─────────────┘  └────────────┘│   │
│                                                         │   │
│  ┌──────────────────────────────────────────────────────┘   │
│  │                                                          │
│  │  CalculatorFactory.get_strategy("pinnaclesports")        │
│  │                     │                                    │
│  │                     ▼                                    │
│  │              PinnacleStrategy()                          │
│  │                                                          │
│  └──────────────────────────────────────────────────────────┘
```

### 4.2 Chain of Responsibility - Validación

```
┌─────────────────────────────────────────────────────────────┐
│              CHAIN OF RESPONSIBILITY                         │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  Pick ──▶ [Odds] ──▶ [Profit] ──▶ [Time] ──▶ [Dedup] ──▶ ✓ │
│              │          │           │          │            │
│              ▼          ▼           ▼          ▼            │
│           Rechazar   Rechazar   Rechazar   Rechazar         │
│           (razón)    (razón)    (razón)    (razón)          │
│                                                              │
└─────────────────────────────────────────────────────────────┘

Cada validador:
1. Evalúa su condición
2. Si falla: retorna error con razón
3. Si pasa: delega al siguiente
```

### 4.3 Repository Pattern - Abstracción de Datos### 4.3 Repository Pattern - Abstracción de Datos

```
┌─────────────────────────────────────────────────────────────┐
│                  REPOSITORY PATTERN                          │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────────────────┐                                    │
│  │  PickRepository     │  (Interfaz abstracta)              │
│  │  ──────────────     │                                    │
│  │  + save(pick)       │                                    │
│  │  + exists(key)      │                                    │
│  │  + get_by_key(key)  │                                    │
│  └──────────┬──────────┘                                    │
│             │                                                │
│             │ implementa                                     │
│             ▼                                                │
│  ┌─────────────────────┐     ┌─────────────────────┐        │
│  │RedisPickRepository  │     │PostgresRepository   │        │
│  │                     │     │    (futuro)         │        │
│  └─────────────────────┘     └─────────────────────┘        │
│                                                              │
│  Beneficio: Cambiar implementación sin tocar dominio        │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

---

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

## 6. Interfaces y Contratos

### 6.1 Interfaz PickRepository

```python
class PickRepository(ABC):
    @abstractmethod
    async def save(self, key: str, ttl: int) -> bool: ...
    
    @abstractmethod
    async def exists(self, key: str) -> bool: ...
    
    @abstractmethod
    async def exists_batch(self, keys: List[str]) -> Dict[str, bool]: ...
    
    @abstractmethod
    async def save_with_opposites(self, pick: Pick, ttl: int) -> bool: ...
    
    @abstractmethod
    async def save_cursor(self, cursor: str) -> bool: ...
    
    @abstractmethod
    async def load_cursor(self) -> Optional[str]: ...
```

### 6.2 Interfaz BaseCalculator

```python
class BaseCalculator(ABC):
    @property
    @abstractmethod
    def name(self) -> str: ...
    
    @abstractmethod
    def calculate_stake(self, profit: float) -> Optional[StakeResult]: ...
    
    @abstractmethod
    def calculate_min_odds(self, sharp_odds: float) -> MinOddsResult: ...
    
    @abstractmethod
    def is_valid_profit(self, profit: float) -> bool: ...
```

**Nota**: No incluye `margin` - será añadido en versión futura para yield real.

### 6.3 Interfaz Validator

```python
class Validator(ABC):
    @abstractmethod
    async def validate(self, pick: Pick) -> ValidationResult: ...
    
    def set_next(self, validator: 'Validator') -> 'Validator': ...
```

### 6.4 Interfaz TelegramGateway

```python
class TelegramGateway(ABC):
    @abstractmethod
    async def enqueue(self, message: str, channel_id: int, profit: float) -> bool: ...
    
    @abstractmethod
    async def start_sending(self) -> None: ...
    
    @abstractmethod
    async def stop(self) -> None: ...
```

---

## 7. Gestión de Errores

### 7.1 Jerarquía de Excepciones

```
RetadorError (base)
├── DomainError
│   ├── InvalidOddsError
│   ├── InvalidProfitError
│   └── InvalidMarketError
├── InfrastructureError
│   ├── ApiConnectionError
│   ├── ApiRateLimitError
│   ├── RedisConnectionError
│   └── TelegramSendError
└── ApplicationError
    ├── ValidationError
    └── ProcessingError
```

### 7.2 Estrategia de Manejo

| Tipo de Error       | Acción                    | Retry      | Alerta             |
| ------------------- | ------------------------- | ---------- | ------------------ |
| API timeout         | Log + retry con backoff   | Sí (3x)    | No                 |
| API 429             | Aumentar polling interval | Automático | Si persiste >10min |
| Redis connection    | Reconectar                | Sí         | Sí                 |
| Redis timeout       | Log + continuar           | No         | No                 |
| Telegram rate limit | Rotar bot                 | Automático | No                 |
| Telegram forbidden  | Log + skip canal          | No         | Sí                 |
| Validation error    | Log + descartar pick      | No         | No                 |
| Domain error        | Log + descartar pick      | No         | No                 |

---

## 8. Configuración y Despliegue

### 8.1 Variables de Entorno

```env
# API
SUREBET_API_URL=https://api.apostasseguras.com/request
SUREBET_API_TOKEN=xxx

# API Params
API_ORDER=created_at_desc
API_MIN_PROFIT=-1
API_LIMIT=5000

# Polling
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

# Validation
MIN_PROFIT=-1.0
MAX_PROFIT=25.0
MIN_ODDS=1.10
MAX_ODDS=9.99

# Cache
HTML_CACHE_TTL=60
LOCAL_CACHE_MAX_SIZE=2000
```

### 8.2 Docker Compose

```yaml
version: '3.8'

services:
  retador:
    build: .
    env_file: .env
    depends_on:
      - redis
    restart: unless-stopped
    
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  redis_data:
```

---

## 9. Plan de Migración

| Fase           | Duración | Con Buffer (x1.5) | Entregable                            |
| -------------- | -------- | ----------------- | ------------------------------------- |
| 0. Setup       | 2-3h     | 3-4h              | Proyecto configurado                  |
| 1. Domain Core | 4-6h     | 6-9h              | Value Objects + Entidades + Constants |
| 2. Calculators | 3-4h     | 4-6h              | Strategy pattern                      |
| 3. Validators  | 3-4h     | 4-6h              | Chain of Responsibility               |
| 4. Config      | 2-3h     | 3-4h              | Pydantic Settings                     |
| 5A. Redis      | 2-3h     | 3-4h              | Repository + Tests                    |
| 5B. API Client | 2-3h     | 3-4h              | Client + RateLimiter                  |
| 5C. Messaging  | 2-3h     | 3-4h              | Formatter (RF-010) + Gateway          |
| 6. Application | 3-4h     | 4-6h              | PickHandler                           |
| 7. Integración | 4-6h     | 6-9h              | Tests E2E + Cutover                   |

**Total estimado**: 27-38 horas → **40-56 horas** (con buffer realista)

---

## 10. Riesgos y Mitigaciones

| Riesgo               | Prob. | Impacto | Mitigación                      |
| -------------------- | ----- | ------- | ------------------------------- |
| API proveedor cambia | Media | Alto    | Abstracción, tests de contrato  |
| API proveedor cae    | Baja  | Alto    | Retry con backoff, alerta >5min |
| Latencia aumenta     | Baja  | Alto    | Profiling, métricas             |
| Redis falla          | Baja  | Medio   | Fallback cache local            |
| Telegram rate limit  | Alta  | Bajo    | Pool 5 bots, rotación           |
| Cursor se corrompe   | Baja  | Medio   | Validación, reset manual        |
| Fórmula min_odds mal | -     | Alto    | ✅ Corregida en v2.0             |
| Bloom Filter         | -     | Alto    | ✅ Rechazado                     |
| Fire-and-forget      | -     | Alto    | ✅ Rechazado                     |

---

## 11. Métricas Objetivo

| Métrica        | V6 (actual)  | V2.0 (objetivo) |
| -------------- | ------------ | --------------- |
| Latencia p50   | ~150ms       | ~60ms           |
| Latencia p95   | ~250ms       | ~100ms          |
| Throughput     | ~300 picks/s | ~500 picks/s    |
| Duplicados     | <0.01%       | <0.01%          |
| Picks perdidos | 0%           | 0%              |

**Nota**: No se acepta degradación en duplicados ni picks perdidos (rechazamos Bloom Filter y fire-and-forget por estas razones).

---

## 12. Plan de Rollback

### 12.1 Criterios de Rollback

El rollback a V6 se ejecutará **inmediatamente** si se detecta:

| Métrica              | Umbral Crítico         | Acción                                            |
| -------------------- | ---------------------- | ------------------------------------------------- |
| **Duplicados**       | >0.1%                  | 🔴 Rollback inmediato                              |
| **Picks perdidos**   | >0 en 1 hora           | 🔴 Rollback inmediato                              |
| **Latencia p95**     | >300ms sostenido 10min | 🟠 Investigar, rollback si no se resuelve en 1h    |
| **Errores Redis**    | >10/min sostenido 5min | 🟠 Investigar, rollback si no se resuelve en 30min |
| **Errores Telegram** | >50% mensajes fallidos | 🔴 Rollback inmediato                              |

### 12.2 Procedimiento de Rollback

```bash
# 1. Detener V2.0
docker-compose -f docker-compose.v2.yml down

# 2. Verificar que V6 sigue corriendo (debería estar en paralelo)
docker ps | grep retador-v6

# 3. Si V6 no está corriendo, iniciarlo
docker-compose -f docker-compose.v6.yml up -d

# 4. Verificar que V6 está enviando picks
docker logs retador-v6 --tail 50

# 5. Limpiar cursor de V2.0 en Redis (evitar conflictos futuros)
redis-cli DEL retador:v2:cursor
```

### 12.3 Estrategia de Ejecución Paralela

Durante la fase de validación (Fase 7), V6 y V2.0 correrán en paralelo:

```
┌─────────────────┐     ┌─────────────────┐
│   Retador V6    │     │  Retador V2.0   │
│   (producción)  │     │   (shadow)      │
└────────┬────────┘     └────────┬────────┘
         │                       │
         │  Envía picks          │  Solo registra, NO envía
         ▼                       ▼
   ┌──────────┐           ┌──────────┐
   │ Telegram │           │  Logs +  │
   │ Channels │           │ Métricas │
   └──────────┘           └──────────┘
```

**Modo Shadow de V2.0:**
- Procesa los mismos picks que V6
- Registra qué enviaría (sin enviar realmente)
- Compara con lo que V6 envió
- Alerta si hay discrepancias

### 12.4 Checklist Pre-Cutover

Antes de hacer cutover completo a V2.0, verificar:

- [ ] V2.0 en shadow mode por mínimo 24 horas
- [ ] 0 discrepancias con V6 en picks enviados
- [ ] Latencia p95 < 100ms consistente
- [ ] 0 errores críticos en logs
- [ ] Redis y Telegram estables
- [ ] Equipo disponible para monitoreo post-cutover (primera hora)

### 12.5 Checklist Post-Rollback

Si se ejecuta rollback, verificar:

- [ ] V6 enviando picks correctamente
- [ ] Logs de V6 sin errores
- [ ] Canal de Telegram recibiendo mensajes
- [ ] Crear issue en GitHub con detalles del problema
- [ ] Programar post-mortem en 24 horas
