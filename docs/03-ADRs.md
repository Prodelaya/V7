# Registro de Decisiones Arquitectónicas (ADR)
## Sistema Retador v2.0

**Fecha de inicio**: Diciembre 2025  
**Estado**: Activo  
**Última actualización**: Integración selectiva de propuestas V7

---

## Índice de Decisiones

| ID      | Título                                         | Estado    | Fecha    |
| ------- | ---------------------------------------------- | --------- | -------- |
| ADR-001 | Arquitectura Monolito Modular                  | Aceptada  | Dic 2024 |
| ADR-002 | Strategy Pattern para Cálculos por Sharp       | Aceptada  | Dic 2024 |
| ADR-003 | Fórmula de Cuota Mínima                        | Aceptada  | Dic 2024 |
| ADR-004 | Redis para Deduplicación (sin Bloom Filter)    | Aceptada  | Dic 2024 |
| ADR-005 | Chain of Responsibility para Validación        | Aceptada  | Dic 2024 |
| ADR-006 | Multi-Bot Telegram con Heap Priorizado         | Aceptada  | Dic 2024 |
| ADR-007 | Persistencia PostgreSQL Diferida               | Diferida  | Dic 2024 |
| ADR-008 | Value Objects para Datos de Dominio            | Aceptada  | Dic 2024 |
| ADR-009 | Cursor Incremental para API                    | Aceptada  | Dic 2024 |
| ADR-010 | Polling Adaptativo con Backoff                 | Aceptada  | Dic 2024 |
| ADR-011 | Cache HTML en Message Formatter                | Aceptada  | Dic 2024 |
| ADR-012 | Rechazo de Bloom Filter                        | Rechazada | Dic 2024 |
| ADR-013 | Rechazo de Fire-and-Forget Redis               | Rechazada | Dic 2024 |
| ADR-014 | Procesamiento con asyncio.gather (sin workers) | Aceptada  | Dic 2024 |
| ADR-015 | Filtrado en Origen (API Parameters)            | Aceptada  | Dic 2024 |
| ADR-016 | Sistema de Suscripciones Automatizado          | Propuesta | Dic 2024 |

---

## ADR-001: Arquitectura Monolito Modular

### Estado
**Aceptada**

### Contexto
El sistema actual (v6) es un script monolítico de ~1500 líneas con todas las responsabilidades mezcladas. Necesitamos escalar a un sistema profesional, mantenible y testeable.

### Decisión
Adoptamos **Monolito Modular** con Clean Architecture (Domain, Application, Infrastructure).

### Justificación
- Volumen actual (200-500 picks/hora) no justifica microservicios
- La latencia es la ventaja competitiva principal
- Un solo proceso facilita monitoreo y despliegue
- Estructura modular permite migrar a microservicios si es necesario

### Consecuencias
**Positivas**: Despliegue simple, latencia interna ~0ms, debugging simple
**Negativas**: Escala vertical, fallo total si el proceso muere

---

## ADR-002: Strategy Pattern para Cálculos por Sharp

### Estado
**Aceptada**

### Contexto
Actualmente solo usamos Pinnacle como sharp, pero el sistema debe soportar múltiples sharps en el futuro.

### Decisión
Implementar **Strategy Pattern** para encapsular la lógica de cálculo por sharp.

### Justificación
- Open/Closed Principle: Añadir sharps sin modificar código existente
- Single Responsibility: Cada estrategia maneja una sharp
- Testeable: Cada estrategia se prueba aisladamente

---

## ADR-003: Fórmula de Cuota Mínima

### Estado
**Aceptada**

### Contexto
La fórmula anterior era incorrecta y aceptaba picks con -3% de profit creyendo que el límite era -1%.

### Decisión
Adoptar la fórmula matemáticamente correcta:
```python
min_odds = 1 / (1.01 - 1/odd_pinnacle)
```

### Justificación
- Corte exacto en -1% de profit
- Impacto económico estimado: +900€/mes por cada 1000€/día apostados

---

## ADR-004: Redis para Deduplicación (sin Bloom Filter)

### Estado
**Aceptada** (actualizada - rechaza Bloom Filter)

