"""
CustomerRepository
==================

Repositorio para operaciones CRUD de Customer.

Métodos:
    - get_by_telegram_id(telegram_id: int) -> Customer | None
    - get_by_stripe_id(stripe_customer_id: str) -> Customer | None
    - create(customer: Customer) -> Customer
    - update(customer: Customer) -> Customer
    - get_or_create_by_telegram(telegram_id: int, username: str | None) -> Customer

Dependencias:
    - asyncpg (PostgreSQL)

TODO: Implementar repositorio async con asyncpg
"""

# Placeholder - Implementación pendiente
