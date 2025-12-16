# 🔔 Guía del Sistema de Suscripciones

## 📖 Introducción

Este documento describe el **Sistema de Suscripciones Automatizado** que permite a los clientes suscribirse a canales exclusivos de Telegram para recibir picks. Este sistema es **complementario** al core de envío de picks descrito en los documentos 04-06.

> 📌 **ADR relacionado**: [ADR-016-Subscriptions.md](./ADRs/ADR-016-Subscriptions.md)

---

## 🏗️ Arquitectura General

```
┌─────────────────────────────────────────────────────────────────────┐
│                     SISTEMA DE SUSCRIPCIONES                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────┐    ┌────────────────┐    ┌────────────────────┐ │
│  │  🌐 WEB        │    │  🤖 BOT        │    │  👤 USERBOT        │ │
│  │  (FastAPI)     │    │  (aiogram)     │    │  (Telethon)        │ │
│  │                │    │                │    │                    │ │
│  │  • Landing     │    │  • /start      │    │  • Crear canales   │ │
│  │  • FAQ         │    │  • /planes     │    │  • Añadir admins   │ │
│  │  • Términos    │    │  • /estado     │    │  • Gen. invites    │ │
│  │  • Webhooks    │    │  • /cancelar   │    │                    │ │
│  │    Stripe      │    │                │    │                    │ │
│  └────────────────┘    └────────────────┘    └────────────────────┘ │
│           │                    │                      │              │
│           └────────────────────┼──────────────────────┘              │
│                                │                                     │
│                    ┌───────────▼───────────┐                        │
│                    │   📦 SUBSCRIPTIONS    │                        │
│                    │      MODULE           │                        │
│                    │                       │                        │
│                    │  • Domain (Entities)  │                        │
│                    │  • Application        │                        │
│                    │  • Infrastructure     │                        │
│                    └───────────────────────┘                        │
│                                │                                     │
│                    ┌───────────▼───────────┐                        │
│                    │   🐘 PostgreSQL       │                        │
│                    │   💳 Stripe           │                        │
│                    └───────────────────────┘                        │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 📁 Estructura de Carpetas

### `src/subscriptions/` - Módulo de Suscripciones

```
src/subscriptions/
├── __init__.py
├── domain/                    # Capa de dominio
│   ├── entities/              # Entidades de negocio
│   │   ├── customer.py        # Cliente suscrito
│   │   ├── service_plan.py    # Plan de suscripción (soft)
│   │   ├── subscription.py    # Suscripción activa
│   │   └── channel.py         # Canal de Telegram creado
│   └── services/
│       └── provisioning_service.py  # Orquestación de provisioning
│
├── application/               # Capa de aplicación
│   ├── handlers/
│   │   ├── stripe_webhook_handler.py   # Procesa webhooks de Stripe
│   │   └── subscription_handler.py     # Lógica de suscripciones
│   └── dto/
│       └── subscription_dto.py         # DTOs para transferencia
│
└── infrastructure/            # Capa de infraestructura
    ├── payments/
    │   ├── stripe_client.py   # Cliente SDK de Stripe
    │   └── stripe_config.py   # Config de productos/precios
    ├── telegram/
    │   ├── subscription_bot.py    # 🤖 Bot de interacción con usuario
    │   ├── userbot_client.py      # 👤 Userbot MTProto (Telethon)
    │   └── channel_provisioner.py # Crear y configurar canales
    └── repositories/
        ├── customer_repository.py      # CRUD clientes
        ├── subscription_repository.py  # CRUD suscripciones
        └── channel_repository.py       # CRUD canales
```

---

### `src/web/` - Módulo Web

```
src/web/
├── __init__.py
├── app.py                 # Aplicación FastAPI
├── routes/
│   ├── pages.py           # Rutas de páginas estáticas
│   └── webhooks.py        # Endpoint de webhooks Stripe
├── templates/             # Templates Jinja2
│   ├── base.html          # Template base
│   ├── index.html         # Landing page
│   ├── faq.html           # Preguntas frecuentes
│   ├── terms.html         # Términos y condiciones
│   └── privacy.html       # Política de privacidad
└── static/
    ├── css/styles.css     # Estilos CSS
    └── img/               # Imágenes
```

---

## 🤖 Bot de Suscripción (`subscription_bot.py`)

Este es el bot con el que el usuario interactúa directamente por Telegram.

### Comandos

| Comando     | Descripción                                              |
| ----------- | -------------------------------------------------------- |
| `/start`    | Inicia el flujo de suscripción, muestra bienvenida       |
| `/planes`   | Muestra casas de apuestas disponibles con inline buttons |
| `/estado`   | Consulta el estado de la suscripción actual              |
| `/cancelar` | Inicia el proceso de cancelación                         |

### Flujo de Interacción

```
Usuario: /start
    └─► Bot: "¡Bienvenido! Aquí podrás suscribirte a alertas de apuestas..."
        └─► [Ver Planes] (inline button)

Usuario: Click en [Ver Planes]
    └─► Bot: "Elige una casa de apuestas:"
        └─► [🎰 Retabet] [⚽ Sportium] [🎲 Bet365] ... (inline buttons)

Usuario: Click en [Retabet]
    └─► Bot: "Plan Retabet - 29.99€/mes"
              "Recibe alertas de valor en tiempo real"
        └─► [💳 Suscribirse] [⬅️ Volver] (inline buttons)

Usuario: Click en [Suscribirse]
    └─► Bot: "Pulsa aquí para completar el pago:"
              [Ir a pago seguro] (link a Stripe Checkout)

[Usuario paga en Stripe Checkout]
    └─► Webhook → Provisioning → Canal creado

