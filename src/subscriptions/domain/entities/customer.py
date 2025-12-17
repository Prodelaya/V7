"""
Customer Entity
===============

Representa un cliente del sistema de suscripciones.

Atributos:
    - id: UUID único del cliente
    - telegram_id: ID de Telegram del usuario
    - telegram_username: Username de Telegram (opcional)
    - email: Email del cliente (opcional)
    - created_at: Fecha de creación
    - updated_at: Fecha de última actualización

Relaciones:
    - payment_accounts: Lista de cuentas de pago externas (1:N)
      Ver PaymentAccount para IDs de proveedores (Stripe, PayPal, etc.)
    - subscriptions: Lista de suscripciones activas (1:N)

Nota:
    Los IDs de clientes en pasarelas de pago externas (stripe_customer_id,
    paypal_account_id, etc.) se almacenan en la entidad PaymentAccount,
    no directamente en Customer. Esto permite soporte multi-gateway.

TODO: Implementar dataclass o Pydantic model con validaciones
"""

# Placeholder - Implementación pendiente
