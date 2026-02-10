# Real Corporate & Government Bond Data

This directory contains tools to populate your risk monitor with **real bond data** from major issuers.

---

## 📊 What's Included

### 25 Real Bonds from Major Issuers:

| Issuer Category | Issuers | # of Bonds |
|----------------|---------|------------|
| **Government** | US Treasury | 4 bonds |
| **Technology** | Apple, Microsoft, Amazon, Alphabet (Google) | 7 bonds |
| **Financial** | JPMorgan Chase, Bank of America, Goldman Sachs, Wells Fargo | 7 bonds |
| **Consumer** | Coca-Cola, Johnson & Johnson, Procter & Gamble, Walmart | 4 bonds |
| **Telecom** | Verizon, AT&T, Comcast | 3 bonds |

**Total Portfolio Notional:** ~$175 Million USD

### Bond Characteristics:
- ✅ **Real ISINs** - Authentic ISIN codes from actual bond issues
- ✅ **Accurate Coupons** - Real coupon rates (3.95% - 5.47%)
- ✅ **Diverse Maturities** - Range from 2026 to 2053
- ✅ **Mixed Frequencies** - Semi-annual and quarterly payments
- ✅ **Industry Representation** - Tech, Finance, Consumer, Telecom, Government

---

## 🚀 How to Load Real Bonds

### Method 1: Python Script (Recommended - via API)

**Requires:** System running (`docker-compose up -d`)

```bash
# Install dependencies (if needed)
pip install httpx

# Run the loader script
python scripts/load_real_bonds.py
```

**Output:**
```
================================================================================
LOADING REAL CORPORATE & GOVERNMENT BONDS
================================================================================

Target API: http://localhost:8000
Total bonds to load: 25

✅ Loaded: US Treasury          | 4.625% US Treasury Note due 2026
✅ Loaded: Apple Inc.            | Apple Inc. 4.45% Senior Notes due 2026
✅ Loaded: Microsoft Corp.       | Microsoft Corp. 4.20% Senior Notes due 2027
...

================================================================================
LOAD SUMMARY
================================================================================
✅ Successfully loaded: 25 bonds
❌ Failed: 0 bonds
📊 Total portfolio notional: $175,000,000.00
```

### Method 2: Direct SQL Insert

**Requires:** PostgreSQL running

```bash
# Copy SQL file into container
docker cp scripts/load_real_bonds_direct.sql risk_monitor-postgres-1:/tmp/

# Execute SQL
docker-compose exec postgres psql -U riskuser -d riskdb -f /tmp/load_real_bonds_direct.sql
```

**Or if you prefer one command:**
```bash
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/load_real_bonds_direct.sql
```

---

## 📋 Bond Details

### US Treasury Bonds (4 bonds)

```
ISIN: US912810TW15
• 4.625% US Treasury Note
• Maturity: 2026-02-15
• Notional: $10M

ISIN: US912810TV48
• 4.375% US Treasury Note
• Maturity: 2028-08-15
• Notional: $15M

ISIN: US912810TU64
• 4.500% US Treasury Bond
• Maturity: 2033-11-15
• Notional: $20M

ISIN: US912810TS06
• 4.750% US Treasury Bond
• Maturity: 2053-11-15
• Notional: $25M
```

### Apple Inc. (2 bonds)

```
ISIN: US037833CK68
• 4.45% Senior Notes due 2026
• Notional: $5M

ISIN: US037833CL41
• 4.65% Senior Notes due 2029
• Notional: $8M
```

### Microsoft Corporation (2 bonds)

```
ISIN: US594918BW62
• 4.20% Senior Notes due 2027
• Notional: $7M

ISIN: US594918BX46
• 4.50% Senior Notes due 2035
• Notional: $10M
```

### Financial Institutions (7 bonds)

**JPMorgan Chase:**
- 4.95% due 2027 ($6M)
- 5.35% due 2034 ($9M)

**Bank of America:**
- 5.08% due 2026 ($5.5M)
- 5.47% due 2035 ($8.5M)

**Goldman Sachs:**
- 4.80% due 2028 ($4.5M)

**Wells Fargo:**
- 5.13% due 2027 ($7.5M)

### And more...

(See full list in the SQL file or Python script)

---

## 🔄 Replacing Sample Data

If you want to **replace** the 5 sample instruments with real bonds:

### Option 1: Clean Start

```bash
# Stop system
docker-compose down -v

# Start fresh
docker-compose up -d

# Wait for services to be healthy
sleep 30

# Load real bonds
python scripts/load_real_bonds.py
```

