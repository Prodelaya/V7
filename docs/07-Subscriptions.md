# 🔔 Guía del Sistema de Suscripciones

## 📖 Introducción

Este documento describe el **Sistema de Suscripciones Automatizado** que permite a los clientes suscribirse a canales exclusivos de Telegram para recibir picks. Este sistema es **complementario** al core de envío de picks descrito en los documentos 04-06.

> 📌 **ADR relacionado**: [ADR-016-Subscriptions.md](./ADRs/ADR-016-Subscriptions.md)

---

## 🎯 Decisión de Diseño: Bot-First

> [!IMPORTANT]
> El flujo de suscripción se realiza **exclusivamente a través del Bot de Telegram**, no desde la web.

### ¿Por qué Bot-First?

| Desde Web                                            | Desde Bot Telegram                        |
| ---------------------------------------------------- | ----------------------------------------- |
| ❌ Usuario escribe su @username manualmente           | ✅ Obtenemos `telegram_id` automáticamente |
| ❌ Puede escribirlo mal → problemas de identificación | ✅ Sin errores, ID verificado              |
| ❌ Hay que validar que el usuario de Telegram existe  | ✅ Ya sabemos que existe (nos escribió)    |
| ❌ No podemos notificarle si no nos escribió primero  | ✅ Podemos enviarle mensajes directamente  |

### Rol de cada componente

| Componente       | Rol                                           | ¿Suscripción? |
| ---------------- | --------------------------------------------- | ------------- |
| **Bot Telegram** | Punto de entrada para suscripciones           | ✅ SÍ          |
| **Web**          | Información, FAQ, términos, webhooks          | ❌ NO          |
| **Userbot**      | Crear canales (técnico, invisible al usuario) | -             |

### Flujo simplificado

```
Usuario ──▶ Bot (@RetadorBot) ──▶ /planes ──▶ Selecciona ──▶ Link Stripe
                                                                │
    ┌───────────────────────────────────────────────────────────┘
    │
    ▼
Stripe Checkout (con telegram_id en metadata) ──▶ Webhook ──▶ Provisioning
                                                                │
    ┌───────────────────────────────────────────────────────────┘
    │
    ▼
Bot envía invite link al usuario ──▶ Usuario se une al canal
```

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
│   │   ├── payment_account.py # Cuentas de pago externas
│   │   └── channel.py         # Canal de Telegram creado
│   ├── ports/                 # 🆕 Interfaces (puertos)
│   │   └── payment_gateway.py # Interfaz abstracta multi-gateway
│   └── services/
│       └── provisioning_service.py  # Orquestación de provisioning
│
├── application/               # Capa de aplicación
│   ├── handlers/
│   │   ├── payment_webhook_handler.py  # Handler genérico
│   │   ├── stripe_webhook_adapter.py   # Adaptador Stripe
│   │   └── subscription_handler.py     # Lógica de suscripciones
│   └── dto/
│       └── subscription_dto.py         # DTOs para transferencia
│
└── infrastructure/            # Capa de infraestructura
    ├── payments/              # 🆕 Multi-gateway
    │   ├── gateway_factory.py # Factory para gateways
    │   └── stripe/            # Adaptador Stripe
    │       ├── stripe_gateway.py
    │       └── stripe_config.py
    ├── telegram/
    │   ├── subscription_bot.py    # 🤖 Bot de interacción
    │   ├── userbot_client.py      # 👤 Userbot MTProto
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

Landing page **informativa** con FastAPI + Jinja2.

> [!NOTE]
> La web **NO tiene formulario de suscripción**. Solo proporciona información y un enlace al Bot de Telegram. La suscripción se realiza exclusivamente a través del bot.

### Propósito

- **Información**: Explicar el servicio a visitantes
- **SEO/Marketing**: Página indexable por buscadores
- **Legal**: Términos, privacidad, FAQ
- **Técnico**: Endpoint para webhooks de Stripe

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

| Tabla                 | Descripción                                            |
| --------------------- | ------------------------------------------------------ |
| `customers`           | Clientes suscritos (telegram_id)                       |
| `payment_accounts`    | Cuentas de pago externas por proveedor (multi-gateway) |
| `service_plans`       | Planes disponibles (soft_id, precio)                   |
| `plan_payment_prices` | Precios externos por proveedor (multi-gateway)         |
| `subscriptions`       | Suscripciones activas (estado, período, proveedor)     |
| `telegram_channels`   | Canales creados (channel_id, invite_link)              |

### Migraciones

```
migrations/
├── 001_create_customers.sql
├── 002_create_service_plans.sql
├── 003_create_subscriptions.sql
├── 004_create_telegram_channels.sql
├── 005_create_plan_payment_prices.sql   # Multi-gateway
└── 006_create_payment_accounts.sql      # Multi-gateway
```

---

## 🔌 Extensibilidad: Añadir Nuevos Proveedores de Pago

