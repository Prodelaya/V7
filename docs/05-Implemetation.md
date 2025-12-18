# 🚀 Guía de Implementación - Retador v2.0

## 📋 Principios de Implementación

1. **De dentro hacia afuera**: Empezar por `domain/` (sin dependencias externas), luego `application/`, finalmente `infrastructure/`
2. **Cada tarea debe ser testeable**: No avanzar sin verificar que funciona
3. **Commits pequeños**: Una tarea = un commit
4. **Sin conexiones externas al inicio**: Primero lógica pura, luego conexiones

---

## 🗓️ Visión General de Fases

| Fase               | Duración | Duración c/Buffer (x1.5) | Entregable                                    |
| ------------------ | -------- | ------------------------ | --------------------------------------------- |
| **0. Setup**       | 2-3h     | 3-4h                     | Proyecto configurado, dependencias instaladas |
| **1. Domain Core** | 4-6h     | 6-9h                     | Value Objects + Entidades + Constants + Tests |
| **2. Calculators** | 3-4h     | 4-6h                     | Strategy pattern completo + Tests             |
| **3. Validators**  | 3-4h     | 4-6h                     | Chain of Responsibility + Tests               |
| **4. Config**      | 2-3h     | 3-4h                     | Settings + Bookmakers configurados            |
| **5A. Redis**      | 2-3h     | 3-4h                     | Repository + Tests                            |
| **5B. API Client** | 2-3h     | 3-4h                     | Client + RateLimiter + Tests                  |
| **5C. Messaging**  | 2-3h     | 3-4h                     | Formatter + Gateway + Tests                   |
| **6. Application** | 3-4h     | 4-6h                     | Handler que orquesta todo                     |
| **7. Integración** | 4-6h     | 6-9h                     | Main + Tests E2E + Comparación con V6         |

**Total estimado**: 27-38 horas → **40-56 horas** (con buffer realista)

---

## 📦 FASE 0: Setup del Proyecto

### Objetivo
Tener el proyecto listo para desarrollar: dependencias, estructura, herramientas.

### Backlog

| ID  | Tarea                                        | Archivo(s)               | Criterio de Aceptación                   |
| --- | -------------------------------------------- | ------------------------ | ---------------------------------------- |
| 0.1 | Configurar `pyproject.toml` con dependencias | `pyproject.toml`         | `pip install -e .` funciona              |
| 0.2 | Crear `requirements.txt`                     | `requirements.txt`       | Todas las deps listadas                  |
| 0.3 | Configurar `.env.example`                    | `.env.example`           | Todas las variables documentadas         |
| 0.4 | Verificar estructura de carpetas             | `src/`, `tests/`         | Todos los `__init__.py` creados          |
| 0.5 | Configurar pytest                            | `pyproject.toml`         | `pytest` ejecuta sin errores             |
| 0.6 | Crear Dockerfile multi-stage                 | `Dockerfile`             | `docker build .` funciona sin errores    |
| 0.7 | Crear docker-compose.yml                     | `docker-compose.yml`     | `docker-compose up -d` levanta app+redis |
| 0.8 | Crear docker-compose.dev.yml                 | `docker-compose.dev.yml` | Hot-reload funciona en desarrollo        |
| 0.9 | Crear .dockerignore                          | `.dockerignore`          | Build context optimizado (<100MB)        |

### Dependencias a instalar

```txt
# requirements.txt
aiohttp>=3.9.0
aiogram>=3.0.0
redis>=5.0.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
python-dotenv>=1.0.0
orjson>=3.9.0
pytz>=2024.1

# Dev
pytest>=8.0.0
pytest-asyncio>=0.23.0
pytest-cov>=4.0.0
```

### Docker Stack

| Servicio | Imagen         | Recursos (bmax90)    | Puerto |
| -------- | -------------- | -------------------- | ------ |
| retador  | Build local    | 2GB RAM límite       | -      |
| redis    | redis:7-alpine | 1GB RAM límite (LRU) | 6379*  |

> **Nota**: Puerto 6379 solo expuesto en `docker-compose.dev.yml` para debugging local.