### Contexto
Necesitamos prevenir duplicados y rebotes. El informe V7 propuso usar Bloom Filter para optimizar latencia.

### Decisión
Usar **Redis con pipeline batch**, **SIN Bloom Filter**.

### Justificación

| Criterio            | Redis Pipeline  | Redis + Bloom     |
| ------------------- | --------------- | ----------------- |
| Latencia            | ~10ms (50 keys) | ~2ms              |
| Falsos positivos    | 0%              | ~1%               |
| Picks perdidos/hora | 0               | ~5 (en 500 picks) |
| Complejidad         | Baja            | Media             |
| Dependencias        | 0 nuevas        | +1 (pybloom)      |

**Factor decisivo**: 1% de falsos positivos = picks válidos con valor NO enviados = pérdida de dinero para el apostador. La ganancia de 8ms no justifica el riesgo.

### Consecuencias
**Positivas**: Cero picks perdidos por falsos positivos, simplicidad
**Negativas**: ~8ms más de latencia (insignificante vs API ~200ms)

---

## ADR-005: Chain of Responsibility para Validación

### Estado
**Aceptada**

### Contexto
Un pick debe pasar múltiples validaciones antes de procesarse.

### Decisión
Implementar **Chain of Responsibility** con orden optimizado (fail-fast).

### Orden de Ejecución
1. OddsValidator (CPU, ~0ms)
2. ProfitValidator (CPU, ~0ms)
3. TimeValidator (CPU, ~0ms)
4. DuplicateValidator (I/O Redis, ~5ms)
5. OppositeMarketValidator (I/O Redis, ~5ms)

---

## ADR-006: Multi-Bot Telegram con Heap Priorizado

### Estado
**Aceptada** (actualizada - añade heap)

### Contexto
Telegram tiene rate limits. El informe V7 propuso priorizar envío por profit.

### Decisión
Pool de 5 bots con **cola de prioridad (heap)** ordenada por profit descendente.

### Justificación
- Picks de mayor valor se envían primero
- Si hay congestión, se descartan los de menor valor
- `heapq` es O(log n) para insert/extract

### Implementación
```python
# Heap: (-profit, timestamp, channel_id, message)
# Negativo para que heapq (min-heap) funcione como max-heap

async def enqueue(self, message: str, channel_id: int, profit: float) -> bool:
    if len(self.heap) >= self.max_size:
        min_profit = -self.heap[0][0]
        if profit <= min_profit:
            return False  # Rechazar pick de bajo valor
        heapq.heappop(self.heap)  # Sacar el de menor valor
    
    heapq.heappush(self.heap, (-profit, time.time(), channel_id, message))
    return True
```

### Consecuencias
**Positivas**: Mayor valor enviado primero, degradación graceful bajo carga
**Negativas**: Picks de bajo valor pueden perderse bajo congestión extrema

---

## ADR-007: Persistencia PostgreSQL Diferida

### Estado
**Diferida**

### Contexto
Guardar histórico permitiría análisis, pero requiere normalización compleja.

### Decisión
Diferir hasta que el sistema core esté estable y exista módulo de normalización.

---

## ADR-008: Value Objects para Datos de Dominio

### Estado
**Aceptada**

### Decisión
Implementar Value Objects inmutables con validación en construcción (Odds, Profit, MarketType, EventTime).

---

## ADR-009: Cursor Incremental para API

### Estado
**Aceptada** (nueva - del informe V7)

### Contexto
El sistema actual hace polling sin estado, recibiendo picks ya procesados repetidamente.

### Decisión
Implementar **cursor incremental** usando el campo `sort_by:id` de la API.

### Implementación
```python
async def fetch_picks(self) -> List[dict]:
    params = {
        'product': 'surebets',
        'order': 'created_at_desc',
        'min-profit': -1,
        'limit': 5000,
    }
    
    if self.last_cursor:
        params['cursor'] = self.last_cursor
    
    data = await self._request(params)
    
    if data and data.get('records'):
        picks = data['records']
        # Guardar cursor del último pick para siguiente petición
        last_pick = picks[-1]
        self.last_cursor = f"{last_pick['sort_by']}:{last_pick['id']}"
        await self._persist_cursor()
        return picks
    
    return []
```