> [!NOTE]
> La arquitectura está diseñada para soportar múltiples pasarelas de pago (Stripe, PayPal, Cryptomus, etc.) sin modificar el dominio ni la lógica de negocio.

### Arquitectura Multi-Gateway

```
domain/ports/
└── payment_gateway.py      ← Interfaz abstracta (no tocar)

infrastructure/payments/
├── gateway_factory.py      ← Registrar nuevo gateway aquí
├── stripe/                 ← Implementación actual
│   ├── stripe_gateway.py
│   └── stripe_config.py
├── paypal/                 ← FUTURO
│   ├── paypal_gateway.py
│   └── paypal_config.py
└── cryptomus/              ← FUTURO
    ├── cryptomus_gateway.py
    └── cryptomus_config.py
```

### Pasos para Añadir un Nuevo Proveedor

#### 1. Crear subcarpeta del proveedor

```bash
mkdir -p src/subscriptions/infrastructure/payments/paypal
touch src/subscriptions/infrastructure/payments/paypal/__init__.py
```

#### 2. Implementar el Gateway

```python
# paypal_gateway.py
from subscriptions.domain.ports import PaymentGateway, CheckoutSession, PaymentEvent

class PayPalGateway(PaymentGateway):
    async def create_checkout_session(self, plan_id, customer_telegram_id, ...) -> CheckoutSession:
        # Implementar con PayPal REST API
        pass
    
    async def cancel_subscription(self, subscription_id: str) -> bool:
        # Implementar cancelación
        pass
    
    def parse_webhook(self, payload: bytes, signature: str) -> PaymentEvent:
        # Convertir eventos PayPal → PaymentEvent normalizado
        pass
```

#### 3. Crear Adapter de Webhooks

```python
# application/handlers/paypal_webhook_adapter.py
class PayPalWebhookAdapter:
    """Convierte webhooks de PayPal a PaymentEvent."""
    
    EVENT_MAP = {
        "PAYMENT.CAPTURE.COMPLETED": "payment_completed",
        "BILLING.SUBSCRIPTION.CANCELLED": "subscription_cancelled",
    }
```

#### 4. Registrar en el Factory

```python
# gateway_factory.py
from .paypal import PayPalGateway

class GatewayFactory:
    _registry = {
        "stripe": StripeGateway,
        "paypal": PayPalGateway,  # ← Añadir aquí
    }
```

#### 5. Añadir endpoint de webhook

```python
# web/routes/webhooks.py
@router.post("/webhooks/paypal")
async def paypal_webhook(request: Request):
    adapter = PayPalWebhookAdapter()
    event = adapter.parse(await request.body())
    await payment_handler.handle(event)
```

#### 6. Configurar precios en BD

```sql
INSERT INTO plan_payment_prices (plan_id, provider, external_price_id)
VALUES 
  ('uuid-retabet', 'paypal', 'PAYPAL-PLAN-XXX'),
  ('uuid-sportium', 'paypal', 'PAYPAL-PLAN-YYY');
```

### Mapeo de Eventos por Proveedor

| PaymentEvent             | Stripe                          | PayPal                           | Cryptomus        |
| ------------------------ | ------------------------------- | -------------------------------- | ---------------- |
| `payment_completed`      | `checkout.session.completed`    | `PAYMENT.CAPTURE.COMPLETED`      | `payment:paid`   |
| `payment_failed`         | `invoice.payment_failed`        | `PAYMENT.CAPTURE.DENIED`         | `payment:cancel` |
| `subscription_cancelled` | `customer.subscription.deleted` | `BILLING.SUBSCRIPTION.CANCELLED` | N/A              |

### Variables de Entorno por Proveedor

```env
# === STRIPE (actual) ===
STRIPE_SECRET_KEY=sk_xxx
STRIPE_PUBLISHABLE_KEY=pk_xxx
STRIPE_WEBHOOK_SECRET=whsec_xxx

# === PAYPAL (futuro) ===
PAYPAL_CLIENT_ID=xxx
PAYPAL_CLIENT_SECRET=xxx
PAYPAL_WEBHOOK_ID=xxx
PAYPAL_MODE=sandbox  # o 'live'

# === CRYPTOMUS (futuro) ===
CRYPTOMUS_MERCHANT_ID=xxx
CRYPTOMUS_API_KEY=xxx
CRYPTOMUS_WEBHOOK_SECRET=xxx
```

### Lo que NO hay que modificar

| Componente                        | Razón                        |
| --------------------------------- | ---------------------------- |
| `domain/entities/*`               | Agnósticos de proveedor      |
| `domain/ports/payment_gateway.py` | Interfaz estable             |
| `payment_webhook_handler.py`      | Procesa eventos normalizados |
| `provisioning_service.py`         | Solo recibe PaymentEvent     |

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
- [PayPal Subscriptions API](https://developer.paypal.com/docs/subscriptions/)
- [Cryptomus API](https://doc.cryptomus.com/)
- [Telethon Docs](https://docs.telethon.dev/)
- [aiogram Docs](https://docs.aiogram.dev/)

