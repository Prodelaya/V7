-- Migration: 005_create_plan_payment_prices
-- Description: Creates mapping table for plan prices in external payment providers
-- Date: December 2025
-- ADR: ADR-016

-- TODO: Implementar migración

-- Esta tabla mapea planes a sus IDs de precio en diferentes pasarelas de pago.
-- Permite configurar precios diferentes por proveedor (Stripe, PayPal, etc.)

CREATE TABLE IF NOT EXISTS plan_payment_prices (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    plan_id UUID NOT NULL REFERENCES service_plans(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,          -- stripe, paypal, cryptomus
    external_price_id VARCHAR(255) NOT NULL, -- price_xxx (Stripe), plan_xxx (PayPal)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Un plan solo puede tener un precio activo por proveedor
    UNIQUE(plan_id, provider)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_plan_prices_plan ON plan_payment_prices(plan_id);
CREATE INDEX IF NOT EXISTS idx_plan_prices_provider ON plan_payment_prices(provider);
CREATE INDEX IF NOT EXISTS idx_plan_prices_active ON plan_payment_prices(is_active) WHERE is_active = TRUE;

-- Comentarios
COMMENT ON TABLE plan_payment_prices IS 'Mapeo de planes a precios en pasarelas de pago';
COMMENT ON COLUMN plan_payment_prices.provider IS 'Proveedor: stripe, paypal, cryptomus';
COMMENT ON COLUMN plan_payment_prices.external_price_id IS 'ID del precio en la pasarela externa';

-- Ejemplos de uso:
-- INSERT INTO plan_payment_prices (plan_id, provider, external_price_id)
-- VALUES 
--   ('uuid-del-plan', 'stripe', 'price_xxx'),
--   ('uuid-del-plan', 'paypal', 'plan_yyy');