### Justificación
- Evita recibir picks ya procesados
- Reduce carga en API y en nuestro sistema
- Persistir en Redis permite recuperación tras reinicio

### Consecuencias
**Positivas**: Menos datos redundantes, menor procesamiento
**Negativas**: Si cursor se corrompe, puede saltar picks (mitigado con validación)

---

## ADR-010: Polling Adaptativo con Backoff

### Estado
**Aceptada** (nueva - del informe V7)

### Contexto
El rate limit de la API (2 req/s) puede saturarse. El informe V7 propuso ajuste dinámico.

### Decisión
Implementar **polling adaptativo con backoff exponencial**.

### Implementación
```python
class AdaptiveRateLimiter:
    def __init__(self):
        self.base_interval = 0.5
        self.max_interval = 5.0
        self.consecutive_429 = 0
    
    @property
    def current_interval(self) -> float:
        return min(self.max_interval, self.base_interval * (2 ** self.consecutive_429))
    
    def report_success(self):
        self.consecutive_429 = max(0, self.consecutive_429 - 1)
    
    def report_rate_limit(self):
        self.consecutive_429 += 1
```

### Tabla de Intervalos

| Errores 429 | Intervalo |
| ----------- | --------- |
| 0           | 0.5s      |
| 1           | 1.0s      |
| 2           | 2.0s      |
| 3           | 4.0s      |
| 4+          | 5.0s      |

### Justificación
- Auto-recuperación cuando el límite se libera
- Sin intervención manual
- Backoff exponencial es estándar en la industria

### Consecuencias
**Positivas**: Manejo robusto de rate limits, auto-healing
**Negativas**: Latencia aumenta bajo carga (aceptable - es protección)

---

## ADR-011: Cache HTML en Message Formatter

### Estado
**Aceptada** (nueva - del informe V7)

### Contexto
El formateo de mensajes repite cálculos para picks del mismo evento.

### Decisión
Cachear partes estáticas del mensaje HTML (teams, tournament, date).

### Implementación
```python
def format_message(self, apuesta: dict, contrapartida: dict, profit: float) -> str:
    event_key = self._get_event_key(apuesta)
    
    # Intentar obtener partes cacheadas
    cached = self._get_cached_parts(event_key)
    
    if cached:
        teams_html = cached['teams']
        tournament_html = cached['tournament']
        date_html = cached['date']
    else:
        teams_html = self._format_teams(apuesta)
        tournament_html = self._format_tournament(apuesta)
        date_html = self._format_date(apuesta)
        self._cache_parts(event_key, {
            'teams': teams_html,
            'tournament': tournament_html,
            'date': date_html
        })
    
    # Partes dinámicas (no cachear)
    stake_emoji = self._calculate_stake(profit)
    min_odds = self._calculate_min_odds(contrapartida['value'])
    
    return self._build_message(stake_emoji, teams_html, ...)
```

### Justificación
- Ahorra ~2-3ms por pick del mismo evento
- Sin riesgo (TTL corto de 60s)
- Las partes cacheadas no cambian para el mismo evento

### Consecuencias
**Positivas**: Menor latencia en picks consecutivos del mismo evento
**Negativas**: ~1KB memoria por entrada de cache (insignificante)

---

## ADR-012: Rechazo de Bloom Filter

### Estado
**Rechazada**

### Contexto
El informe V7 propuso Bloom Filter para reducir latencia de Redis de ~10ms a ~2ms.

### Decisión
**NO implementar Bloom Filter**.

### Justificación

1. **Falsos positivos = Pérdida de dinero**
   - Bloom Filter tiene ~1% de falsos positivos
   - Falso positivo = "creo que ya lo envié" cuando NO lo enviaste
   - En 500 picks/hora = 5 picks/hora perdidos = ~120 picks/día
   - Cada pick perdido es una oportunidad de valor NO aprovechada

