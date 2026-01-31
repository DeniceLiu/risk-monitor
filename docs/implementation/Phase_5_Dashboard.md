# Phase 5: Dashboard

**Duration:** Days 13-14
**Status:** ✅ Complete
**Prerequisites:** Phases 1-4 running (especially Redis with risk data)

---

## Overview

The Dashboard is a Streamlit application providing real-time visualization of portfolio risk metrics. It reads from Redis and auto-refreshes every 2 seconds.

---

## Access

**URL:** http://localhost:8501

---

## Directory Structure

```
dashboard/
├── Dockerfile
├── requirements.txt
└── app/
    ├── __init__.py
    ├── config.py     ← Settings
    ├── data.py       ← Redis data fetcher
    └── main.py       ← Streamlit application
```

---

## Features

### 1. Portfolio Summary
- Instrument count
- Total NPV
- Total DV01 with long/short indicator
- Last update timestamp

### 2. Key Rate Duration Profile
- Bar chart showing KRD at 2Y, 5Y, 10Y, 30Y tenors
- Identifies which parts of the curve drive risk

### 3. Risk Distribution
- Bar chart of DV01 by instrument
- Sorted by absolute value

### 4. Trade-Level Details
- Table with NPV, DV01, and KRD for each trade
- Formatted currency values

### 5. Status Indicator
- 🟢 Live (data < 10s old)
- 🟡 Stale (data 10-60s old)
- 🔴 Disconnected or very stale

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `REFRESH_INTERVAL` | `2` | Refresh interval in seconds |

---

## Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  📊 Fixed Income Risk Monitor                    [🟢 Live]  │
├─────────────────────────────────────────────────────────────┤
│  PORTFOLIO SUMMARY                                          │
│  ┌──────────┬────────────┬─────────────┬────────────┐      │
│  │ Instruments │ Total NPV   │ Total DV01   │ Last Update │  │
│  │     5       │ $11.3M      │ -$20.6K      │ 14:24:18   │  │
│  └──────────┴────────────┴─────────────┴────────────┘      │
├─────────────────────────────────────────────────────────────┤
│  KEY RATE DURATION              │  RISK DISTRIBUTION        │
│       ██                        │   ██████  Trade 1         │
│       ██                        │   ████    Trade 2         │
│  ██   ██   ██   ██              │   ███     Trade 3         │
│  2Y   5Y   10Y  30Y             │   ██      Trade 4         │
├─────────────────────────────────────────────────────────────┤
│  TRADE-LEVEL RISK DETAILS                                   │
│  ┌────────────┬──────────┬─────────┬────────┬────────┐     │
│  │ Instrument │   NPV    │   DV01  │ KRD 2Y │ KRD 5Y │     │
│  │ 11111...   │ $994.5K  │ $256.97 │ $47.85 │ -$17.76│     │
│  │ 22222...   │ $4.78M   │ $683.21 │ ...    │ ...    │     │
│  └────────────┴──────────┴─────────┴────────┴────────┘     │
└─────────────────────────────────────────────────────────────┘
```

---

## Running Locally

```bash
cd dashboard
pip install -r requirements.txt

export REDIS_HOST=localhost
export REDIS_PORT=6379

streamlit run app/main.py
```

---

## Docker

```bash
# Build and start
docker-compose up -d --build dashboard

# View logs
docker-compose logs -f dashboard

# Access
open http://localhost:8501
```

---

## Acceptance Criteria

- [x] Streamlit dashboard application
- [x] Portfolio summary with NPV, DV01, instrument count
- [x] Key Rate Duration bar chart
- [x] Risk distribution by instrument chart
- [x] Trade-level details table
- [x] Auto-refresh (2-second interval)
- [x] Connection status indicator
- [x] Docker container on port 8501

---

## System Complete

All 5 phases are now complete:

1. ✅ **Phase 1:** Infrastructure (Kafka, PostgreSQL, Redis)
2. ✅ **Phase 2:** Security Master API (FastAPI)
3. ✅ **Phase 3:** Market Data Feed (Python generator → Kafka)
4. ✅ **Phase 4:** Risk Engine (QuantLib pricing, DV01/KRD)
5. ✅ **Phase 5:** Dashboard (Streamlit visualization)

---

**Completed:** 2026-01-31
