"""
SubscriptionRepository
======================

Repositorio para operaciones CRUD de Subscription.

Métodos:
    - get_by_id(subscription_id: UUID) -> Subscription | None
    - get_by_stripe_id(stripe_subscription_id: str) -> Subscription | None
    - get_active_by_customer(customer_id: UUID) -> List[Subscription]
    - create(subscription: Subscription) -> Subscription
    - update(subscription: Subscription) -> Subscription
    - update_status(subscription_id: UUID, status: str) -> Subscription

Dependencias:
    - asyncpg (PostgreSQL)

TODO: Implementar repositorio async con asyncpg
"""

# Placeholder - Implementación pendiente