2. **El cuello de botella NO es Redis**
   - API externa: ~100-300ms
   - Redis: ~10ms
   - Optimizar Redis de 10ms a 2ms es irrelevante (3% del tiempo total)

3. **Complejidad añadida**
   - Nueva dependencia (`pybloom-live`)
   - Sincronización bloom ↔ Redis
   - El propio informe V7 documenta 4 riesgos altos

### Alternativa implementada
Redis con pipeline batch:
```python
async def exists_batch(self, keys: List[str]) -> Dict[str, bool]:
    async with self.redis.pipeline() as pipe:
        for key in keys:
            pipe.exists(key)
        results = await pipe.execute()
    return dict(zip(keys, results))
```

---

## ADR-013: Rechazo de Fire-and-Forget Redis

### Estado
**Rechazada**

### Contexto
El informe V7 propuso no esperar confirmación de Redis para ganar ~5-10ms.

### Decisión
**NO implementar fire-and-forget**.

### Justificación

1. **Race condition documentada**
   > "Síntoma: Dos picks idénticos con 50-100ms diferencia"
   
   Escenario:
   ```
   T=0ms:  Pick A llega, check_redis() → "no existe"
   T=5ms:  Pick A dispara write_async() (no await)
   T=10ms: Pick A' (mismo evento) llega, check_redis() → "no existe" (write aún no completó)
   T=15ms: Pick A' también se envía → DUPLICADO
   ```

2. **La "mitigación" propuesta es un hack**
   ```python
   # Optimistic lock en cache local
   self.local_cache[key] = True  # antes de Redis
   ```
   Solo funciona en un proceso. Si reinicias, pierdes el lock.

3. **Ganancia marginal**
   - Ahorra ~5-10ms por pick
   - Pero introduce duplicados que cuestan dinero al apostador

### Alternativa implementada
```python
async def mark_sent(self, pick: Pick, ttl: int) -> bool:
    try:
        async with asyncio.timeout(0.1):  # 100ms máximo
            await self.redis.setex(key, ttl, time.time())
            return True
    except asyncio.TimeoutError:
        logger.warning(f"Redis timeout para {key}")
        return False
```

---

## ADR-014: Procesamiento con asyncio.gather (sin workers)

### Estado
**Aceptada** (nueva - del informe V7)

### Contexto
V6 usa 3 tipos de workers con colas internas:
- validation_queue → validation_workers
- redis_queue → redis_workers
- telegram_queue → telegram_workers

### Decisión
Eliminar workers y colas internas, usar **asyncio.gather** para procesamiento paralelo.

### Implementación
```python
# V6 (workers/colas)
await self.validation_queue.put(pick)
# ... pick viaja por 3 colas ...

# V2.0 (gather directo)
async def process_batch(self, picks: List[dict]) -> List[ProcessedPick]:
    tasks = [self._process_single(pick) for pick in picks]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return [r for r in results if isinstance(r, ProcessedPick)]
```

### Justificación
- Las colas internas añaden latencia (~5-10ms por cola)
- `asyncio.gather` es suficiente para el volumen
- Simplifica debugging (sin estados intermedios)
- Reduce complejidad de código

### Consecuencias
**Positivas**: Menor latencia, código más simple, debugging más fácil
**Negativas**: Menos control granular sobre backpressure (aceptable para volumen actual)

---

## ADR-015: Filtrado en Origen (API Parameters)

### Estado
**Aceptada** (nueva - análisis de optimización API)

### Contexto
El análisis de la API de apostasseguras.com reveló que solo usábamos una fracción de los parámetros de filtrado disponibles. Esto resultaba en recibir ~5000 picks y filtrar ~80% en código.

### Decisión
Implementar **filtrado en origen** usando todos los parámetros de API disponibles.

### Parámetros Implementados

| Parámetro              | Valor   | Propósito                                |
| ---------------------- | ------- | ---------------------------------------- |
| `outcomes`             | `2`     | Solo surebets de 2 patas                 |
| `min-profit`           | `-1`    | Profit mínimo                            |
| `max-profit`           | `25`    | Profit máximo                            |
| `min-odds`             | `1.10`  | Cuota mínima                             |
| `max-odds`             | `9.99`  | Cuota máxima                             |
| `hide-different-rules` | `true`  | Excluir surebets con reglas conflictivas |
| `startAge`             | `PT10M` | Solo surebets < 10 min antigüedad        |
| `oddsFormat`           | `eu`    | Formato decimal explícito                |



