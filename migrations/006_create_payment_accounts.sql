-- Migration: 006_create_payment_accounts
-- Description: Creates table for external payment provider customer accounts
-- Date: December 2025
-- ADR: ADR-016

-- TODO: Implementar migración

-- Esta tabla almacena las cuentas de clientes en diferentes pasarelas de pago.
-- Permite que un cliente tenga cuentas en múltiples proveedores (Stripe Y PayPal).

CREATE TABLE IF NOT EXISTS payment_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,              -- stripe, paypal, cryptomus
    external_customer_id VARCHAR(255) NOT NULL, -- cus_xxx (Stripe), ACC-xxx (PayPal)
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Un cliente solo puede tener una cuenta activa por proveedor
    UNIQUE(customer_id, provider)
);

-- Índices
CREATE INDEX IF NOT EXISTS idx_payment_accounts_customer ON payment_accounts(customer_id);
CREATE INDEX IF NOT EXISTS idx_payment_accounts_provider ON payment_accounts(provider);
CREATE INDEX IF NOT EXISTS idx_payment_accounts_external ON payment_accounts(external_customer_id);

-- Comentarios
COMMENT ON TABLE payment_accounts IS 'Cuentas de clientes en pasarelas de pago externas';
COMMENT ON COLUMN payment_accounts.provider IS 'Proveedor: stripe, paypal, cryptomus';
COMMENT ON COLUMN payment_accounts.external_customer_id IS 'ID del cliente en la pasarela externa';

-- Ejemplos de uso:
-- INSERT INTO payment_accounts (customer_id, provider, external_customer_id)
-- VALUES 
--   ('uuid-del-customer', 'stripe', 'cus_xxx'),
--   ('uuid-del-customer', 'paypal', 'PAYPAL-ACC-xxx');