Bot: "✅ ¡Pago recibido! Tu canal exclusivo está listo:"
     "🔗 [Unirte al canal Retabet]"
```

### Callbacks (Inline Buttons)

| Callback Data           | Acción                    |
| ----------------------- | ------------------------- |
| `plan_list`             | Mostrar lista de planes   |
| `plan_select_{soft_id}` | Mostrar detalles del plan |
| `subscribe_{soft_id}`   | Generar link de checkout  |
| `back_to_plans`         | Volver a lista de planes  |
| `confirm_cancel`        | Confirmar cancelación     |

---

## 👤 Userbot (`userbot_client.py`)

El userbot usa **Telethon (MTProto)** porque los bots normales no pueden crear canales.

### ¿Por qué un Userbot?

| Operación            | Bot API               | Userbot (MTProto) |
| -------------------- | --------------------- | ----------------- |
| Crear canal          | ❌ No puede            | ✅ Puede           |
| Añadir admin a canal | ⚠️ Solo si ya es admin | ✅ Puede           |
| Generar invite link  | ⚠️ Solo si ya es admin | ✅ Puede           |
| Enviar mensajes      | ✅ Puede               | ✅ Puede           |

### Operaciones del Userbot

1. **Crear canal**: Con título personalizado (ej: "Retador - Retabet - @usuario")
2. **Añadir bots de envío**: Como administradores del canal
3. **Generar invite link**: Link único para el cliente
4. **Configurar permisos**: Solo admins pueden postear

### Configuración Requerida

```env
# Credenciales de my.telegram.org
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=abcdef1234567890

# Sesión persistente
TELEGRAM_USERBOT_SESSION=userbot_session

# Teléfono de la cuenta dedicada
TELEGRAM_USERBOT_PHONE=+34600000000
```

---

## 🌐 Web (`src/web/`)

Landing page minimalista con FastAPI + Jinja2.

### Endpoints

| Ruta               | Método | Descripción               |
| ------------------ | ------ | ------------------------- |
| `/`                | GET    | Landing page              |
| `/faq`             | GET    | Preguntas frecuentes      |
| `/terms`           | GET    | Términos y condiciones    |
| `/privacy`         | GET    | Política de privacidad    |
| `/webhooks/stripe` | POST   | Recibe webhooks de Stripe |

### Webhook de Stripe

El endpoint `/webhooks/stripe` recibe eventos de Stripe y dispara el provisioning:

```python
# Eventos procesados:
checkout.session.completed  → Provisioning inicial
invoice.paid                → Renovación OK
invoice.payment_failed      → Notificar fallo
customer.subscription.deleted → Desactivar canal
```

---

## 🔄 Flujo Completo de Provisioning

```
1. Cliente envía /start al bot
2. Bot muestra planes con inline buttons
3. Cliente selecciona plan (ej: Retabet)
4. Bot crea Stripe Checkout Session
5. Bot envía link de pago al cliente
6. Cliente paga en Stripe Checkout
7. Stripe envía webhook: checkout.session.completed
8. Webhook handler:
   a. Extrae telegram_id y plan_id de metadata
   b. Crea/actualiza Customer en BD
   c. Crea Subscription en BD
   d. Llama a ProvisioningService
9. ProvisioningService:
   a. Userbot crea canal
   b. Userbot añade bots de envío como admin
   c. Userbot genera invite link
   d. Guarda TelegramChannel en BD
   e. Bot notifica al cliente con invite link
10. Cliente se une al canal
11. Core de Retador enruta picks al canal (via pick_router.py)
```

---

## 🗄️ Modelo de Datos

### Tablas PostgreSQL

| Tabla               | Descripción                                           |
| ------------------- | ----------------------------------------------------- |
| `customers`         | Clientes suscritos (telegram_id, stripe_customer_id)  |
| `service_plans`     | Planes disponibles (soft_id, precio, stripe_price_id) |
| `subscriptions`     | Suscripciones activas (estado, período)               |
| `telegram_channels` | Canales creados (channel_id, invite_link)             |

### Migraciones

```
migrations/
├── 001_create_customers.sql
├── 002_create_service_plans.sql
├── 003_create_subscriptions.sql
└── 004_create_telegram_channels.sql
```

---

## 🔗 Integración con Core

El módulo de suscripciones se conecta con el core de envío de picks a través de:

```
src/infrastructure/messaging/pick_router.py
```

Este archivo consulta los canales activos por `soft_id` y enruta los picks a los canales correspondientes.

```
Core (telegram_gateway.py)
    └─► pick_router.py
        └─► Consulta canales activos para la soft
            └─► Envía pick a cada canal del cliente
```

---

## ⚙️ Variables de Entorno

```env
# Stripe
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# Userbot
TELEGRAM_API_ID=xxx
TELEGRAM_API_HASH=xxx
TELEGRAM_USERBOT_SESSION=xxx
TELEGRAM_USERBOT_PHONE=xxx

# Bot de Suscripción
TELEGRAM_SUBSCRIPTION_BOT_TOKEN=xxx

# Web
WEB_HOST=0.0.0.0
WEB_PORT=8000
WEB_BASE_URL=https://retador.es
```

---

## 📚 Referencias

- [ADR-016: Sistema de Suscripciones Automatizado](./ADRs/ADR-016-Subscriptions.md)
- [05-Implementation.md](./05-Implemetation.md) - Core de picks
- [Stripe Billing Docs](https://stripe.com/docs/billing)
- [Telethon Docs](https://docs.telethon.dev/)
- [aiogram Docs](https://docs.aiogram.dev/)