### Justificación

**Impacto cuantificado**:
- **Antes**: Recibíamos ~5000 picks, filtrar en código, ~500 válidos
- **Después**: Recibimos ~1000-2000 picks (pre-filtrados), ~500 válidos
- **Ahorro**: ~60-70% menos datos a procesar

**Beneficios**:
1. Menor consumo de ancho de banda
2. Menor carga de CPU en validaciones
3. Menor uso de memoria
4. Menor latencia end-to-end

### Consecuencias
**Positivas**: Reducción significativa de datos procesados, menor latencia
**Negativas**: Mayor dependencia de la estabilidad de parámetros de API

| Validador       | Antes               | Después               |
| --------------- | ------------------- | --------------------- |
| OddsValidator   | Validación primaria | Optional safety check |
| ProfitValidator | Validación primaria | Optional safety check |

---

## ADR-016: Sistema de Suscripciones Automatizado

### Estado
**Propuesta**

### Contexto
Implementación de sistema de suscripciones con canales exclusivos por cliente. Flujo automático: selección → pago → provisioning → acceso.

### Decisiones Clave
- **Telegram**: Userbot con Telethon (MTProto) para crear canales programáticamente
- **Pagos**: Stripe Checkout + Billing con webhooks
- **Web**: FastAPI + Jinja2 para landing page y webhooks
- **Base de Datos**: PostgreSQL con tablas `customers`, `service_plans`, `subscriptions`, `telegram_channels`

### Componentes Nuevos
- `src/subscriptions/` - Módulo completo de suscripciones
- `src/web/` - Landing page y webhooks
- `migrations/` - Scripts SQL para nuevas tablas

### Documentación Detallada
📄 **[ADR-016-Subscriptions.md](./ADRs/ADR-016-Subscriptions.md)** - Documento completo con:
- Análisis de alternativas
- Arquitectura de bots
- Modelo de datos SQL
- Flujo de provisioning
- Estimaciones y riesgos

---

## Apéndice A: Resumen de Decisiones V7

| Propuesta V7           | Decisión    | ADR                       |
| ---------------------- | ----------- | ------------------------- |
| Bloom Filter           | ❌ Rechazada | ADR-012                   |
| Fire-and-forget Redis  | ❌ Rechazada | ADR-013                   |
| Estructura carpetas V7 | ❌ Rechazada | (usar Clean Architecture) |
| Cursor incremental     | ✅ Aceptada  | ADR-009                   |
| Polling adaptativo     | ✅ Aceptada  | ADR-010                   |
| Cache HTML             | ✅ Aceptada  | ADR-011                   |
| Heap priorizado        | ✅ Aceptada  | ADR-006 (actualizado)     |
| Eliminar workers       | ✅ Aceptada  | ADR-014                   |
| Filtrado en origen     | ✅ Aceptada  | ADR-015                   |

---

## Apéndice B: Plantilla para Nuevas Decisiones

```markdown
## ADR-XXX: [Título]

### Estado
[Propuesta | Aceptada | Rechazada | Deprecada | Sustituida por ADR-YYY]

### Contexto
[Descripción del problema y contexto]

### Decisión
[La decisión tomada]

### Justificación
[Por qué esta decisión sobre las alternativas]

### Consecuencias
**Positivas**: ...
**Negativas**: ...

### Alternativas Consideradas
[Otras opciones evaluadas y por qué se descartaron]
```

---

## Historial de Cambios

| Fecha    | Versión | Cambios                                                                      | Autor          |
| -------- | ------- | ---------------------------------------------------------------------------- | -------------- |
| Dic 2024 | 1.0     | Documento inicial con 8 ADRs                                                 | Equipo Retador |
| Dic 2024 | 2.0     | Integración selectiva V7: +6 ADRs (009-014), actualización ADR-004 y ADR-006 | Equipo Retador |