"""
PaymentAccount Entity
=====================

Representa una cuenta de pago externa de un cliente en un proveedor específico.

Atributos:
    - id: UUID único de la cuenta
    - customer_id: FK al cliente
    - provider: Proveedor de pago (stripe, paypal, cryptomus)
    - external_customer_id: ID del cliente en el proveedor externo
    - is_active: Si la cuenta está activa
    - created_at: Fecha de creación
    - updated_at: Fecha de última actualización

Relación con Customer:
    Un Customer puede tener múltiples PaymentAccounts (una por proveedor).
    Esto permite que un cliente pague con Stripe Y con PayPal si lo desea.

Ejemplos de external_customer_id:
    - Stripe: 'cus_xxx'
    - PayPal: 'PAYPAL-ACC-xxx'
    - Cryptomus: 'cryptomus_user_xxx'

Propósito:
    Esta entidad desacopla la información del cliente de los proveedores
    de pago específicos. Antes, customer.stripe_customer_id era un campo
    directo. Ahora, los IDs externos se almacenan aquí.

TODO: Implementar dataclass o Pydantic model con validaciones
"""

# Placeholder - Implementación pendiente
