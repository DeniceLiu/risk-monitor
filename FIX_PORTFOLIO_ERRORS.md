# Fix Portfolio Visualization Errors

## 🐛 Problem
Dashboard shows "no portfolio assignments found" in all portfolio breakdown charts.

## 🔍 Root Cause
The existing 5 sample bonds don't have `portfolio_id` assigned in the database, but the updated dashboard expects portfolio information.

## ✅ Solutions (Pick One)

### **Solution 1: Quick Fix - Assign Default Portfolio** ⭐ FASTEST

Run this SQL script to assign all existing bonds to a default portfolio:

```bash
cd /Users/liuyuxuan/risk_monitor

# If system is running:
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/assign_portfolios_to_existing_bonds.sql

# If system is NOT running, start it first:
docker-compose up -d
sleep 10
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/assign_portfolios_to_existing_bonds.sql
```

**What this does:**
- Creates `portfolios` table if missing
- Adds `portfolio_id` column to `instruments` table if missing
- Creates a "Main Portfolio" (ID: DEFAULT)
- Assigns all existing bonds to this portfolio
- Dashboard will now show all 5 bonds under "Main Portfolio"

**Result:**
✅ Portfolio breakdown charts will now work  
✅ Shows "Main Portfolio" with all 5 bonds  
✅ No more "no portfolio assignments found" errors  

---

### **Solution 2: Load 1000+ Bonds with Portfolios** ⭐ BEST FOR DEMO

Generate and load 1000+ real bonds across 10 portfolios:

```bash
cd /Users/liuyuxuan/risk_monitor

# 1. Generate bond database
python scripts/fetch_finra_bonds.py --min-bonds 1000 --portfolios 10

# 2. Apply portfolio schema
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/add_portfolio_support.sql

# 3. Install dependencies
pip install tqdm httpx

# 4. Load bonds
python scripts/load_bonds_from_json.py --batch-size 50

# 5. Restart risk workers
docker-compose restart risk_worker
```

**What this does:**
- Generates 1,020 bonds from 60+ real issuers
- Creates 10 portfolio strategies
- Loads all bonds with proper portfolio assignments
- Dashboard shows rich portfolio breakdown

**Result:**
✅ 1,020 bonds across 10 portfolios  
✅ Real issuer names (Apple, Microsoft, JPMorgan...)  
✅ Portfolio breakdown shows 10 strategies  
✅ Much more impressive for interviews!  

---

### **Solution 3: Code Changes Only** (Already Applied)

I've updated the dashboard code to handle missing portfolio data gracefully:

**Changes made:**
- `dashboard/app/components/charts.py` - Added fallback to "Main Portfolio" when data missing
- `dashboard/app/data.py` - Added Portfolio column with default values

**What this does:**
- Dashboard won't crash if portfolio data is missing
- Shows "Main Portfolio" as default for all bonds
- Graceful degradation

**Result:**
✅ No more errors  
✅ Charts show all bonds under "Main Portfolio"  
⚠️ But still only 5 sample bonds  

---

## 🚀 Recommended Approach

**For Quick Fix (5 minutes):**
```bash
# Run Solution 1
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/assign_portfolios_to_existing_bonds.sql
docker-compose restart risk_worker
```

**For Impressive Demo (10 minutes):**
```bash
# Run Solution 2
python scripts/fetch_finra_bonds.py --min-bonds 1000 --portfolios 10
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/add_portfolio_support.sql
pip install tqdm httpx
python scripts/load_bonds_from_json.py --batch-size 50
docker-compose restart risk_worker
```

---

## 🧪 Verify the Fix

After applying Solution 1 or 2:

### 1. Check Database
```bash
docker-compose exec postgres psql -U riskuser -d riskdb -c "
SELECT 
    p.name as portfolio,
    COUNT(i.id) as instruments,
    SUM(i.notional) as total_notional
FROM portfolios p
LEFT JOIN instruments i ON p.id = i.portfolio_id
GROUP BY p.name
ORDER BY total_notional DESC;
"
```

**Expected output (Solution 1):**
```
    portfolio     | instruments | total_notional
------------------+-------------+----------------
 Main Portfolio   |           5 |       43500000
```

**Expected output (Solution 2):**
```
        portfolio              | instruments | total_notional
-------------------------------+-------------+----------------
 Investment Grade Credit       |         150 |     1200000000
 Financial Institutions        |         130 |     1170000000
 Technology Sector             |         120 |      840000000
 ...
```

### 2. Check Dashboard

1. Open: http://localhost:8501
2. Scroll to "Portfolio Breakdown" section
3. Should now see charts with data (not "no portfolio assignments found")

**Solution 1 result:**
- Bar chart showing "Main Portfolio"
- Pie chart showing 100% in "Main Portfolio"

**Solution 2 result:**
- Bar chart showing 10 portfolios
- Pie chart showing distribution across 10 strategies
- Can switch between portfolios using dropdown

---

## 🔧 Troubleshooting

### "Database 'riskdb' does not exist"
```bash
# Initialize database first
docker-compose up -d postgres
sleep 10
docker-compose exec postgres psql -U riskuser -d postgres -c "CREATE DATABASE riskdb;"
docker-compose exec -T postgres psql -U riskuser -d riskdb < scripts/init_db.sql
```

### "Permission denied connecting to Docker"
```bash
# Start Docker Desktop first, then try again
open -a Docker
# Wait for Docker to start, then retry
```

### "psql: command not found"
```bash
# Use docker-compose exec instead
docker-compose exec postgres psql -U riskuser -d riskdb -f /path/to/script.sql
```

### Charts still show "no portfolio assignments found"
```bash
# Restart risk workers to pick up changes
docker-compose restart risk_worker

# Clear Redis cache
docker-compose exec redis redis-cli FLUSHALL

# Restart dashboard
docker-compose restart dashboard
```

---

## 📊 Before & After

### Before (Broken):
```
Portfolio Breakdown:
  ┌─────────────────────────────────┐
  │                                 │
  │  No portfolio assignments found │
  │                                 │
  └─────────────────────────────────┘
```

### After Solution 1 (Quick Fix):
```
Portfolio Breakdown:
  ┌─────────────────────────────────┐
  │    Main Portfolio               │
  │    █████████████████  5 bonds   │
  │    DV01: $150K                  │
  └─────────────────────────────────┘
```

### After Solution 2 (Full Implementation):
```
Portfolio Breakdown:
  ┌─────────────────────────────────┐
  │  Investment Grade: ████████ 150 │
  │  Financial Inst:   ███████  130 │
  │  Technology:       ██████   120 │
  │  Healthcare:       █████    100 │
  │  ...7 more portfolios...        │
  └─────────────────────────────────┘
```

---

## ✅ Summary

**Issue:** Portfolio charts show "no portfolio assignments found"  
**Cause:** Bonds don't have portfolio_id in database  
**Fix:** Run `assign_portfolios_to_existing_bonds.sql` (Solution 1)  
**Better:** Load 1000+ bonds with portfolios (Solution 2)  

**Choose:**
- **Need it working NOW?** → Solution 1 (5 minutes)
- **Want impressive demo?** → Solution 2 (10 minutes)
- **Just browsing?** → Code changes already applied (no errors, but still basic)

---

Ready to fix? Run Solution 1 for quick fix or Solution 2 for full power! 🚀
