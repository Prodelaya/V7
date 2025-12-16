"""
PickRouter
==========

Enruta picks a los canales de clientes suscritos.

Responsabilidades:
    - Obtener canales activos por soft_id
    - Enviar pick a todos los canales correspondientes
    - Usar pool de bots de envío para rate limiting

Integración:
    - Se integra con TelegramGateway existente
    - Usa ChannelRepository para obtener canales activos

Flujo:
    1. Recibe pick procesado con soft_id
    2. Consulta canales activos para ese soft_id
    3. Envía mensaje a cada canal usando bot pool

TODO: Implementar clase con lógica de routing
"""

# Placeholder - Implementación pendiente
