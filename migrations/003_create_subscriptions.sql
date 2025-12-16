-- Migration: 003_create_subscriptions
-- Description: Creates the subscriptions table for active customer subscriptions
-- Date: December 2024
-- ADR: ADR-016

-- TODO: Implementar migración

CREATE TABLE IF NOT EXISTS subscriptions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES service_plans(id),
    stripe_subscription_id VARCHAR(255) UNIQUE,
    status VARCHAR(50) NOT NULL,            -- active, canceled, past_due
    current_period_start TIMESTAMPTZ,
    current_period_end TIMESTAMPTZ,
    cancel_at_period_end BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Un cliente solo puede tener una suscripción activa por plan
    UNIQUE(customer_id, plan_id)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_subscriptions_customer ON subscriptions(customer_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_stripe ON subscriptions(stripe_subscription_id);

-- Comentarios
COMMENT ON TABLE subscriptions IS 'Suscripciones activas de clientes a planes';
COMMENT ON COLUMN subscriptions.status IS 'Estado: active, canceled, past_due';
