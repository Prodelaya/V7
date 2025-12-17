"""
StripeConfig
============

Configuración de productos y precios de Stripe.

Mapeo de planes a price_ids:
    - STRIPE_PRICE_RETABET
    - STRIPE_PRICE_SPORTIUM
    - (más softs según se añadan)

Variables de entorno:
    - STRIPE_SECRET_KEY
    - STRIPE_PUBLISHABLE_KEY
    - STRIPE_WEBHOOK_SECRET

Nota:
    Los price_ids también se almacenan en la tabla plan_payment_prices
    para permitir gestión dinámica. Esta config es para valores por defecto.

TODO: Implementar clase de configuración con Pydantic Settings
"""

# Placeholder - Implementación pendiente
