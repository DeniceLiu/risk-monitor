-- ============================================
-- Assign Portfolios to Existing Bonds
-- Quick fix for portfolio visualization errors
-- ============================================

BEGIN;

-- First, ensure portfolio table exists
CREATE TABLE IF NOT EXISTS portfolios (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add portfolio_id column if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'instruments' AND column_name = 'portfolio_id'
    ) THEN
        ALTER TABLE instruments ADD COLUMN portfolio_id VARCHAR(50) REFERENCES portfolios(id);
        CREATE INDEX idx_instruments_portfolio ON instruments(portfolio_id);
    END IF;
END $$;

-- Insert default portfolio
INSERT INTO portfolios (id, name, description, strategy_type) VALUES
    ('DEFAULT', 'Main Portfolio', 'Default portfolio for unassigned instruments', 'MIXED')
ON CONFLICT (id) DO NOTHING;

-- Assign all existing instruments without portfolio to DEFAULT
UPDATE instruments 
SET portfolio_id = 'DEFAULT' 
WHERE portfolio_id IS NULL;

COMMIT;

-- Verify
SELECT 
    COALESCE(i.portfolio_id, 'NULL') as portfolio,
    p.name as portfolio_name,
    i.instrument_type,
    COUNT(*) as count,
    SUM(i.notional) as total_notional
FROM instruments i
LEFT JOIN portfolios p ON i.portfolio_id = p.id
GROUP BY i.portfolio_id, p.name, i.instrument_type
ORDER BY i.portfolio_id, i.instrument_type;
