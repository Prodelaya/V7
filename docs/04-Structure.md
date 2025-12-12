# 🗂️ Guía de Estructura del Proyecto Retador v2.0

## 📖 Introducción: ¿Por qué esta estructura?

Imagina tu código V6 como una **casa donde todo está en una sola habitación**: cocina, dormitorio, baño, todo junto. Funciona, pero si quieres cambiar algo (por ejemplo, el grifo del baño), corres el riesgo de romper la cocina.

La nueva estructura es como una **casa con habitaciones separadas**: cada cosa en su lugar. Si cambias algo en la cocina, el baño sigue funcionando.

---

## 🏠 Vista General: Las "Habitaciones" del Proyecto

```
retador/
├── 📚 docs/           → Documentación (los "planos" de la casa)
├── 🏚️ legacy/         → Código antiguo V6 (referencia, no usar)
├── 🧠 src/            → Código nuevo (la casa nueva)
│   ├── domain/        → "El cerebro" - Reglas de negocio puras
│   ├── application/   → "El coordinador" - Organiza el trabajo
│   ├── infrastructure/→ "Las manos" - Hace el trabajo real (API, Redis, Telegram)
│   ├── config/        → "Los ajustes" - Configuración
│   └── shared/        → "Herramientas comunes" - Cosas que todos usan
├── 🧪 tests/          → Pruebas automáticas
└── 📜 scripts/        → Punto de entrada (arranque)
```

---

## 📁 Explicación Carpeta por Carpeta

### 📚 `docs/` - La Documentación

| Archivo | ¿Para qué sirve? |
|---------|------------------|
| `01-SRS.md` | **Qué debe hacer** el sistema (requisitos) |
| `02-PDR.md` | **Cómo está diseñado** (arquitectura, diagramas) |
| `03-ADRs.md` | **Por qué tomamos cada decisión** (justificaciones) |

**Analogía**: Son los planos del arquitecto. Antes de construir, miras los planos.

---

### 🏚️ `legacy/` - El Código Antiguo

| Archivo | ¿Para qué sirve? |
|---------|------------------|
| `RetadorV6.py` | Tu código actual, guardado como **referencia**. No se ejecuta, solo se consulta para ver cómo funcionaban las cosas. |

**Analogía**: Es la foto de tu casa antigua. No vives ahí, pero la miras para recordar cómo era.

---

### 🧠 `src/domain/` - El Cerebro (Reglas de Negocio)

Esta es la parte más importante. Aquí están las **reglas del negocio de apuestas**, sin importar si usas Telegram, Redis o lo que sea. Son reglas puras.

#### `domain/value_objects/` - Los "Tipos de Datos Inteligentes"

| Archivo | ¿Qué representa? | Origen en V6 |
|---------|------------------|--------------|
| `odds.py` | Una **cuota** (ej: 2.05). Se valida automáticamente que esté entre 1.01 y 1000. | Antes era un simple `float` sin validación |
| `profit.py` | Un **porcentaje de profit** (ej: 2.5%). Se valida que esté entre -100% y 100%. | Antes era un simple `float` |
| `market_type.py` | El **tipo de mercado** (over, under, win1, etc.). Lista cerrada de valores válidos. | Antes eran strings sin validar |

**Analogía**: En lugar de decir "dame un número", dices "dame una cuota válida". Si alguien te da -5, el sistema lo rechaza automáticamente.

#### `domain/entities/` - Las "Cosas" del Negocio

| Archivo | ¿Qué representa? | Origen en V6 |
|---------|------------------|--------------|
| `pick.py` | Un **pick completo**: equipos, cuota, mercado, tiempo, bookie. Todo junto y validado. | Antes era un `dict` suelto |
| `surebet.py` | Una **surebet**: dos patas (sharp y soft) + el profit. | Antes era un `dict` con `prongs` |
| `bookmaker.py` | Una **casa de apuestas**: nombre, si es sharp o soft, configuración. | Antes estaba en `BotConfig` |

**Analogía**: Son los "sustantivos" de tu negocio. Un pick, una surebet, una bookie.

#### `domain/services/` - Los "Cálculos"

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `calculation_service.py` | Orquesta los cálculos: pide el stake y la cuota mínima. | Nuevo (antes mezclado en `MessageFormatter`) |
| `opposite_market_service.py` | Dado un mercado (ej: "over"), te dice el opuesto ("under"). | `opposite_markets` dict en `RedisHandler` |

