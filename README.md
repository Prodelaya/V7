# 🎯 Retador v2.0

Sistema profesional de detección y distribución de apuestas de valor basadas en arbitraje entre casas de apuestas **sharp** y **soft**, con sistema automatizado de suscripciones.

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-Private-red.svg)
![Status](https://img.shields.io/badge/Status-Active-green.svg)

## 📖 Descripción

**Retador** es una plataforma que:
1. Consume datos de surebets de un proveedor externo
2. Filtra y valida oportunidades de valor según reglas de negocio
3. Distribuye picks a apostadores profesionales vía Telegram
4. Gestiona suscripciones con canales exclusivos por cliente

### Características Principales

- 🔍 **Detección de Value Bets**: Identifica oportunidades donde las softs ofrecen cuotas superiores a Pinnacle
- 📊 **Filtrado Inteligente**: Valida picks con múltiples criterios (cuotas, profit, tiempo, mercados opuestos)
- 🚫 **Deduplicación con Redis**: Previene envío de picks duplicados y rebotes de cuotas
- 📱 **Distribución vía Telegram**: Envío priorizado con rotación de bots para máximo throughput
- ⚡ **Polling Adaptativo**: Ajuste dinámico del intervalo según respuesta de la API
- 💳 **Suscripciones Automatizadas**: Flujo completo con Stripe y canales exclusivos

## 🏗️ Arquitectura

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           RETADOR v2.0                                   │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    CORE (Envío de Picks)                         │   │
│  │                                                                   │   │
│  │   API Externa ──▶ Validación ──▶ Redis ──▶ Telegram (5 Bots)    │   │
│  │  (apostasseguras)   (Chain)     (dedup)    (heap priorizado)    │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │               SUSCRIPCIONES (Gestión de Clientes)                │   │
│  │                                                                   │   │
│  │   Bot Telegram ──▶ Stripe ──▶ Userbot ──▶ Canal Exclusivo       │   │
│  │    (aiogram)      (pagos)   (Telethon)   (por cliente)          │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                        WEB (Landing Page)                        │   │
│  │                                                                   │   │
│  │   FastAPI + Jinja2 ──▶ Webhooks Stripe ──▶ Provisioning         │   │
│  │                                                                   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                          │
├─────────────────────────────────────────────────────────────────────────┤
│   PostgreSQL (suscripciones)  │  Redis (dedup/cache)                    │
└─────────────────────────────────────────────────────────────────────────┘
```

## 📋 Requisitos

- **Python** 3.10+
- **Redis** 6.0+
- **PostgreSQL** 14+ (para suscripciones)
- Conexión a internet estable
- Tokens de Telegram Bot API
- Cuenta de Stripe (para pagos)
- Cuenta de Telegram con API credentials (para userbot)

### Dependencias Principales

```txt
# Core
aiohttp       # Cliente HTTP asíncrono
aiogram       # Framework de Telegram Bot
redis         # Cliente Redis asíncrono
orjson        # Serialización JSON optimizada
pytz          # Gestión de zonas horarias

# Suscripciones
asyncpg       # Driver PostgreSQL asíncrono
stripe        # SDK de Stripe para pagos
telethon      # Cliente MTProto para Telegram (userbot)

# Web
fastapi       # Framework web asíncrono
uvicorn       # Servidor ASGI
jinja2        # Templates HTML
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

# Copiar y configurar variables de entorno
cp .env.example .env
# Editar .env con tus credenciales
```

## ⚙️ Configuración

### Variables de Entorno Core

```env
# API
API_TOKEN=your_api_token
API_BASE_URL=https://api.apostasseguras.com

# Redis
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=your_password

# Telegram (Bots de envío)
TELEGRAM_BOT_TOKENS=token1,token2,token3,token4,token5
```

### Variables de Entorno Suscripciones

```env
# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Userbot (MTProto)
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890
TELEGRAM_USERBOT_SESSION=userbot_session
TELEGRAM_USERBOT_PHONE=+34600000000

# Bot de Suscripción
TELEGRAM_SUBSCRIPTION_BOT_TOKEN=123456:ABC-xxx

# Web
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_BASE_URL=https://retador.es

# PostgreSQL
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=retador
POSTGRES_USER=retador
POSTGRES_PASSWORD=xxx
```

## 📊 Modelo de Negocio

### Estrategia de Valor

El sistema detecta surebets entre **Pinnacle** (sharp) y casas de apuestas soft, apostando solo a la pata de la soft:

| Profit       | Indicador | Nivel de Confianza |
| ------------ | --------- | ------------------ |
| -1% a -0.5%  | 🔴         | Baja               |
| -0.5% a 1.5% | 🟠         | Media-baja         |
| 1.5% a 4%    | 🟡         | Media-alta         |
| > 4%         | 🟢         | Alta               |

### Casas de Apuestas Soportadas

**Sharp (Contrapartida):**
- Pinnacle Sports

**Soft (Objetivo):**
- Retabet, Sportium, Bet365, y otras configurables...

## 📁 Estructura del Proyecto

```
RetadorV7/
├── docs/                          # 📚 Documentación
│   ├── 01-SRS.md                  # Requisitos del sistema
│   ├── 02-PDR.md                  # Diseño del producto
│   ├── 03-ADRs.md                 # Decisiones de arquitectura
│   ├── 04-Structure.md            # Guía de estructura
│   ├── 05-Implementation.md       # Guía de implementación
│   ├── 06-Deployment.md           # Guía de despliegue
│   ├── 07-Subscriptions.md        # Sistema de suscripciones
│   └── ADRs/                      # ADRs detallados
│       └── ADR-016-Subscriptions.md
│
├── src/                           # 🧠 Código fuente
│   ├── domain/                    # Reglas de negocio puras
│   │   ├── value_objects/         # Tipos validados (Odds, Profit...)
│   │   ├── entities/              # Entidades (Pick, Surebet...)
│   │   ├── services/              # Cálculos y lógica
│   │   └── rules/                 # Cadena de validación
│   │
│   ├── application/               # Coordinación
│   │   ├── handlers/              # Orquestación de flujos
│   │   └── dto/                   # Objetos de transferencia
│   │
│   ├── infrastructure/            # Conexiones externas
│   │   ├── api/                   # Cliente API surebets
│   │   ├── repositories/          # Redis, PostgreSQL
│   │   ├── messaging/             # Telegram gateway + pick_router
│   │   └── cache/                 # Cache local
│   │
│   ├── subscriptions/             # 🔔 Módulo de suscripciones
│   │   ├── domain/                # Entities (Customer, Subscription...)
│   │   ├── application/           # Handlers (Stripe, Subscription)
│   │   └── infrastructure/        # Stripe, Telegram, Repositories
│   │
│   ├── web/                       # 🌐 Landing page + Webhooks
│   │   ├── routes/                # Páginas y webhooks
│   │   ├── templates/             # Templates Jinja2
│   │   └── static/                # CSS, imágenes
│   │
│   ├── config/                    # Configuración
│   └── shared/                    # Utilidades compartidas
│
├── migrations/                    # 🗄️ Migraciones SQL
│   ├── 001_create_customers.sql
│   ├── 002_create_service_plans.sql
│   ├── 003_create_subscriptions.sql
│   └── 004_create_telegram_channels.sql
│
├── tests/                         # 🧪 Tests
│   ├── unit/                      # Tests unitarios
│   └── integration/               # Tests de integración
│
├── legacy/                        # 🏚️ Código V6 (referencia)
│   └── RetadorV6.py
│
├── scripts/                       # 📜 Scripts de arranque
├── requirements.txt
├── pyproject.toml
└── .env.example
```

## 📈 Métricas de Rendimiento

| Métrica                | Objetivo                    |
| ---------------------- | --------------------------- |
| Latencia API→Telegram  | < 500ms (objetivo: < 100ms) |
| Throughput             | > 500 picks/hora            |
| Tiempo respuesta Redis | < 10ms                      |
| Uptime                 | 99.5%                       |

## 📚 Documentación

La documentación completa se encuentra en `/docs`:

| Documento                                          | Descripción                    |
| -------------------------------------------------- | ------------------------------ |
| [01-SRS.md](./docs/01-SRS.md)                      | Especificación de requisitos   |
| [02-PDR.md](./docs/02-PDR.md)                      | Diseño del producto            |
| [03-ADRs.md](./docs/03-ADRs.md)                    | Decisiones de arquitectura     |
| [04-Structure.md](./docs/04-Structure.md)          | Guía de estructura de carpetas |
| [05-Implementation.md](./docs/05-Implemetation.md) | Guía de implementación         |
| [06-Deployment.md](./docs/06-Deployment.md)        | Guía de despliegue             |
| [07-Subscriptions.md](./docs/07-Subscriptions.md)  | Sistema de suscripciones       |

## 🔒 Seguridad

- Tokens almacenados en variables de entorno
- Conexión Redis con autenticación
- Verificación de firma en webhooks de Stripe
- Cuenta de userbot dedicada (no la personal)
- Logs estructurados con filtrado de información sensible

## 📝 Licencia

Este proyecto es **privado** y su uso está restringido.

---

<p align="center">
  <strong>Retador v2.0</strong> - Sistema de Value Betting Profesional
  <br>
  Diciembre 2024
</p>