### Checklist
- [x] 0.1 pyproject.toml configurado
- [x] 0.2 requirements.txt creado
- [x] 0.3 .env.example con todas las variables
- [x] 0.4 Estructura verificada
- [x] 0.5 pytest funciona
- [x] 0.6 Dockerfile creado
- [x] 0.7 docker-compose.yml creado
- [x] 0.8 docker-compose.dev.yml creado
- [x] 0.9 .dockerignore creado

---

## 🧠 FASE 1: Domain Core (Value Objects + Entidades)

### Objetivo
Implementar los tipos de datos fundamentales con validación automática.

### Backlog

| ID   | Tarea                                | Archivo                                   | Dependencia  | Criterio de Aceptación                           |
| ---- | ------------------------------------ | ----------------------------------------- | ------------ | ------------------------------------------------ |
| 1.1  | Implementar excepciones de dominio   | `shared/exceptions.py`                    | -            | Clases de error definidas                        |
| 1.2  | Implementar `Odds` value object      | `domain/value_objects/odds.py`            | 1.1          | `Odds(2.05)` ✅, `Odds(0.5)` ❌ lanza error        |
| 1.3  | Implementar `Profit` value object    | `domain/value_objects/profit.py`          | 1.1          | `Profit(2.5)` ✅, `Profit(150)` ❌                 |
| 1.4  | Implementar `MarketType` enum        | `domain/value_objects/market_type.py`     | -            | Enum con over, under, win1, etc.                 |
| 1.4b | Definir `OPPOSITE_MARKETS` constante | `shared/constants.py`                     | 1.4          | Mapa completo de mercados opuestos (ver SRS 6.1) |
| 1.5  | Tests de Value Objects               | `tests/unit/domain/test_value_objects.py` | 1.2-1.4b     | 100% cobertura de VOs                            |
| 1.6  | Implementar entidad `Bookmaker`      | `domain/entities/bookmaker.py`            | -            | Enum Sharp/Soft + config                         |
| 1.7  | Implementar entidad `Pick`           | `domain/entities/pick.py`                 | 1.2-1.4, 1.6 | Dataclass inmutable validada                     |
| 1.8  | Implementar entidad `Surebet`        | `domain/entities/surebet.py`              | 1.7          | Dos prongs + profit                              |
| 1.9  | Tests de Entidades                   | `tests/unit/domain/test_entities.py`      | 1.6-1.8      | 100% cobertura                                   |

### Detalle de Tareas Clave

#### 1.2 - `Odds` Value Object

```python
# Criterios de aceptación:
# - Odds(2.05).value == 2.05 ✅
# - Odds(1.01).value == 1.01 ✅ (mínimo válido)
# - Odds(1000).value == 1000 ✅ (máximo válido)
# - Odds(0.99) → lanza InvalidOddsError
# - Odds(1001) → lanza InvalidOddsError
# - Odds(-1) → lanza InvalidOddsError
# - odds.implied_probability() retorna 1/valor
# - Es inmutable (frozen dataclass)
```

#### 1.7 - Entidad `Pick`

```python
# Criterios de aceptación:
# - Contiene: teams, odds, market_type, event_time, bookmaker, tournament
# - Se crea desde dict de API: Pick.from_api_response(data)
# - Genera clave Redis: pick.redis_key
# - Es inmutable
```

### Checklist Fase 1
- [x] 1.1 Excepciones
- [ ] 1.2 Odds VO
- [ ] 1.3 Profit VO
- [ ] 1.4 MarketType enum
- [ ] 1.5 Tests VOs
- [ ] 1.6 Bookmaker entity
- [ ] 1.7 Pick entity
- [ ] 1.8 Surebet entity
- [ ] 1.9 Tests entidades

---

## 🧮 FASE 2: Calculators (Strategy Pattern)

### Objetivo
Implementar el cálculo de stake y cuota mínima de forma extensible.

### Backlog

