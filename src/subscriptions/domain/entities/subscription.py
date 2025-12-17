"""
Subscription Entity
===================

Representa una suscripción activa de un cliente a un plan.

Atributos:
    - id: UUID único de la suscripción
    - customer_id: FK al cliente
    - plan_id: FK al plan de servicio
    - external_subscription_id: ID de la suscripción en la pasarela de pago
    - payment_provider: Proveedor de pago (stripe, paypal, cryptomus)
    - status: Estado (active, canceled, past_due)
    - current_period_start: Inicio del período actual
    - current_period_end: Fin del período actual
    - cancel_at_period_end: Si se cancelará al final del período
    - created_at: Fecha de creación
    - updated_at: Fecha de última actualización

Valores de payment_provider:
    - 'stripe': Stripe Billing
    - 'paypal': PayPal Subscriptions (futuro)
    - 'cryptomus': Cryptomus (futuro)

Nota:
    El campo external_subscription_id es genérico y almacena el ID
    de la suscripción en cualquier proveedor. El campo payment_provider
    indica qué proveedor gestiona esta suscripción específica.

TODO: Implementar dataclass o Pydantic model con validaciones
"""

# Placeholder - Implementación pendiente
