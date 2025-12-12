# Especificación de Requisitos de Software (SRS)
## Sistema Retador v2.0

**Versión**: 2.1  
**Fecha**: Diciembre 2024  
**Estado**: Aprobado  
**Última actualización**: Integración de optimizaciones V7

---

## 1. Introducción

### 1.1 Propósito
Este documento especifica los requisitos funcionales y no funcionales del sistema Retador v2.0, una plataforma de detección y distribución de apuestas de valor basadas en arbitraje entre casas de apuestas sharp y soft.

### 1.2 Alcance
Retador v2.0 es un sistema que:
- Consume datos de surebets de un proveedor externo (API apostasseguras.com)
- Filtra y valida oportunidades de valor según reglas de negocio específicas
- Distribuye picks a apostadores profesionales vía Telegram
- Previene duplicados y rebotes de cuotas mediante almacenamiento en Redis

### 1.3 Definiciones y Acrónimos

| Término | Definición |
|---------|------------|
| **Sharp** | Casa de apuestas con cuotas eficientes (ej: Pinnacle) |
| **Soft** | Casa de apuestas con márgenes altos y cuotas ineficientes |
| **Surebet** | Arbitraje entre dos cuotas que garantiza beneficio apostando ambas |
| **Value bet** | Apuesta con esperanza matemática positiva |
| **Profit** | Porcentaje de ganancia teórica de una surebet |
| **Prong** | Cada pata/lado de una surebet |
| **Pick** | Recomendación de apuesta enviada al usuario |
| **Rebote** | Inversión de cuotas por entrada masiva de dinero |
| **Cursor** | Puntero para paginación incremental en API |

### 1.4 Referencias
- Documentación API apostasseguras.com
- Código fuente RetadorV6.py (versión actual)
- Informe de análisis V7 (parcialmente integrado)

---

## 2. Descripción General

### 2.1 Perspectiva del Producto
Retador v2.0 es una evolución del sistema actual (v6) hacia una arquitectura profesional, escalable y mantenible. El sistema opera como intermediario entre un proveedor de datos de arbitraje y apostadores profesionales.

### 2.2 Modelo de Negocio

#### 2.2.1 Supuestos Fundamentales
1. **Pinnacle (Sharp)**: Referente de mercado con cuotas que representan probabilidades reales (~2-3% margen)
2. **Bookies Soft**: Cuotas infladas con márgenes altos (~4-6%), ofrecen valor cuando divergen de la sharp

#### 2.2.2 Estrategia de Valor
- Se detectan surebets entre Pinnacle y bookies soft
- Solo se apuesta a la pata de la soft (no arbitraje real)
- Se aceptan surebets hasta -1% de profit porque:
  - El margen de Pinnacle no se descuenta en el cálculo
  - Las soft inflan cuotas para atraer clientes
  - El valor esperado real es positivo

### 2.3 Funciones del Producto
1. **Obtención de datos**: Polling incremental a API de surebets con cursor
2. **Filtrado**: Validación de picks según reglas de negocio
3. **Deduplicación**: Prevención de picks duplicados y rebotes (Redis)
4. **Cálculo**: Stake recomendado y cuota mínima aceptable
5. **Priorización**: Envío ordenado por profit (mayor valor primero)
6. **Distribución**: Envío de picks por Telegram con rotación de bots

### 2.4 Usuarios y Características

| Usuario | Descripción | Necesidades |
|---------|-------------|-------------|
| Apostador profesional | Cliente suscrito al servicio | Picks rápidos, precisos, con info clara |
| Operador | Administrador del sistema | Monitoreo, logs, métricas |

### 2.5 Restricciones
- Dependencia de API externa (apostasseguras.com)
- Rate limit de API: 2 req/segundo
- Latencia crítica: ventaja competitiva basada en velocidad
- Sin acceso a WebSockets (solo REST polling)

### 2.6 Suposiciones y Dependencias
- Disponibilidad de API del proveedor
- Conectividad con servidores de Telegram
- Servidor Redis operativo
- Las soft mantienen cuotas durante ventana de tiempo suficiente

---

## 3. Requisitos Específicos

### 3.1 Requisitos Funcionales

