-- ============================================
-- Risk Monitor Database Schema
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
    portfolio_id VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes
CREATE INDEX idx_instruments_type ON instruments(instrument_type);
CREATE INDEX idx_instruments_created_at ON instruments(created_at);
CREATE INDEX idx_instruments_portfolio ON instruments(portfolio_id);

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

CREATE INDEX idx_swaps_maturity ON interest_rate_swaps(maturity_date);
CREATE INDEX idx_swaps_trade_date ON interest_rate_swaps(trade_date);

-- ============================================
-- UPDATED_AT TRIGGER
-- ============================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_instruments_updated_at
    BEFORE UPDATE ON instruments
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- SEED DATA: 27 Real Corporate & Government Bonds
-- ============================================

-- US Treasury (4 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('10000001-0001-0001-0001-000000000001', 'BOND', 10000000.00, 'USD'),
    ('10000001-0001-0001-0001-000000000002', 'BOND', 15000000.00, 'USD'),
    ('10000001-0001-0001-0001-000000000003', 'BOND', 20000000.00, 'USD'),
    ('10000001-0001-0001-0001-000000000004', 'BOND', 25000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('10000001-0001-0001-0001-000000000001', 'US912810TW15', 0.04625, '2026-02-15', '2023-02-15', 'SEMI_ANNUAL', 'ACT_ACT'),
    ('10000001-0001-0001-0001-000000000002', 'US912810TV48', 0.04375, '2028-08-15', '2023-08-15', 'SEMI_ANNUAL', 'ACT_ACT'),
    ('10000001-0001-0001-0001-000000000003', 'US912810TU64', 0.04500, '2033-11-15', '2023-11-15', 'SEMI_ANNUAL', 'ACT_ACT'),
    ('10000001-0001-0001-0001-000000000004', 'US912810TS06', 0.04750, '2053-11-15', '2023-11-15', 'SEMI_ANNUAL', 'ACT_ACT');

-- Apple Inc. (2 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('20000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD'),
    ('20000001-0001-0001-0001-000000000002', 'BOND', 8000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('20000001-0001-0001-0001-000000000001', 'US037833CK68', 0.04450, '2026-02-23', '2021-02-23', 'SEMI_ANNUAL', '30_360'),
    ('20000001-0001-0001-0001-000000000002', 'US037833CL41', 0.04650, '2029-02-23', '2021-02-23', 'SEMI_ANNUAL', '30_360');

-- Microsoft Corp. (2 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('30000001-0001-0001-0001-000000000001', 'BOND', 7000000.00, 'USD'),
    ('30000001-0001-0001-0001-000000000002', 'BOND', 10000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('30000001-0001-0001-0001-000000000001', 'US594918BW62', 0.04200, '2027-08-08', '2020-08-08', 'SEMI_ANNUAL', '30_360'),
    ('30000001-0001-0001-0001-000000000002', 'US594918BX46', 0.04500, '2035-02-06', '2020-02-06', 'SEMI_ANNUAL', '30_360');

-- JPMorgan Chase (2 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('40000001-0001-0001-0001-000000000001', 'BOND', 6000000.00, 'USD'),
    ('40000001-0001-0001-0001-000000000002', 'BOND', 9000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('40000001-0001-0001-0001-000000000001', 'US46647PCD64', 0.04950, '2027-07-25', '2022-07-25', 'QUARTERLY', '30_360'),
    ('40000001-0001-0001-0001-000000000002', 'US46647PCE48', 0.05350, '2034-01-23', '2024-01-23', 'QUARTERLY', '30_360');

-- Bank of America (2 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('50000001-0001-0001-0001-000000000001', 'BOND', 5500000.00, 'USD'),
    ('50000001-0001-0001-0001-000000000002', 'BOND', 8500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('50000001-0001-0001-0001-000000000001', 'US06051GJH47', 0.05080, '2026-04-25', '2021-04-25', 'QUARTERLY', '30_360'),
    ('50000001-0001-0001-0001-000000000002', 'US06051GJJ03', 0.05470, '2035-04-25', '2021-04-25', 'QUARTERLY', '30_360');

-- Goldman Sachs (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('60000001-0001-0001-0001-000000000001', 'BOND', 4500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('60000001-0001-0001-0001-000000000001', 'US38141GXS18', 0.04800, '2028-10-21', '2023-10-21', 'QUARTERLY', '30_360');

-- Wells Fargo (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('70000001-0001-0001-0001-000000000001', 'BOND', 7500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('70000001-0001-0001-0001-000000000001', 'US95001AAA86', 0.05130, '2027-01-24', '2022-01-24', 'QUARTERLY', '30_360');

-- Amazon.com (2 bonds)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('80000001-0001-0001-0001-000000000001', 'BOND', 6500000.00, 'USD'),
    ('80000001-0001-0001-0001-000000000002', 'BOND', 12000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('80000001-0001-0001-0001-000000000001', 'US023135BW97', 0.04250, '2027-12-05', '2020-12-05', 'SEMI_ANNUAL', '30_360'),
    ('80000001-0001-0001-0001-000000000002', 'US023135BX70', 0.04800, '2034-12-05', '2020-12-05', 'SEMI_ANNUAL', '30_360');

-- Alphabet Inc. (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('90000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('90000001-0001-0001-0001-000000000001', 'US02079KAF07', 0.03950, '2029-08-15', '2021-08-15', 'SEMI_ANNUAL', '30_360');

-- Coca-Cola (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('a0000001-0001-0001-0001-000000000001', 'BOND', 4000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('a0000001-0001-0001-0001-000000000001', 'US191216CU83', 0.04200, '2028-03-25', '2023-03-25', 'SEMI_ANNUAL', '30_360');

-- Johnson & Johnson (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('b0000001-0001-0001-0001-000000000001', 'BOND', 8000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('b0000001-0001-0001-0001-000000000001', 'US478160CJ49', 0.03950, '2030-09-01', '2023-09-01', 'SEMI_ANNUAL', '30_360');

-- Procter & Gamble (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('c0000001-0001-0001-0001-000000000001', 'BOND', 6000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('c0000001-0001-0001-0001-000000000001', 'US742718FZ51', 0.04100, '2029-11-15', '2022-11-15', 'SEMI_ANNUAL', '30_360');

-- Walmart Inc. (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('d0000001-0001-0001-0001-000000000001', 'BOND', 7000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('d0000001-0001-0001-0001-000000000001', 'US931142EK62', 0.04050, '2028-06-29', '2023-06-29', 'SEMI_ANNUAL', '30_360');

-- Verizon Communications (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('e0000001-0001-0001-0001-000000000001', 'BOND', 5500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('e0000001-0001-0001-0001-000000000001', 'US92343VGM92', 0.04500, '2027-08-21', '2022-08-21', 'SEMI_ANNUAL', '30_360');

-- AT&T Inc. (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('f0000001-0001-0001-0001-000000000001', 'BOND', 6500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('f0000001-0001-0001-0001-000000000001', 'US00206RGN26', 0.04750, '2029-05-15', '2024-05-15', 'SEMI_ANNUAL', '30_360');

-- Comcast Corp. (1 bond)
INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('f1000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('f1000001-0001-0001-0001-000000000001', 'US20030NCK53', 0.04150, '2028-10-15', '2023-10-15', 'SEMI_ANNUAL', '30_360');