| ID  | Tarea                                 | Archivo                                   | Dependencia | Criterio de Aceptación      |
| --- | ------------------------------------- | ----------------------------------------- | ----------- | --------------------------- |
| 2.1 | Implementar `BaseCalculator` interfaz | `domain/services/calculators/base.py`     | -           | ABC con métodos abstractos  |
| 2.2 | Implementar `PinnacleCalculator`      | `domain/services/calculators/pinnacle.py` | 2.1         | Fórmulas correctas          |
| 2.3 | Implementar `CalculatorFactory`       | `domain/services/calculators/factory.py`  | 2.2         | Factory funcional           |
| 2.4 | Implementar `CalculationService`      | `domain/services/calculation_service.py`  | 2.3         | Orquesta calculators        |
| 2.5 | Tests de Calculators                  | `tests/unit/domain/test_calculators.py`   | 2.1-2.4     | Tabla de valores verificada |

### Detalle de Tareas Clave

#### 2.2 - Tests de `PinnacleCalculator`

```python
# Tests obligatorios para calculate_min_odds:
# | Sharp Odds | Min Odds Esperado |
# |------------|-------------------|
# | 1.50       | 2.92              |
# | 1.80       | 2.20              |
# | 2.00       | 1.96              |
# | 2.05       | 1.92              |
# | 2.50       | 1.64              |
# | 3.00       | 1.48              |

# Tests obligatorios para calculate_stake:
# | Profit | Emoji Esperado |
# |--------|----------------|
# | -1.5   | None (rechaza) |
# | -0.8   | 🔴             |
# | 0.5    | 🟠             |
# | 2.5    | 🟡             |
# | 5.0    | 🟢             |
# | 30.0   | None (rechaza) |
```

### Checklist Fase 2
- [ ] 2.1 BaseCalculator
- [ ] 2.2 PinnacleCalculator
- [ ] 2.3 CalculatorFactory
- [ ] 2.4 CalculationService
- [ ] 2.5 Tests completos

---

## ✅ FASE 3: Validators (Chain of Responsibility)

### Objetivo
Implementar validación modular y ordenada.

### Backlog

| ID  | Tarea                                | Archivo                                       | Dependencia | Criterio de Aceptación |
| --- | ------------------------------------ | --------------------------------------------- | ----------- | ---------------------- |
| 3.1 | Implementar `BaseValidator` interfaz | `domain/rules/validators/base.py`             | -           | ABC con validate()     |
| 3.2 | Implementar `OddsValidator`          | `domain/rules/validators/odds_validator.py`   | 3.1         | Valida rango 1.10-9.99 |
| 3.3 | Implementar `ProfitValidator`        | `domain/rules/validators/profit_validator.py` | 3.1         | Valida rango -1% a 25% |
| 3.4 | Implementar `TimeValidator`          | `domain/rules/validators/time_validator.py`   | 3.1         | Evento en futuro       |
| 3.5 | Implementar `ValidationChain`        | `domain/rules/validation_chain.py`            | 3.2-3.4     | Encadena validadores   |
| 3.6 | Tests de Validators                  | `tests/unit/domain/test_validators.py`        | 3.1-3.5     | Casos edge cubiertos   |

### Detalle de Tareas Clave

#### 3.5 - `ValidationChain`

```python
# Criterios de aceptación:
# - chain.validate(pick) retorna ValidationResult
# - ValidationResult tiene: is_valid, error_message, failed_validator
# - Ejecuta validadores en orden (fail-fast)
# - Si uno falla, no ejecuta los siguientes
# - Puede añadir/quitar validadores dinámicamente
```

### Checklist Fase 3
- [ ] 3.1 BaseValidator
- [ ] 3.2 OddsValidator
- [ ] 3.3 ProfitValidator
- [ ] 3.4 TimeValidator
- [ ] 3.5 ValidationChain
- [ ] 3.6 Tests

---

## ⚙️ FASE 4: Configuración

### Objetivo
Centralizar toda la configuración con Pydantic Settings.

### Backlog