##### `domain/services/calculators/` - Las Fórmulas Matemáticas

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `base.py` | Define la **interfaz**: "todo calculador debe tener estos métodos". | Nuevo |
| `pinnacle.py` | Calcula stake y cuota mínima **usando Pinnacle como sharp**. | `get_stake()` y `calculate_min_odds()` de `MessageFormatter` |
| `factory.py` | Dado el nombre "pinnaclesports", te devuelve el calculador correcto. | Nuevo |

**⚠️ IMPORTANTE**: La fórmula de `calculate_min_odds` en V6 estaba **mal**. En `pinnacle.py` está corregida.

#### `domain/rules/` - Las Validaciones

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `validation_chain.py` | Encadena todas las validaciones en orden. | Nuevo (antes todo en `validate_pick()`) |

##### `domain/rules/validators/` - Cada Validación Individual

| Archivo | ¿Qué valida? | Origen en V6 |
|---------|--------------|--------------|
| `base.py` | Define la interfaz de un validador. | Nuevo |
| `odds_validator.py` | ¿La cuota está entre 1.10 y 9.99? | Parte de `validate_pick()` |
| `profit_validator.py` | ¿El profit está entre -1% y 25%? | Parte de `validate_pick()` |
| `time_validator.py` | ¿El evento es en el futuro? | Parte de `validate_pick()` |
| `duplicate_validator.py` | ¿Ya enviamos este pick? (consulta Redis) | Parte de `redis_worker()` |

**Analogía**: En V6 tenías un método gigante `validate_pick()` que hacía todo. Ahora cada validación es una pieza separada que puedes probar, cambiar o quitar independientemente.

---

### 🎯 `src/application/` - El Coordinador

Esta capa **organiza el trabajo** pero no hace el trabajo real. Es como un director de orquesta.

#### `application/handlers/`

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `pick_handler.py` | Coordina todo el flujo: recibir pick → validar → guardar en Redis → enviar a Telegram. | Lógica de `process_single_pick()` y los workers |

#### `application/dto/`

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `pick_dto.py` | "Data Transfer Object" - Estructura para pasar datos entre capas. | Nuevo |

**Analogía**: El `pick_handler` es como un camarero. No cocina (eso lo hace la cocina/infrastructure), no decide el menú (eso lo hace el chef/domain), pero lleva los platos de un lado a otro.

---

### 🔌 `src/infrastructure/` - Las Manos (Conexiones Externas)

Aquí está todo lo que **habla con el mundo exterior**: APIs, bases de datos, Telegram.

#### `infrastructure/api/` - Conexión con la API de Surebets

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `surebet_client.py` | Llama a la API, obtiene picks, gestiona el **cursor incremental**. | `RequestQueue` + `fetch_picks()` |
| `rate_limiter.py` | Controla el **polling adaptativo**: si hay muchos errores 429, espera más. | Nuevo (inspirado en V7) |

**Mejoras sobre V6**:
- Cursor incremental (no recibe picks repetidos)
- Polling adaptativo (si la API dice "para", para)
- Parámetros optimizados (`order=created_at_desc`, `min-profit=-1`)

#### `infrastructure/repositories/` - Conexión con Bases de Datos

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `base.py` | Define la interfaz: "todo repositorio debe tener save(), exists(), etc." | Nuevo |
| `redis_repository.py` | Guarda y consulta picks en Redis para evitar duplicados. | `RedisHandler` |
| `_postgres_repository.py` | (Futuro) Guardará histórico en PostgreSQL. | No existe en V6 |

**⚠️ IMPORTANTE**: No usamos Bloom Filter ni fire-and-forget. Eso causaba bugs.

#### `infrastructure/messaging/` - Conexión con Telegram

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `telegram_gateway.py` | Envía mensajes a Telegram con **heap priorizado** (mayor profit primero) y rotación de bots. | `TelegramSender` |
| `message_formatter.py` | Formatea el mensaje HTML con **cache** para partes que no cambian. | `MessageFormatter` |

**Mejoras sobre V6**:
- Heap priorizado: si hay congestión, se envían primero los picks de mayor valor
- Cache HTML: no recalcula equipos/torneo/fecha si ya lo hizo para ese evento

#### `infrastructure/cache/`

| Archivo | ¿Qué hace? | Origen en V6 |
|---------|------------|--------------|
| `local_cache.py` | Cache en memoria para evitar consultas repetidas a Redis. | `CacheManager` |

---

