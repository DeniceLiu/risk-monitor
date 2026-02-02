-- ============================================
-- Add Portfolio Support to Risk Monitor
-- Migration Script
-- ============================================

BEGIN;

-- Create portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id VARCHAR(50) PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    strategy_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add portfolio_id to instruments table
ALTER TABLE instruments 
ADD COLUMN IF NOT EXISTS portfolio_id VARCHAR(50) REFERENCES portfolios(id);

-- Create index for portfolio queries
CREATE INDEX IF NOT EXISTS idx_instruments_portfolio ON instruments(portfolio_id);

-- Create update_updated_at_column function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to portfolios (drop first if exists)
DROP TRIGGER IF EXISTS update_portfolios_updated_at ON portfolios;
CREATE TRIGGER update_portfolios_updated_at
    BEFORE UPDATE ON portfolios
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Insert default portfolios
INSERT INTO portfolios (id, name, description, strategy_type) VALUES
    ('CREDIT_IG', 'Investment Grade Credit', 'High-quality corporate bonds, BBB- and above', 'CREDIT'),
    ('CREDIT_HY', 'High Yield Credit', 'Below investment grade corporate bonds', 'CREDIT'),
    ('GOVT_US', 'US Government', 'US Treasury notes and bonds', 'GOVERNMENT'),
    ('TECH_SECTOR', 'Technology Sector', 'Concentrated tech company debt', 'SECTOR'),
    ('FINANCIAL_SECTOR', 'Financial Institutions', 'Bank and insurance company bonds', 'SECTOR'),
    ('CONSUMER_DISCRETIONARY', 'Consumer Discretionary', 'Retail, automotive, leisure', 'SECTOR'),
    ('HEALTHCARE_PHARMA', 'Healthcare & Pharma', 'Healthcare providers and pharmaceutical companies', 'SECTOR'),
    ('ENERGY_UTILITIES', 'Energy & Utilities', 'Power generation, oil & gas', 'SECTOR'),
    ('TELECOM_MEDIA', 'Telecom & Media', 'Telecommunications and media companies', 'SECTOR'),
    ('EMERGING_MARKETS', 'Emerging Markets Corporate', 'EM corporate bonds (USD denominated)', 'EMERGING_MARKETS')
ON CONFLICT (id) DO NOTHING;

COMMIT;

-- Verification
SELECT 
    p.id,
    p.name,
    COUNT(i.id) as instrument_count,
    SUM(i.notional) as total_notional
FROM portfolios p
LEFT JOIN instruments i ON p.id = i.portfolio_id
GROUP BY p.id, p.name
ORDER BY p.id;
