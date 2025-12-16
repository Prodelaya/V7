-- Migration: 001_create_customers
-- Description: Creates the customers table for subscription system
-- Date: December 2024
-- ADR: ADR-016

-- TODO: Implementar migración

CREATE TABLE IF NOT EXISTS customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT UNIQUE NOT NULL,
    telegram_username VARCHAR(255),
    email VARCHAR(255),
    stripe_customer_id VARCHAR(255) UNIQUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_customers_telegram ON customers(telegram_id);
CREATE INDEX IF NOT EXISTS idx_customers_stripe ON customers(stripe_customer_id);

-- Comentarios
COMMENT ON TABLE customers IS 'Clientes del sistema de suscripciones';
COMMENT ON COLUMN customers.telegram_id IS 'ID único del usuario en Telegram';
COMMENT ON COLUMN customers.stripe_customer_id IS 'ID del cliente en Stripe para pagos';
