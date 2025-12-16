"""
ProvisioningService
===================

Orquesta el proceso completo de provisioning de una suscripción:

1. Recibe evento de pago completado
2. Crea/actualiza cliente en BD
3. Crea suscripción en BD
4. Llama a ChannelProvisioner para crear canal
5. Notifica al cliente con el link de invitación

Dependencias:
    - CustomerRepository
    - SubscriptionRepository
    - ChannelRepository
    - ChannelProvisioner (Userbot)
    - NotificationService (Bot de suscripción)

Flujo:
    checkout.session.completed → provision_subscription() → canal creado + notificación

TODO: Implementar clase con inyección de dependencias
"""

# Placeholder - Implementación pendiente