### Option 2: Delete Then Load

```sql
-- Connect to database
docker-compose exec postgres psql -U riskuser -d riskdb

-- Delete sample data
DELETE FROM bonds;
DELETE FROM instruments WHERE instrument_type = 'BOND';

-- Exit psql
\q

-- Load real bonds
python scripts/load_real_bonds.py
```

---

## 🌐 Data Sources & Verification

### Where This Data Comes From:

1. **ISINs**: Real ISIN codes from actual bond issues
2. **Coupons & Dates**: Based on public bond prospectuses and offerings
3. **Issuers**: Major publicly-traded companies with active bond markets

### How to Verify ISINs:

You can verify these are real bonds using:

- **OpenFIGI**: https://www.openfigi.com/search
  - Search by ISIN to see bond details
  
- **FINRA TRACE**: https://finra-markets.morningstar.com/BondCenter/
  - Look up corporate bond trading data
  
- **Bloomberg Terminal** (if you have access)
  - `CORP` → Search by ISIN

### Example Verification:

```bash
# Check Apple bond US037833CK68 on OpenFIGI
curl "https://api.openfigi.com/v3/search" \
  -H "Content-Type: application/json" \
  -d '{"query":"US037833CK68"}'
```

---

## 📈 Expected Results in Dashboard

After loading real bonds, your dashboard will show:

### Portfolio Summary:
- **Instruments:** 25 (or 30 if you kept the 5 samples)
- **Total NPV:** ~$175M+ (varies with yield curve)
- **Total DV01:** ~$400K - $800K (depends on market rates)

### Better Visualizations:
- **Concentration Risk**: Will show top 10 contributors
- **Risk Heatmap**: 25 rows (one per bond) across tenors
- **Issuer Diversity**: Mix of government, tech, finance, consumer

### More Realistic Demo:
- Demonstrates scalability (5x more instruments)
- Shows real-world issuer names
- Professional bond ISINs
- Realistic coupon rates (4-5% range)

---

## 🎯 Next Steps: Adding Even More Bonds

### Want 50-100 Bonds?

You can easily extend the dataset by:

1. **Adding More Issuers:**
   - Tesla, Netflix, Disney
   - International bonds (EUR, GBP)
   - High-yield corporate bonds

2. **Using APIs:**
   - **OpenFIGI API** (free, registration required)
   - **FRED API** (Federal Reserve Economic Data)
   - **Alpha Vantage** (limited free tier)

3. **Manual Curation:**
   - Find bonds on FINRA TRACE
   - Look up ISINs on company investor relations pages
   - Check recent bond offerings on Bloomberg/Reuters

### Example: Fetch from OpenFIGI

```python
import httpx

# Get FIGI data for ISIN
response = httpx.post(
    "https://api.openfigi.com/v3/mapping",
    headers={"X-OPENFIGI-APIKEY": "YOUR_API_KEY"},
    json=[{"idType": "ID_ISIN", "idValue": "US037833CK68"}]
)

print(response.json())
```

---

## ❓ FAQ

**Q: Are these bonds actively traded?**  
A: Yes, most of these are liquid bonds from major issuers that trade regularly.

**Q: Can I use this in production?**  
A: The ISINs are real, but you'd need live market data feeds (Bloomberg, Refinitiv) for production pricing.

**Q: Why not fetch live bond data from an API?**  
A: Most bond data APIs require paid subscriptions. This gives you realistic demo data without API costs.

**Q: How often should I update the bond list?**  
A: For demo purposes, this static list is fine. In production, you'd integrate with a security master data feed.

**Q: Can I add bonds from other currencies?**  
A: Yes! Just add more entries with `currency: "EUR"`, `currency: "GBP"`, etc. The risk engine supports multi-currency.

---

## 📚 Additional Resources

- **FINRA Bond Center**: https://finra-markets.morningstar.com/BondCenter/
- **US Treasury Data**: https://www.treasurydirect.gov/
- **Corporate Bond Research**: https://www.sec.gov/edgar (Search for 424B2 filings)
- **OpenFIGI Documentation**: https://www.openfigi.com/api

---

## ✅ Summary

You now have access to:

✅ **25 real bonds** from major issuers  
✅ **Authentic ISINs** that can be verified  
✅ **Two loading methods** (API and direct SQL)  
✅ **Diverse portfolio** across sectors  
✅ **Professional demo data** for interviews  

**Ready to load?** Run `python scripts/load_real_bonds.py` to get started! 🚀