#### RF-001: Obtención de Surebets con Cursor Incremental
- **Descripción**: El sistema debe obtener surebets de la API usando paginación incremental
- **Entrada**: Configuración de bookmakers, deportes, límites, cursor
- **Salida**: Lista de surebets con 2 prongs (solo nuevos desde último cursor)
- **Reglas**:
  - Solo surebets de 2 patas
  - Filtrar por bookmakers configurados
  - Usar parámetro `cursor` con formato `{sort_by}:{id}` del último pick
  - Ordenar por `created_at_desc` en API (picks más recientes primero)
  - Incluir `min-profit=-1` para filtrar en origen
  - Persistir cursor en Redis para sobrevivir reinicios

#### RF-002: Polling Adaptativo
- **Descripción**: El sistema debe ajustar dinámicamente el intervalo de polling según respuesta de API
- **Reglas**:
  - Intervalo base: 0.5 segundos
  - Si recibe HTTP 429: incrementar intervalo con backoff exponencial (máx 5s)
  - Si recibe respuesta exitosa: decrementar contador de errores gradualmente
  - Fórmula: `interval = min(5.0, 0.5 * (2 ** consecutive_429))`

#### RF-003: Validación de Picks
- **Descripción**: Cada pick debe pasar validaciones antes de procesarse
- **Validaciones** (en orden, fail-fast):
  1. Cuota en rango [1.10, 9.99]
  2. Profit en rango [-1%, 25%]
  3. Evento en el futuro (>0 segundos)
  4. Una pata debe ser la sharp (Pinnacle)
  5. Otra pata debe ser una soft objetivo
  6. No duplicado en Redis (clave principal)
  7. Mercado opuesto no enviado (Redis)

#### RF-004: Deduplicación con Redis
- **Descripción**: Prevenir envío de picks duplicados o rebotados
- **Reglas**:
  - Clave única: `{team1}:{team2}:{timestamp}:{market}:{variety}:{bookie}`
  - TTL en Redis = tiempo hasta inicio del evento
  - Verificar mercado opuesto (over↔under, win1↔win2, etc.)
  - Usar pipeline batch para verificación eficiente
  - **NO usar Bloom Filter** (riesgo de falsos positivos = pérdida de picks válidos)
  - **NO usar fire-and-forget** (riesgo de race conditions = duplicados)

#### RF-005: Cálculo de Stake
- **Descripción**: Asignar nivel de confianza según profit
- **Rangos para Pinnacle**:

  | Profit | Emoji | Confianza |
  |--------|-------|-----------|
  | -1% a -0.5% | 🔴 | Baja |
  | -0.5% a 1.5% | 🟠 | Media-baja |
  | 1.5% a 4% | 🟡 | Media-alta |
  | >4% | 🟢 | Alta |

#### RF-006: Cálculo de Cuota Mínima
- **Descripción**: Calcular cuota mínima en soft para mantener -1% de value
- **Fórmula**: `min_odds = 1 / (1.01 - 1/odd_pinnacle)`
- **Propósito**: Informar al apostador si la cuota ha bajado demasiado

#### RF-007: Formateo de Mensaje con Cache HTML
- **Descripción**: Generar mensaje legible para Telegram con cache de partes estáticas
- **Contenido**:
  - Emoji de stake
  - Tipo de apuesta (mercado, condición, período)
  - Cuota actual y cuota mínima
  - Equipos y torneo
  - Fecha/hora del evento
  - Enlace a la casa de apuestas
- **Cache**:
  - Cachear partes que no cambian por evento: teams, tournament, date
  - Clave de cache: `{team1}:{team2}:{timestamp}:{bookie}`
  - TTL de cache: 60 segundos

#### RF-008: Envío Priorizado a Telegram
- **Descripción**: Distribuir picks priorizando por profit (mayor valor primero)
- **Requisitos**:
  - Cola de prioridad (heap) ordenada por profit descendente
  - Tamaño máximo de cola: 1000 mensajes
  - Si cola llena: rechazar picks de menor profit que el mínimo en cola
  - Soporte multi-bot para rate limiting (5 bots)
  - Reintentos con backoff exponencial
  - Rotación de bots ante límites (30 msg/s por bot)

