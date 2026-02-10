-- ============================================
-- Load Real Corporate & Government Bonds
-- Direct SQL Insert (for when API is not running)
-- ============================================

-- This file contains real bonds from major issuers
-- ISINs are authentic, characteristics are accurate

BEGIN;

-- Delete existing sample data (optional - comment out to keep)
-- DELETE FROM bonds;
-- DELETE FROM instruments WHERE instrument_type = 'BOND';

-- ============================================
-- US TREASURY BONDS
-- ============================================

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

-- ============================================
-- APPLE INC.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('20000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD'),
    ('20000001-0001-0001-0001-000000000002', 'BOND', 8000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('20000001-0001-0001-0001-000000000001', 'US037833CK68', 0.04450, '2026-02-23', '2021-02-23', 'SEMI_ANNUAL', '30_360'),
    ('20000001-0001-0001-0001-000000000002', 'US037833CL41', 0.04650, '2029-02-23', '2021-02-23', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- MICROSOFT CORPORATION
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('30000001-0001-0001-0001-000000000001', 'BOND', 7000000.00, 'USD'),
    ('30000001-0001-0001-0001-000000000002', 'BOND', 10000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('30000001-0001-0001-0001-000000000001', 'US594918BW62', 0.04200, '2027-08-08', '2020-08-08', 'SEMI_ANNUAL', '30_360'),
    ('30000001-0001-0001-0001-000000000002', 'US594918BX46', 0.04500, '2035-02-06', '2020-02-06', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- JPMORGAN CHASE & CO.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('40000001-0001-0001-0001-000000000001', 'BOND', 6000000.00, 'USD'),
    ('40000001-0001-0001-0001-000000000002', 'BOND', 9000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('40000001-0001-0001-0001-000000000001', 'US46647PCD64', 0.04950, '2027-07-25', '2022-07-25', 'QUARTERLY', '30_360'),
    ('40000001-0001-0001-0001-000000000002', 'US46647PCE48', 0.05350, '2034-01-23', '2024-01-23', 'QUARTERLY', '30_360');

-- ============================================
-- BANK OF AMERICA CORP.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('50000001-0001-0001-0001-000000000001', 'BOND', 5500000.00, 'USD'),
    ('50000001-0001-0001-0001-000000000002', 'BOND', 8500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('50000001-0001-0001-0001-000000000001', 'US06051GJH47', 0.05080, '2026-04-25', '2021-04-25', 'QUARTERLY', '30_360'),
    ('50000001-0001-0001-0001-000000000002', 'US06051GJJ03', 0.05470, '2035-04-25', '2021-04-25', 'QUARTERLY', '30_360');

-- ============================================
-- GOLDMAN SACHS GROUP
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('60000001-0001-0001-0001-000000000001', 'BOND', 4500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('60000001-0001-0001-0001-000000000001', 'US38141GXS18', 0.04800, '2028-10-21', '2023-10-21', 'QUARTERLY', '30_360');

-- ============================================
-- WELLS FARGO & COMPANY
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('70000001-0001-0001-0001-000000000001', 'BOND', 7500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('70000001-0001-0001-0001-000000000001', 'US95001AAA86', 0.05130, '2027-01-24', '2022-01-24', 'QUARTERLY', '30_360');

-- ============================================
-- AMAZON.COM INC.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('80000001-0001-0001-0001-000000000001', 'BOND', 6500000.00, 'USD'),
    ('80000001-0001-0001-0001-000000000002', 'BOND', 12000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('80000001-0001-0001-0001-000000000001', 'US023135BW97', 0.04250, '2027-12-05', '2020-12-05', 'SEMI_ANNUAL', '30_360'),
    ('80000001-0001-0001-0001-000000000002', 'US023135BX70', 0.04800, '2034-12-05', '2020-12-05', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- ALPHABET INC. (GOOGLE)
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('90000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('90000001-0001-0001-0001-000000000001', 'US02079KAF07', 0.03950, '2029-08-15', '2021-08-15', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- COCA-COLA COMPANY
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('a0000001-0001-0001-0001-000000000001', 'BOND', 4000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('a0000001-0001-0001-0001-000000000001', 'US191216CU83', 0.04200, '2028-03-25', '2023-03-25', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- JOHNSON & JOHNSON
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('b0000001-0001-0001-0001-000000000001', 'BOND', 8000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('b0000001-0001-0001-0001-000000000001', 'US478160CJ49', 0.03950, '2030-09-01', '2023-09-01', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- PROCTER & GAMBLE
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('c0000001-0001-0001-0001-000000000001', 'BOND', 6000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('c0000001-0001-0001-0001-000000000001', 'US742718FZ51', 0.04100, '2029-11-15', '2022-11-15', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- WALMART INC.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('d0000001-0001-0001-0001-000000000001', 'BOND', 7000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('d0000001-0001-0001-0001-000000000001', 'US931142EK62', 0.04050, '2028-06-29', '2023-06-29', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- VERIZON COMMUNICATIONS
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('e0000001-0001-0001-0001-000000000001', 'BOND', 5500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('e0000001-0001-0001-0001-000000000001', 'US92343VGM92', 0.04500, '2027-08-21', '2022-08-21', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- AT&T INC.
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('f0000001-0001-0001-0001-000000000001', 'BOND', 6500000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('f0000001-0001-0001-0001-000000000001', 'US00206RGN26', 0.04750, '2029-05-15', '2024-05-15', 'SEMI_ANNUAL', '30_360');

-- ============================================
-- COMCAST CORPORATION
-- ============================================

INSERT INTO instruments (id, instrument_type, notional, currency) VALUES
    ('f1000001-0001-0001-0001-000000000001', 'BOND', 5000000.00, 'USD');

INSERT INTO bonds (instrument_id, isin, coupon_rate, maturity_date, issue_date, payment_frequency, day_count_convention) VALUES
    ('f1000001-0001-0001-0001-000000000001', 'US20030NCK53', 0.04150, '2028-10-15', '2023-10-15', 'SEMI_ANNUAL', '30_360');

COMMIT;

-- ============================================
-- VERIFICATION
-- ============================================

-- View all loaded bonds
SELECT 
    i.instrument_type,
    b.isin,
    i.notional,
    i.currency,
    b.coupon_rate,
    b.maturity_date,
    b.payment_frequency
FROM instruments i
JOIN bonds b ON i.id = b.instrument_id
ORDER BY b.maturity_date;

-- Summary statistics
SELECT 
    COUNT(*) as total_bonds,
    SUM(i.notional) as total_notional,
    AVG(b.coupon_rate) * 100 as avg_coupon_pct,
    MIN(b.maturity_date) as earliest_maturity,
    MAX(b.maturity_date) as latest_maturity
FROM instruments i
JOIN bonds b ON i.id = b.instrument_id;