| ID  | Tarea                               | Archivo                    | Dependencia | Criterio de Aceptación     |
| --- | ----------------------------------- | -------------------------- | ----------- | -------------------------- |
| 4.1 | Implementar `Settings` con Pydantic | `config/settings.py`       | -           | Lee de .env                |
| 4.2 | Implementar `BookmakerConfig`       | `config/bookmakers.py`     | -           | Lista de bookies + canales |
| 4.3 | Implementar `LoggingConfig`         | `config/logging_config.py` | -           | Logger + TelegramHandler   |
| 4.4 | Crear `.env.example` completo       | `.env.example`             | 4.1-4.2     | Todas las variables        |

### Detalle de Tareas Clave

#### 4.1 - `Settings`

```python
# Variables que debe leer:
# API
SUREBET_API_URL: str
SUREBET_API_TOKEN: str
API_LIMIT: int = 5000
API_MIN_PROFIT: float = -1.0

# Polling
POLLING_BASE_INTERVAL: float = 0.5
POLLING_MAX_INTERVAL: float = 5.0

# Redis
REDIS_HOST: str
REDIS_PORT: int
REDIS_PASSWORD: str
REDIS_DB: int = 0

# Telegram
TELEGRAM_TOKENS: List[str]  # comma-separated en .env
TELEGRAM_MAX_QUEUE_SIZE: int = 1000

# Validation
MIN_ODDS: float = 1.10
MAX_ODDS: float = 9.99
MIN_PROFIT: float = -1.0
MAX_PROFIT: float = 25.0
```

### Checklist Fase 4
- [ ] 4.1 Settings
- [ ] 4.2 BookmakerConfig
- [ ] 4.3 LoggingConfig
- [ ] 4.4 .env.example

---

## 🔌 FASE 5A: Infrastructure - Redis

### Objetivo
Implementar la capa de persistencia con Redis.

### Backlog

| ID   | Tarea                                 | Archivo                                           | Dependencia | Criterio de Aceptación   |
| ---- | ------------------------------------- | ------------------------------------------------- | ----------- | ------------------------ |
| 5A.1 | Implementar `BaseRepository` interfaz | `infrastructure/repositories/base.py`             | -           | ABC definida             |
| 5A.2 | Implementar `RedisRepository`         | `infrastructure/repositories/redis_repository.py` | 5A.1        | CRUD + pipeline batch    |
| 5A.3 | Tests de RedisRepository              | `tests/integration/test_redis_repository.py`      | 5A.2        | Con Redis/Testcontainers |

### Detalle: `RedisRepository`

```python
# Métodos requeridos:
# - exists(key: str) -> bool
# - exists_batch(keys: List[str]) -> Dict[str, bool]  # Pipeline
# - save(key: str, ttl: int) -> bool
# - save_with_opposites(pick: Pick, ttl: int) -> bool
# - save_cursor(cursor: str) -> bool
# - load_cursor() -> Optional[str]

# ⚠️ SIN Bloom Filter
# ⚠️ SIN fire-and-forget (siempre await)
```

### Checklist Fase 5A
- [ ] 5A.1 BaseRepository
- [ ] 5A.2 RedisRepository
- [ ] 5A.3 Tests Redis

---

## 🔌 FASE 5B: Infrastructure - API Client

### Objetivo
Implementar el cliente de API con cursor incremental y rate limiting adaptativo.

### Backlog

| ID   | Tarea                             | Archivo                                | Dependencia | Criterio de Aceptación |
| ---- | --------------------------------- | -------------------------------------- | ----------- | ---------------------- |
| 5B.1 | Implementar `AdaptiveRateLimiter` | `infrastructure/api/rate_limiter.py`   | -           | Backoff exponencial    |
| 5B.2 | Implementar `SurebetClient`       | `infrastructure/api/surebet_client.py` | 5B.1, 4.1   | Cursor incremental     |
| 5B.3 | Tests de API Client               | `tests/integration/test_api_client.py` | 5B.2        | Mock de respuestas     |

### Detalle: `SurebetClient`

```python
# Funcionalidades:
# - fetch_picks() → List[dict]
# - Cursor incremental (guarda último sort_by:id)
# - Parámetros: order=created_at_desc, min-profit=-1
# - Usa AdaptiveRateLimiter
# - Persiste cursor en Redis (sobrevive reinicios)
```

