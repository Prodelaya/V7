-- Migration: 002_create_service_plans
-- Description: Creates the service_plans table for available subscription plans
-- Date: December 2024
-- ADR: ADR-016

-- TODO: Implementar migración

CREATE TABLE IF NOT EXISTS service_plans (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    soft_id VARCHAR(50) UNIQUE NOT NULL,    -- 'retabet', 'sportium', etc.
    name VARCHAR(100) NOT NULL,
    description TEXT,
    price_cents INTEGER NOT NULL,
    currency VARCHAR(3) DEFAULT 'EUR',
    stripe_price_id VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Comentarios
COMMENT ON TABLE service_plans IS 'Planes de suscripción disponibles (uno por soft)';
COMMENT ON COLUMN service_plans.soft_id IS 'Identificador de la soft (retabet, sportium, etc.)';
COMMENT ON COLUMN service_plans.stripe_price_id IS 'ID del precio en Stripe';
