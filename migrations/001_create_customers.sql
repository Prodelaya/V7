-- Migration: 001_create_customers
-- Description: Creates the customers table for subscription system
-- Date: December 2025
-- ADR: ADR-016

-- TODO: Implementar migración

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    email VARCHAR(255),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_customers_telegram ON customers(telegram_id);

-- Comentarios
COMMENT ON TABLE customers IS 'Clientes del sistema de suscripciones';
COMMENT ON COLUMN customers.telegram_id IS 'ID único del usuario en Telegram';

-- NOTA: Los IDs de clientes en pasarelas de pago externas se almacenan
-- en la tabla payment_accounts, no aquí. Esto permite soporte multi-gateway.
-- Ver migration 006_create_payment_accounts.sql