### Checklist Fase 5B
- [ ] 5B.1 AdaptiveRateLimiter
- [ ] 5B.2 SurebetClient
- [ ] 5B.3 Tests API

---

## 🔌 FASE 5C: Infrastructure - Messaging

### Objetivo
Implementar el sistema de mensajería con Telegram.

### Backlog

| ID   | Tarea                                   | Archivo                                         | Dependencia | Criterio de Aceptación               |
| ---- | --------------------------------------- | ----------------------------------------------- | ----------- | ------------------------------------ |
| 5C.1 | Implementar `MessageFormatter`          | `infrastructure/messaging/message_formatter.py` | -           | Cache HTML                           |
| 5C.2 | Implementar `_adjust_domain()` (RF-010) | `infrastructure/messaging/message_formatter.py` | 5C.1        | bet365→.es, betway, bwin, pokerstars |
| 5C.3 | Implementar `TelegramGateway`           | `infrastructure/messaging/telegram_gateway.py`  | 5C.1        | Heap + multi-bot                     |
| 5C.4 | Tests de Messaging                      | `tests/integration/test_messaging.py`           | 5C.1-5C.3   | Sin envío real                       |
| 5C.5 | Implementar `LocalCache`                | `infrastructure/cache/local_cache.py`           | -           | TTL + max size                       |

### Detalle: `_adjust_domain()` (RF-010)

```python
# Transformaciones de URL para mercado español:
# | Casa       | Original           | Transformado           |
# |------------|--------------------|-----------------------|
# | Bet365     | bet365.com         | bet365.es (ruta UPPER)|
# | Betway     | betway.com/en      | betway.es/es          |
# | Bwin       | bwin.com/en        | bwin.es/es            |
# | PokerStars | pokerstars.uk      | pokerstars.es         |
# | Versus     | sportswidget...    | www.versus.es/apuestas|
```

### Detalle: `TelegramGateway`

```python
# Funcionalidades:
# - enqueue(message, channel_id, profit) -> bool
# - Heap ordenado por profit (mayor primero)
# - Si cola llena (1000): rechaza si profit < mínimo en cola
# - Rotación de 5 bots
# - Rate limit: 30 msg/s por bot
# - start_sending() → loop de envío
```

### Checklist Fase 5C
- [ ] 5C.1 MessageFormatter
- [ ] 5C.2 _adjust_domain (RF-010)
- [ ] 5C.3 TelegramGateway
- [ ] 5C.4 Tests Messaging
- [ ] 5C.5 LocalCache

---

## 🎯 FASE 6: Application Layer

### Objetivo
Orquestar todo el flujo con el Handler.

### Backlog

| ID  | Tarea                               | Archivo                                          | Dependencia   | Criterio de Aceptación  |
| --- | ----------------------------------- | ------------------------------------------------ | ------------- | ----------------------- |
| 6.1 | Implementar `PickDTO`               | `application/dto/pick_dto.py`                    | Fase 1        | Conversión API → Domain |
| 6.2 | Implementar `DuplicateValidator`    | `domain/rules/validators/duplicate_validator.py` | 5.2           | Consulta Redis          |
| 6.3 | Implementar `OppositeMarketService` | `domain/services/opposite_market_service.py`     | -             | Dict de opuestos        |
| 6.4 | Implementar `PickHandler`           | `application/handlers/pick_handler.py`           | Todo anterior | Flujo completo          |
| 6.5 | Tests de Handler                    | `tests/unit/application/test_handler.py`         | 6.4           | Con mocks               |

### Detalle de Tareas Clave

#### 6.4 - `PickHandler`

```python
# Flujo que debe implementar:
async def process_batch(self, raw_picks: List[dict]) -> int:
    """
    1. Convertir raw_picks a DTOs/Entidades
    2. Para cada pick (con asyncio.gather):
       a. Validar con ValidationChain
       b. Si válido: check duplicado en Redis
       c. Si no duplicado: calcular stake + min_odds
       d. Formatear mensaje
       e. Encolar en TelegramGateway
       f. Guardar en Redis (con await, no fire-and-forget)
    3. Retornar cantidad de picks enviados
    """
```

