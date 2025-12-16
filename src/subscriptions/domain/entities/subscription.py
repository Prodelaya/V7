"""
Subscription Entity
===================

Representa una suscripción activa de un cliente a un plan.

Atributos:
    - id: UUID único de la suscripción
    - customer_id: FK al cliente
    - plan_id: FK al plan de servicio
    - stripe_subscription_id: ID de la suscripción en Stripe
    - status: Estado (active, canceled, past_due)
    - current_period_start: Inicio del período actual
    - current_period_end: Fin del período actual
    - cancel_at_period_end: Si se cancelará al final del período

TODO: Implementar dataclass o Pydantic model con validaciones
"""

# Placeholder - Implementación pendiente
