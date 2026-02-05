# Payments Infrastructure
#
# Arquitectura multi-gateway para pasarelas de pago.
#
# Componentes:
#   - GatewayFactory: Factory para instanciar gateways
#   - stripe/: Adaptador para Stripe
#   - paypal/: Adaptador para PayPal (futuro)
#   - cryptomus/: Adaptador para Cryptomus (futuro)
#
# Uso:
#   from subscriptions.infrastructure.payments import GatewayFactory
#   gateway = GatewayFactory.create('stripe')

# Imports restaurados cuando Stripe + Factory se implementan (ver Fase 3 en 07.1-Subscriptions-roadmap.md)
#
# from .gateway_factory import GatewayFactory
# from .stripe import StripeConfig, StripeGateway
#
# __all__ = ["GatewayFactory", "StripeGateway", "StripeConfig"]
