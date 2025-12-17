"""
ServicePlan Entity
==================

Representa un plan de servicio (soft) disponible para suscripción.

Atributos:
    - id: UUID único del plan
    - soft_id: Identificador de la soft ('retabet', 'sportium', etc.)
    - name: Nombre del plan
    - description: Descripción del plan
    - price_cents: Precio en céntimos
    - currency: Moneda (EUR por defecto)
    - is_active: Si el plan está activo
    - created_at: Fecha de creación

Relaciones:
    - payment_prices: Diccionario de precios externos por proveedor (1:N)
      Almacenado en tabla plan_payment_prices.
      Ejemplo: {'stripe': 'price_xxx', 'paypal': 'plan_yyy'}

Nota:
    Los IDs de precios en pasarelas de pago externas (stripe_price_id, etc.)
    se almacenan en la tabla plan_payment_prices, no en esta entidad.
    Esto permite configurar precios diferentes por proveedor de pago.

TODO: Implementar dataclass o Pydantic model con validaciones
"""

# Placeholder - Implementación pendiente