### ⚙️ `src/config/` - La Configuración

| Archivo | ¿Qué contiene? | Origen en V6 |
|---------|----------------|--------------|
| `settings.py` | Todas las configuraciones: URLs, tokens, límites, intervalos de polling. | `BotConfig` |
| `bookmakers.py` | Lista de bookies, cuáles son sharp, cuáles soft, sus canales de Telegram. | Parte de `BotConfig` |
| `logging_config.py` | Configuración de logs y alertas por Telegram. | `TelegramLogHandler` + logging básico |

---

### 🧰 `src/shared/` - Herramientas Comunes

| Archivo | ¿Qué contiene? | Origen en V6 |
|---------|----------------|--------------|
| `exceptions.py` | Errores personalizados: `InvalidOddsError`, `ApiConnectionError`, etc. | Nuevo |
| `constants.py` | Constantes globales: emojis, formatos de fecha, etc. | Disperso en V6 |

---

### 🧪 `tests/` - Las Pruebas

| Carpeta | ¿Qué prueba? |
|---------|--------------|
| `unit/domain/` | Pruebas de lógica pura (calculadores, validadores) sin conexiones externas |
| `integration/` | Pruebas con conexiones reales (Redis, API) |

---

## 🔄 ¿Cómo se Comunican las Partes?

```
┌─────────────────────────────────────────────────────────────────┐
│                        FLUJO DE UN PICK                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. API de Surebets                                             │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ infrastructure/api/surebet_client.py                     │   │
│  │ "Oye API, dame picks nuevos desde el último cursor"      │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     │ Lista de picks (dicts crudos)                            │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ application/handlers/pick_handler.py                     │   │
│  │ "Voy a procesar cada pick"                               │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     │ Para cada pick:                                          │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ domain/rules/validation_chain.py                         │   │
│  │ "¿Cuota OK? ¿Profit OK? ¿Tiempo OK?"                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     │ Si pasa validaciones:                                    │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ infrastructure/repositories/redis_repository.py          │   │
│  │ "¿Ya envié este pick o su opuesto?"                      │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     │ Si no es duplicado:                                      │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ domain/services/calculation_service.py                   │   │
│  │ "Calcula stake (🔴🟠🟡🟢) y cuota mínima"                 │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ infrastructure/messaging/message_formatter.py            │   │
│  │ "Formatea el mensaje HTML bonito"                        │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     ▼                                                           │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ infrastructure/messaging/telegram_gateway.py             │   │
│  │ "Encola en heap por profit y envía al canal"            │   │
│  └─────────────────────────────────────────────────────────┘   │
│     │                                                           │
│     ▼                                                           │
│  2. Canal de Telegram del apostador                            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🆚 Comparativa V6 → V2.0

| Aspecto | V6 (Antes) | V2.0 (Ahora) |
|---------|------------|--------------|
| **Archivos** | 1 archivo de 2000 líneas | 54 archivos organizados |
| **Si quiero cambiar la fórmula de stake** | Buscar en 2000 líneas, rezar para no romper nada | Abrir `domain/services/calculators/pinnacle.py`, cambiar, listo |
| **Si quiero añadir una nueva sharp (ej: Betfair)** | Modificar código existente en varios sitios | Crear `betfair.py` en calculators, registrar en factory |
| **Si quiero probar que el cálculo funciona** | Ejecutar todo el bot y ver qué pasa | Ejecutar `pytest tests/unit/domain/test_calculators.py` |
| **Si Redis falla** | Todo el bot podría fallar | Solo falla la parte de Redis, el resto sigue |
| **Fórmula de cuota mínima** | ❌ Incorrecta (-3% real) | ✅ Correcta (-1% real) |

---

## 🎯 Resumen: ¿Qué Archivo Toco Para...?

| Si quiero... | Archivo(s) a tocar |
|--------------|-------------------|
| Cambiar rangos de profit para stake | `domain/services/calculators/pinnacle.py` |
| Añadir una nueva bookie | `config/bookmakers.py` |
| Cambiar el formato del mensaje | `infrastructure/messaging/message_formatter.py` |
| Añadir una nueva validación | Crear archivo en `domain/rules/validators/` + añadir a `validation_chain.py` |
| Cambiar cómo se conecta a la API | `infrastructure/api/surebet_client.py` |
| Cambiar tokens o configuración | `config/settings.py` o variables de entorno |
| Ver cómo funcionaba algo en V6 | `legacy/RetadorV6.py` (solo consulta) |