### Checklist Fase 6
- [ ] 6.1 PickDTO
- [ ] 6.2 DuplicateValidator
- [ ] 6.3 OppositeMarketService
- [ ] 6.4 PickHandler
- [ ] 6.5 Tests Handler

---

## 🏁 FASE 7: Integración Final

### Objetivo
Ensamblar todo y verificar que funciona como V6 (pero mejor).

### Backlog

| ID  | Tarea                       | Archivo                         | Dependencia | Criterio de Aceptación  |
| --- | --------------------------- | ------------------------------- | ----------- | ----------------------- |
| 7.1 | Implementar `main.py`       | `scripts/run.py`                | Todo        | Arranca el sistema      |
| 7.2 | Test E2E con datos reales   | `tests/integration/test_e2e.py` | 7.1         | Flujo completo funciona |
| 7.3 | Ejecutar en paralelo con V6 | -                               | 7.2         | Mismos picks enviados   |
| 7.4 | Medir latencia              | -                               | 7.3         | p95 < 100ms             |
| 7.5 | Verificar duplicados        | -                               | 7.3         | < 0.01%                 |
| 7.6 | Documentar diferencias      | `README.md`                     | 7.3-7.5     | Changelog completo      |

### Detalle de Tareas Clave

#### 7.1 - `main.py`

```python
# Estructura esperada:
async def main():
    # 1. Cargar configuración
    settings = Settings()
    
    # 2. Inicializar componentes
    redis_repo = RedisRepository(settings)
    api_client = SurebetClient(settings, redis_repo)
    telegram = TelegramGateway(settings)
    handler = PickHandler(redis_repo, telegram, ...)
    
    # 3. Iniciar servicios
    await telegram.start_sending()
    
    # 4. Loop principal
    while True:
        picks = await api_client.fetch_picks()
        if picks:
            sent = await handler.process_batch(picks)
            logger.info(f"Enviados: {sent}/{len(picks)}")
        await asyncio.sleep(rate_limiter.current_interval)

# Cleanup en finally
```

### Checklist Fase 7
- [ ] 7.1 main.py
- [ ] 7.2 Test E2E
- [ ] 7.3 Paralelo con V6
- [ ] 7.4 Latencia OK
- [ ] 7.5 Duplicados OK
- [ ] 7.6 Documentación

---

## 📊 Resumen de Progreso

```
Fase 0:  Setup          [████] 100%
Fase 1:  Domain Core    [____] 0%
Fase 2:  Calculators    [____] 0%
Fase 3:  Validators     [____] 0%
Fase 4:  Config         [____] 0%
Fase 5A: Redis          [____] 0%
Fase 5B: API Client     [____] 0%
Fase 5C: Messaging      [____] 0%
Fase 6:  Application    [____] 0%
Fase 7:  Integración    [____] 0%

Total: 9/57 tareas completadas
```

---

## 🎯 Recomendación de Orden

```
Semana 1: Fase 0 + Fase 1 + Fase 2
          (Setup + Domain puro + Calculators)
          
Semana 2: Fase 3 + Fase 4
          (Validators + Config)
          
Semana 3: Fase 5A + Fase 5B + Fase 5C
          (Infrastructure dividida en 3 sub-fases)
          
Semana 4: Fase 6 + Fase 7
          (Application + Integración)
```

**Consejo**: No saltes fases. Cada fase depende de la anterior. Si intentas hacer infrastructure sin domain, tendrás que rehacer código.

---

## 🧪 Nota sobre Tests de Integración

> [!TIP]
> **Recomendación**: Usar [Testcontainers](https://testcontainers.com/) para tests de integración con Redis.
> 
> ```python
> # En lugar de depender de Redis local:
> from testcontainers.redis import RedisContainer
> 
> @pytest.fixture
> async def redis_container():
>     with RedisContainer() as redis:
>         yield redis.get_connection_url()
> ```
> 
> **Beneficios**:
> - Tests reproducibles sin dependencias locales
> - CI/CD no necesita Redis preinstalado
> - Aislamiento entre tests