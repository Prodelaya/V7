"""
GatewayFactory
==============

Factory para instanciar el PaymentGateway apropiado según el proveedor.

Proveedores soportados:
    - 'stripe': StripeGateway (implementado)
    - 'paypal': PayPalGateway (futuro)
    - 'cryptomus': CryptomusGateway (futuro)

Uso:
    gateway = GatewayFactory.create('stripe')
    session = await gateway.create_checkout_session(...)

Patrón:
    Factory Method - Permite añadir nuevos gateways sin modificar código cliente.

Configuración:
    Cada gateway requiere sus propias variables de entorno.
    El factory carga la configuración apropiada automáticamente.

Extensibilidad:
    Para añadir un nuevo gateway:
    1. Crear subcarpeta payments/nuevo_gateway/
    2. Implementar NuevoGateway(PaymentGateway)
    3. Registrar en GatewayFactory._registry

TODO: Implementar clase factory con registry de gateways
"""

# Placeholder - Implementación pendiente
