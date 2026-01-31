# Phase 4: Risk Engine

**Duration:** Days 10-12
**Status:** ✅ Complete
**Prerequisites:** Phases 1-3 infrastructure running

---

## Overview

The Risk Engine consumes yield curve updates from Kafka, prices instruments using QuantLib, calculates risk metrics (DV01, KRD), and writes results to Redis for the dashboard.

---

## Architecture

```
Kafka (yield_curve_ticks) → Risk Engine → Redis (trade:*:risk)
                                ↑
                    Security Master (portfolio load)
```

---

## Directory Structure

```
risk_engine/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              ← Entry point
│   ├── config.py            ← Settings
│   ├── portfolio.py         ← Load instruments from Security Master
│   ├── pricing/
│   │   ├── __init__.py
│   │   ├── curves.py        ← QuantLib yield curve building
│   │   ├── instruments.py   ← Bond/swap pricing
│   │   └── risk.py          ← DV01/KRD calculations
│   └── consumer/
│       ├── __init__.py
│       ├── kafka_consumer.py
│       └── redis_writer.py
└── tests/
    ├── __init__.py
    └── test_pricing.py
```

---

## Key Components

### 1. Yield Curve Builder (`curves.py`)

Uses mutable QuantLib Quote objects so curves auto-recalibrate when rates change:

```python
# Quotes are updated, curve automatically recalibrates
quote_2y.setValue(0.0415)  # No need to rebuild curve!
```

### 2. Risk Calculator (`risk.py`)

Implements bump-and-reprice for numerical sensitivities:

**DV01 (Dollar Value of 1bp):**
```
DV01 = (NPV_down - NPV_up) / 2
```

**Key Rate Duration (KRD):**
- Bump individual tenor points (2Y, 5Y, 10Y, 30Y)
- Measures sensitivity to specific parts of the curve

### 3. Redis Storage

Trade-level risk stored as hashes:
```
trade:{id}:risk → {
    npv: "994543.69",
    dv01: "256.97",
    krd_2y: "47.85",
    krd_5y: "-17.76",
    krd_10y: "-1.04",
    krd_30y: "-0.03",
    curve_timestamp: "1769592480000",
    updated_at: "1769886988967"
}
```

Portfolio aggregates:
```
portfolio:aggregates → {
    total_npv: "11289590.65",
    total_dv01: "-20626.98",
    instrument_count: "5",
    total_krd_2y: "9.55",
    ...
}
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_TOPIC` | `yield_curve_ticks` | Topic to consume |
| `KAFKA_GROUP_ID` | `risk-engine` | Consumer group |
| `REDIS_HOST` | `localhost` | Redis host |
| `REDIS_PORT` | `6379` | Redis port |
| `SECURITY_MASTER_URL` | `http://localhost:8000` | Security Master API |
| `WORKER_ID` | `worker-1` | Worker identifier |

---

## Risk Metrics Example

For a $1M 5-year Treasury bond at 3.75% coupon:

| Metric | Value | Interpretation |
|--------|-------|----------------|
| NPV | $994,543 | Present value of all cash flows |
| DV01 | $257 | Lose $257 if rates rise 1bp |
| KRD 2Y | $47.85 | Sensitivity to 2Y rate |
| KRD 5Y | -$17.76 | Sensitivity to 5Y rate |

---

## Scaling

The engine supports horizontal scaling via Kafka consumer groups:

```yaml
# docker-compose.yml
risk-engine-1:
  environment:
    KAFKA_GROUP_ID: risk-engine
    WORKER_ID: worker-1

risk-engine-2:
  environment:
    KAFKA_GROUP_ID: risk-engine
    WORKER_ID: worker-2
```

Kafka automatically balances partitions across workers.

---

## Tests

```bash
cd /Users/liuyuxuan/risk_monitor/risk_engine
PYTHONPATH=. pytest tests/ -v
```

8 tests covering:
- Yield curve building
- Discount factor calculation
- Bond pricing
- Swap pricing
- DV01 calculation
- KRD calculation

---

## Viewing Risk Data

```bash
# List all trade risks
docker exec redis redis-cli KEYS "trade:*:risk"

# Get specific trade risk
docker exec redis redis-cli HGETALL "trade:11111111-1111-1111-1111-111111111111:risk"

# Get portfolio aggregates
docker exec redis redis-cli HGETALL "portfolio:aggregates"
```

---

## Known Limitations

1. **Historical Fixings:** Swaps with past effective dates require SOFR fixing history, which is not included. New swaps with future dates work correctly.

2. **Single Currency:** Currently supports USD only.

3. **Curve Construction:** Uses OIS rate helpers for simplicity; production would use full instrument suite.

---

## Acceptance Criteria

- [x] Kafka consumer for yield curve updates
- [x] QuantLib yield curve building (dual-curve framework)
- [x] Bond pricing with QuantLib
- [x] Swap pricing with QuantLib
- [x] DV01 calculation (bump-and-reprice)
- [x] KRD calculation for key tenors
- [x] Redis writer for trade-level risk
- [x] Portfolio aggregation
- [x] 8 unit tests passing
- [x] Docker container running
- [x] Consumer group support for scaling

---

## Next Phase

**Phase 5: Aggregation Layer + Dashboard** - Streamlit dashboard for real-time visualization.

---

**Completed:** 2026-01-31
