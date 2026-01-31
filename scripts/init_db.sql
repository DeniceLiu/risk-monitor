-- ============================================
-- Risk Monitor Database Schema
-- Phase 1: Infrastructure Setup
-- ============================================

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================
-- INSTRUMENTS TABLE (Parent)
-- ============================================
CREATE TABLE instruments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    instrument_type VARCHAR(10) NOT NULL CHECK (instrument_type IN ('BOND', 'SWAP')),
    notional DECIMAL(18, 2) NOT NULL,
    currency VARCHAR(3) NOT NULL DEFAULT 'USD',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Index for common queries
CREATE INDEX idx_instruments_type ON instruments(instrument_type);
CREATE INDEX idx_instruments_created_at ON instruments(created_at);

-- ============================================
-- BONDS TABLE (Child)
-- ============================================
CREATE TABLE bonds (
    instrument_id UUID PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    isin VARCHAR(12) UNIQUE NOT NULL,
    coupon_rate DECIMAL(8, 6) NOT NULL,
    maturity_date DATE NOT NULL,
    issue_date DATE,
    payment_frequency VARCHAR(20) NOT NULL DEFAULT 'SEMI_ANNUAL',
    day_count_convention VARCHAR(20) NOT NULL DEFAULT 'ACT_ACT',

    CONSTRAINT valid_coupon CHECK (coupon_rate >= 0 AND coupon_rate <= 1),
    CONSTRAINT valid_dates CHECK (maturity_date > issue_date OR issue_date IS NULL)
);

-- Index for lookups by ISIN
CREATE INDEX idx_bonds_isin ON bonds(isin);
CREATE INDEX idx_bonds_maturity ON bonds(maturity_date);

-- ============================================
-- INTEREST RATE SWAPS TABLE (Child)
-- ============================================
CREATE TABLE interest_rate_swaps (
    instrument_id UUID PRIMARY KEY REFERENCES instruments(id) ON DELETE CASCADE,
    fixed_rate DECIMAL(8, 6) NOT NULL,
    tenor VARCHAR(10) NOT NULL,
    trade_date DATE NOT NULL,
    maturity_date DATE NOT NULL,
    effective_date DATE,
    pay_receive VARCHAR(10) NOT NULL CHECK (pay_receive IN ('PAY', 'RECEIVE')),
    float_index VARCHAR(20) NOT NULL DEFAULT 'SOFR',
    payment_frequency VARCHAR(20) NOT NULL DEFAULT 'QUARTERLY',

    CONSTRAINT valid_swap_rate CHECK (fixed_rate >= 0 AND fixed_rate <= 1),
    CONSTRAINT valid_swap_dates CHECK (maturity_date > trade_date)
);

-- Index for common queries
CREATE INDEX idx_swaps_maturity ON interest_rate_swaps(maturity_date);
CREATE INDEX idx_swaps_trade_date ON interest_rate_swaps(trade_date);

-- ============================================
-- UPDATED_AT TRIGGER FUNCTION
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply trigger to instruments table
CREATE TRIGGER update_instruments_updated_at
    BEFORE UPDATE ON instruments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SAMPLE DATA (Optional - for testing)
-- ============================================

-- Insert sample bonds
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('11111111-1111-1111-1111-111111111111', 'BOND', 1000000.00, 'USD'),
    ('22222222-2222-2222-2222-222222222222', 'BOND', 5000000.00, 'USD'),
    ('33333333-3333-3333-3333-333333333333', 'BOND', 2500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('11111111-1111-1111-1111-111111111111', 'US912810TM25', 0.0375, '2028-11-15', '2023-11-15', 'SEMI_ANNUAL', 'ACT_ACT'),
    ('22222222-2222-2222-2222-222222222222', 'US912810TN08', 0.0425, '2033-08-15', '2023-08-15', 'SEMI_ANNUAL', 'ACT_ACT'),
    ('33333333-3333-3333-3333-333333333333', 'US912810TP55', 0.0450, '2053-02-15', '2023-02-15', 'SEMI_ANNUAL', 'ACT_ACT');

-- Insert sample swaps
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('44444444-4444-4444-4444-444444444444', 'SWAP', 10000000.00, 'USD'),
    ('55555555-5555-5555-5555-555555555555', 'SWAP', 25000000.00, 'USD');

INSERT INTO interest_rate_swaps (instrument_id, fixed_rate, tenor, trade_date, maturity_date, effective_date, pay_receive, float_index, payment_frequency) VALUES
    ('44444444-4444-4444-4444-444444444444', 0.0410, '5Y', '2024-01-15', '2029-01-15', '2024-01-17', 'PAY', 'SOFR', 'QUARTERLY'),
    ('55555555-5555-5555-5555-555555555555', 0.0435, '10Y', '2024-01-15', '2034-01-15', '2024-01-17', 'RECEIVE', 'SOFR', 'QUARTERLY');

-- ============================================
-- VERIFICATION QUERIES
-- ============================================
-- Run these to verify the schema is correct:
-- SELECT * FROM instruments;
-- SELECT i.*, b.* FROM instruments i JOIN bonds b ON i.id = b.instrument_id;
-- SELECT i.*, s.* FROM instruments i JOIN interest_rate_swaps s ON i.id = s.instrument_id;
