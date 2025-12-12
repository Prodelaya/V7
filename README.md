# 🎯 Retador v2.0

Sistema profesional de detección y distribución de apuestas de valor basadas en arbitraje entre casas de apuestas **sharp** y **soft**.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-Private-red.svg)
![Status](https://img.shields.io/badge/Status-Active-green.svg)

## 📖 Descripción

**Retador** es una plataforma que consume datos de surebets de un proveedor externo, filtra y valida oportunidades de valor según reglas de negocio específicas, y distribuye picks a apostadores profesionales vía Telegram.

### Características Principales

- 🔍 **Detección de Value Bets**: Identifica oportunidades donde las casas de apuestas soft ofrecen cuotas superiores a las eficientes de Pinnacle
- 📊 **Filtrado Inteligente**: Valida picks con múltiples criterios (cuotas, profit, tiempo, mercados opuestos)
- 🚫 **Deduplicación con Redis**: Previene envío de picks duplicados y rebotes de cuotas
- 📱 **Distribución vía Telegram**: Envío priorizado con rotación de bots para máximo throughput
- ⚡ **Polling Adaptativo**: Ajuste dinámico del intervalo según respuesta de la API

## 🏗️ Arquitectura

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│   API Externa   │────▶│     Retador      │────▶│    Telegram     │
│ (apostasseguras)│     │                  │     │    (5 Bots)     │
└─────────────────┘     │  ┌────────────┐  │     └─────────────────┘
                        │  │   Redis    │  │
                        │  │(dedup/TTL) │  │
                        │  └────────────┘  │
                        └──────────────────┘
```

## 📋 Requisitos

- **Python** 3.10+
- **Redis** 6.0+
- Conexión a internet estable
- Tokens de Telegram Bot API

### Dependencias Principales

```txt
aiohttp       # Cliente HTTP asíncrono
aiogram       # Framework de Telegram Bot
asyncpg       # Driver PostgreSQL asíncrono
redis         # Cliente Redis asíncrono
orjson        # Serialización JSON optimizada
pytz          # Gestión de zonas horarias
```

## 🚀 Instalación

```bash
# Clonar el repositorio
git clone <repository-url>
cd RetadorV7

# Crear entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

## ⚙️ Configuración

Las configuraciones principales se encuentran en la clase `BotConfig`:

| Parámetro | Descripción | Valor por defecto |
|-----------|-------------|-------------------|
| `MIN_ODDS` | Cuota mínima aceptable | 1.10 |
| `MAX_ODDS` | Cuota máxima aceptable | 9.99 |
| `REQUEST_RATE_LIMIT` | Peticiones/segundo a la API | 2 |
| `CACHE_TTL` | Tiempo de vida del caché (segundos) | 10 |
| `CONCURRENT_PICKS` | Procesamiento paralelo de picks | 250 |

### Variables de Entorno

```env
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password
API_TOKEN=your_api_token
TELEGRAM_BOT_TOKENS=token1,token2,token3
```

## 📊 Modelo de Negocio

### Estrategia de Valor

El sistema detecta surebets entre **Pinnacle** (sharp) y casas de apuestas soft, apostando solo a la pata de la soft:

| Profit | Indicador | Nivel de Confianza |
|--------|-----------|-------------------|
| -1% a -0.5% | 🔴 | Baja |
| -0.5% a 1.5% | 🟠 | Media-baja |
| 1.5% a 4% | 🟡 | Media-alta |
| > 4% | 🟢 | Alta |

### Casas de Apuestas Soportadas

**Sharp (Contrapartida):**
- Pinnacle Sports

**Soft (Objetivo):**
- Retabet
- YaassCasino
- Y otras configurables...

## 📁 Estructura del Proyecto

```
RetadorV7/
├── docs/
│   ├── 01-SRS.md        # Especificación de requisitos
│   ├── 02-PDR.md        # Documento de diseño
│   └── 03-ADRs.md       # Decisiones de arquitectura
├── legacy/
│   └── RetadorV6.py     # Versión anterior del sistema
├── README.md
└── ...
```

## 📈 Métricas de Rendimiento

| Métrica | Objetivo |
|---------|----------|
| Latencia API→Telegram | < 500ms (objetivo: < 100ms) |
| Throughput | > 500 picks/hora |
| Tiempo respuesta Redis | < 10ms |
| Uptime | 99.5% |

## 📚 Documentación

La documentación completa del proyecto se encuentra en el directorio `/docs`:

- **[SRS](./docs/01-SRS.md)**: Especificación de requisitos de software
- **[PDR](./docs/02-PDR.md)**: Documento de diseño del producto
- **[ADRs](./docs/03-ADRs.md)**: Registros de decisiones de arquitectura

## 🔒 Seguridad

- Tokens almacenados en variables de entorno
- Conexión Redis con autenticación
- Sin exposición de endpoints públicos
- Logs estructurados con filtrado de información sensible

## 📝 Licencia

Este proyecto es **privado** y su uso está restringido.

---

<p align="center">
  <strong>Retador v2.0</strong> - Sistema de Value Betting Profesional
  <br>
  Diciembre 2024
</p>
