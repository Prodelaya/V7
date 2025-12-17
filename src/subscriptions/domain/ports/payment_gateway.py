"""
PaymentGateway Port
===================

Interfaz abstracta para pasarelas de pago. Define el contrato que deben
implementar todos los adaptadores de pago (Stripe, PayPal, Cryptomus, etc.).

Componentes:
    - CheckoutSession: DTO para sesiones de checkout
    - PaymentEvent: DTO para eventos de pago normalizados
    - PaymentGateway: Interfaz abstracta (ABC)

Tipos de eventos soportados:
    - payment_completed: Pago inicial o renovación exitosa
    - payment_failed: Fallo de pago
    - subscription_cancelled: Cancelación de suscripción
    - subscription_updated: Cambios en suscripción

Implementaciones disponibles:
    - StripeGateway (infrastructure/payments/stripe/)
    - PayPalGateway (futuro)
    - CryptomusGateway (futuro)

Uso:
    Las implementaciones concretas se obtienen via GatewayFactory.
    El dominio solo conoce esta interfaz, nunca las implementaciones.

Principio:
    Dependency Inversion - El dominio define el puerto (interfaz),
    la infraestructura provee los adaptadores (implementaciones).

TODO: Implementar ABC con métodos abstractos cuando se implemente Stripe
"""

# Placeholder - Implementación pendiente
# from abc import ABC, abstractmethod
# from dataclasses import dataclass
# from typing import Optional
