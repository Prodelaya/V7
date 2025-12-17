"""
StripeGateway
=============

Implementación de PaymentGateway para Stripe.

Hereda de:
    PaymentGateway (domain/ports/payment_gateway.py)

Funcionalidades:
    - create_checkout_session(): Crear sesión de Stripe Checkout
    - cancel_subscription(): Cancelar suscripción en Stripe Billing
    - parse_webhook(): Parsear webhook de Stripe a PaymentEvent normalizado
    - verify_webhook_signature(): Verificar firma HMAC del webhook

Eventos Stripe → PaymentEvent:
    - checkout.session.completed → payment_completed
    - invoice.paid → payment_completed
    - invoice.payment_failed → payment_failed
    - customer.subscription.deleted → subscription_cancelled
    - customer.subscription.updated → subscription_updated

Dependencias:
    - stripe SDK (pip install stripe)
    - StripeConfig para credenciales

Configuración requerida:
    - STRIPE_SECRET_KEY
    - STRIPE_WEBHOOK_SECRET

Uso:
    Se instancia via GatewayFactory, nunca directamente desde el dominio.

TODO: Implementar clase que herede de PaymentGateway ABC
"""

# Placeholder - Implementación pendiente
