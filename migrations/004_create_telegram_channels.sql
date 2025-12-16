-- Migration: 004_create_telegram_channels
-- Description: Creates the telegram_channels table for subscription channels
-- Date: December 2024
-- ADR: ADR-016

-- TODO: Implementar migración

CREATE TABLE IF NOT EXISTS telegram_channels (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subscription_id UUID UNIQUE REFERENCES subscriptions(id) ON DELETE CASCADE,
    channel_id BIGINT UNIQUE NOT NULL,
    channel_title VARCHAR(255),
    invite_link VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_channels_subscription ON telegram_channels(subscription_id);
CREATE INDEX IF NOT EXISTS idx_channels_active ON telegram_channels(is_active) WHERE is_active = TRUE;

-- Comentarios
COMMENT ON TABLE telegram_channels IS 'Canales de Telegram creados para suscripciones';
COMMENT ON COLUMN telegram_channels.channel_id IS 'ID del canal en Telegram';
COMMENT ON COLUMN telegram_channels.invite_link IS 'Link de invitación al canal';
