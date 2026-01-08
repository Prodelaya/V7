"""
Test PaymentGateway Port
========================

Tests unitarios para la interfaz abstracta PaymentGateway.

Estos tests verifican el contrato de la interfaz sin dependencias
de implementaciones concretas (Stripe, PayPal, etc.).

Casos de test:
    - test_checkout_session_dto_creation: DTO CheckoutSession válido
    - test_payment_event_dto_creation: DTO PaymentEvent válido
    - test_gateway_interface_is_abstract: No se puede instanciar directamente

Implementaciones testeables via mocks:
    - MockPaymentGateway para tests unitarios del dominio
    - StripeGateway, PayPalGateway, etc. en tests de integración

TODO: Implementar tests con pytest y mocks
"""


# Placeholder - Tests pendientes de implementación

class TestPaymentGatewayPort:
    """Tests para la interfaz PaymentGateway."""

    def test_placeholder(self):
        """Placeholder test - eliminar al implementar."""
        assert True


class TestCheckoutSessionDTO:
    """Tests para el DTO CheckoutSession."""

    def test_placeholder(self):
        """Placeholder test - eliminar al implementar."""
        assert True


class TestPaymentEventDTO:
    """Tests para el DTO PaymentEvent."""

    def test_placeholder(self):
        """Placeholder test - eliminar al implementar."""
        assert True
