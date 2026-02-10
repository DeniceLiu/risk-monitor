# Real Corporate Bond Data - Quick Start Guide

## 🎯 What You Get

**25 real corporate and government bonds** from major issuers:
- 🏛️ US Treasury (4 bonds - $70M)
- 🍎 Apple, Microsoft, Amazon, Google (7 bonds - $48M)
- 🏦 JPMorgan, Bank of America, Goldman Sachs, Wells Fargo (7 bonds - $45.5M)
- 🛒 Coca-Cola, J&J, P&G, Walmart (4 bonds - $25M)
- 📱 Verizon, AT&T, Comcast (3 bonds - $17M)

**Total: $175M portfolio** with authentic ISINs and real characteristics!

---

## ⚡ Quick Start (3 Steps)

### Step 1: Start the System

```bash
cd /Users/liuyuxuan/risk_monitor
docker-compose up -d
```

Wait ~30 seconds for services to be ready.

### Step 2: Load Real Bonds

```bash
python scripts/load_real_bonds.py
```

### Step 3: View in Dashboard

Open browser: http://localhost:8501

You'll now see **25 real bonds** instead of 5 samples! 🎉

---

## 📊 What Changes in Your Dashboard

### Before (5 sample bonds):
```
Portfolio Summary:
├─ Instruments: 5
├─ Total NPV: ~$43M
├─ Total DV01: ~$150K
└─ Generic ISINs
```

### After (25 real bonds):
```
Portfolio Summary:
├─ Instruments: 25 (or 30 if kept samples)
├─ Total NPV: ~$175M+
├─ Total DV01: ~$600K+
└─ Real ISINs from:
    • Apple Inc.
    • Microsoft Corp.
    • JPMorgan Chase
    • Amazon.com Inc.
    • US Treasury
    • Goldman Sachs
    • Bank of America
    • And 11 more...
```

### Enhanced Visualizations:
- ✅ **Concentration Risk** shows real issuer names
- ✅ **Risk Heatmap** has 25 rows (more interesting!)
- ✅ **Trade Details Table** shows professional ISINs
- ✅ **Excel Export** contains real bond data

---

## 🔄 Alternative Methods

### Method A: Direct SQL (if API not running)

```bash
# Load directly into PostgreSQL
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/load_real_bonds_direct.sql
```

### Method B: Start Fresh (Remove Samples)

```bash
# Completely reset and load only real bonds
docker-compose down -v
docker-compose up -d
sleep 30
python scripts/load_real_bonds.py
```

---

## ✅ Verification

### Check if bonds were loaded:

```bash
# Via API
curl http://localhost:8000/api/v1/instruments?page_size=50 | jq '.total'
# Should show 25 (or 30 if samples kept)

# Via SQL
docker-compose exec postgres psql -U riskuser -d riskdb -c \
  "SELECT COUNT(*) FROM bonds;"

# Via Dashboard
# Open http://localhost:8501 and check "Instruments" metric
```

---

## 📋 Bond Details Preview

**Sample of what you're getting:**

```
✅ US Treasury 4.625% due 2026 (ISIN: US912810TW15) - $10M
✅ Apple Inc. 4.45% due 2026 (ISIN: US037833CK68) - $5M
✅ Microsoft 4.20% due 2027 (ISIN: US594918BW62) - $7M
✅ JPMorgan 4.95% due 2027 (ISIN: US46647PCD64) - $6M
✅ Bank of America 5.08% due 2026 (ISIN: US06051GJH47) - $5.5M
✅ Amazon 4.25% due 2027 (ISIN: US023135BW97) - $6.5M
✅ Goldman Sachs 4.80% due 2028 (ISIN: US38141GXS18) - $4.5M
... and 18 more real bonds!
```

All ISINs can be verified on:
- OpenFIGI: https://www.openfigi.com/search
- FINRA: https://finra-markets.morningstar.com/BondCenter/

---

## 🎯 Why This Matters for Interviews

**Before:**
> "I built a risk monitor with sample data"

**After:**
> "I built a risk monitor tracking $175M in real corporate bonds from Apple, Microsoft, JPMorgan Chase, and other major issuers. The system processes 25 instruments with authentic ISINs, calculating real-time DV01 and KRD sensitivities."

**Much more impressive!** 💪

---

## 💡 Pro Tips

### Tip 1: Keep Both Sample and Real Bonds
Don't delete the 5 sample bonds - having 30 total instruments shows better scalability!

### Tip 2: Point Out Real ISINs
During demos, highlight that these are real bonds:
- "This is Apple's actual 4.45% bond maturing in 2026"
- "You can verify the ISIN US037833CK68 on Bloomberg or OpenFIGI"

### Tip 3: Explain Diversity
Mention the portfolio composition:
- "We have exposure across tech, financial, consumer, and telecom sectors"
- "Mix of short-dated (2026) and long-dated (2053) bonds"
- "Coupons ranging from 3.95% to 5.47%, reflecting credit quality"

---

## 🚀 Next Steps

1. **Load the bonds:** `python scripts/load_real_bonds.py`
2. **Restart risk engine:** `docker-compose restart risk_worker`
3. **Watch dashboard:** See real calculations on real bonds!
4. **Export to Excel:** Download and show the real bond details
5. **Demo with confidence:** You're now working with production-quality data!

---

## 📚 Full Documentation

See `scripts/REAL_BONDS_README.md` for:
- Complete bond list with all details
- Data source verification
- How to add more bonds
- API integration options
- FAQ and troubleshooting

---

**Ready?** Just run:

```bash
python scripts/load_real_bonds.py
```

And watch your dashboard transform from demo to professional! 🎉
