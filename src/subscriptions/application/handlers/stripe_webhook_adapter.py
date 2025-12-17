"""
StripeWebhookAdapter
====================

Adaptador que convierte webhooks de Stripe en PaymentEvent normalizados.

Responsabilidades:
    1. Verificar firma del webhook (STRIPE_WEBHOOK_SECRET)
    2. Parsear payload JSON de Stripe
    3. Convertir evento Stripe → PaymentEvent normalizado
    4. Delegar al PaymentWebhookHandler genérico

Mapeo de eventos:
    Stripe Event                    → PaymentEvent.event_type
    ─────────────────────────────────────────────────────────
    checkout.session.completed      → payment_completed
    invoice.paid                    → payment_completed
    invoice.payment_failed          → payment_failed
    customer.subscription.deleted   → subscription_cancelled
    customer.subscription.updated   → subscription_updated

Seguridad:
    - Verifica firma HMAC con STRIPE_WEBHOOK_SECRET
    - Rechaza webhooks con firma inválida

Uso:
    Expuesto como endpoint POST /webhooks/stripe en web/routes/webhooks.py

Dependencias:
    - stripe SDK para verificar firma
    - PaymentWebhookHandler para procesar evento normalizado

TODO: Implementar adapter con verificación de firma y mapeo de eventos
"""

# Placeholder - Implementación pendiente
