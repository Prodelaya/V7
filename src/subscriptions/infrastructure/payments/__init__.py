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

from .gateway_factory import GatewayFactory
from .stripe import StripeConfig, StripeGateway

__all__ = ["GatewayFactory", "StripeGateway", "StripeConfig"]