#### RF-009: Gestión de Configuración
- **Descripción**: Configuración externalizada y modificable
- **Elementos**:
  - Bookmakers objetivo y sus contrapartidas
  - Canales de Telegram por bookie
  - Tokens de API y bots
  - Rangos de validación
  - Parámetros de polling (intervalo base, máximo)
  - Parámetros de API (min-profit, order, limit)

### 3.2 Requisitos No Funcionales

#### RNF-001: Rendimiento
- Latencia máxima API→Telegram: <500ms (objetivo: <100ms)
- Throughput: >500 picks/hora procesados
- Tiempo de respuesta Redis: <10ms
- Polling adaptativo: 0.5s - 5.0s según carga

#### RNF-002: Disponibilidad
- Uptime objetivo: 99.5%
- Recuperación automática ante fallos transitorios
- Reconexión automática a Redis/API
- Persistencia de cursor para recuperación tras reinicio

#### RNF-003: Escalabilidad
- Soporte para múltiples bookies soft sin cambios de código
- Adición de nuevas sharps mediante configuración
- Preparado para escalar a microservicios si es necesario

#### RNF-004: Mantenibilidad
- Código modular con separación de responsabilidades
- Cobertura de tests >80% en lógica de dominio
- Documentación de código y API interna

#### RNF-005: Observabilidad
- Logs estructurados con niveles (DEBUG, INFO, WARNING, ERROR)
- Alertas por Telegram para errores críticos
- Métricas de latencia (preparado para futuro)
- Logging de estadísticas cada 10 segundos

#### RNF-006: Seguridad
- Tokens en variables de entorno (no hardcodeados)
- Conexión Redis con autenticación
- Sin exposición de endpoints públicos

---

## 4. Requisitos de Interfaces

### 4.1 Interfaz con API Proveedor
- **Protocolo**: HTTPS REST
- **Autenticación**: Bearer token
- **Rate limit**: 2 req/s
- **Formato**: JSON
- **Parámetros optimizados**:
  - `cursor`: Paginación incremental
  - `order`: `created_at_desc`
  - `min-profit`: `-1`
  - `limit`: `5000`

### 4.2 Interfaz con Redis
- **Protocolo**: Redis protocol (TCP)
- **Autenticación**: Password
- **Operaciones**: GET, SET, SETEX, EXISTS, PIPELINE
- **Datos persistidos**:
  - Picks enviados (con TTL)
  - Último cursor procesado

### 4.3 Interfaz con Telegram
- **Protocolo**: HTTPS (Telegram Bot API)
- **Autenticación**: Bot tokens (pool de 5)
- **Rate limit**: 30 msg/s por bot (150 msg/s total)
- **Formato**: HTML parseado

---

## 5. Requisitos Futuros (No en Alcance v2.0)

### 5.1 Sistema de Suscripciones
- Gestión de clientes
- Canales/bots personalizados por cliente
- Facturación y control de acceso

### 5.2 Histórico y Estadísticas
- Persistencia en PostgreSQL
- Resolución automática de picks
- Dashboard de rentabilidad

### 5.3 Yield Real
- Cálculo dinámico de margen por liga/deporte
- Probabilidades implícitas corregidas
- Stake optimizado por Kelly Criterion

### 5.4 Múltiples Sharps
- Soporte para Bet365, Betfair como sharps
- Estrategias de cálculo específicas por sharp

---

## 6. Apéndices

### 6.1 Mercados Opuestos

| Mercado | Opuesto(s) |
|---------|------------|
| win1 | win2 |
| over | under |
| ah1 | ah2 |
| odd | even |
| yes | no |
| _1x | _x2, _12 |

### 6.2 Tabla de Cuotas Mínimas (Referencia)

| Cuota Pinnacle | Min Odds Soft |
|----------------|---------------|
| 1.50 | 2.92 |
| 1.80 | 2.20 |
| 2.00 | 1.96 |
| 2.05 | 1.92 |
| 2.50 | 1.64 |
| 3.00 | 1.48 |

### 6.3 Parámetros de Polling Adaptativo

| Escenario | Intervalo | Acción |
|-----------|-----------|--------|
| Normal | 0.5s | Base |
| 1x 429 | 1.0s | Backoff |
| 2x 429 | 2.0s | Backoff |
| 3x 429 | 4.0s | Backoff |
| 4x+ 429 | 5.0s | Máximo |
| Éxito tras error | -1 nivel | Recuperación gradual |