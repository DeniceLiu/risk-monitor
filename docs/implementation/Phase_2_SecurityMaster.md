# Phase 2: Security Master API

**Duration:** Days 4-6
**Status:** ✅ Complete
**Prerequisites:** Phase 1 infrastructure running

---

## Overview

The Security Master is a FastAPI REST service providing CRUD operations for financial instruments (bonds and interest rate swaps). It serves as the "Golden Source" of instrument reference data.

---

## Directory Structure

```
security_master/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py              ← FastAPI application
│   ├── config.py            ← Configuration settings
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py      ← Database connection
│   ├── models/
│   │   ├── __init__.py
│   │   └── instrument.py    ← SQLAlchemy models
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── instrument.py    ← Pydantic schemas
│   └── routes/
│       ├── __init__.py
│       └── instruments.py   ← API endpoints
└── tests/
    ├── __init__.py
    └── test_instruments.py  ← Unit tests
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check |
| `GET` | `/api/v1/instruments` | List all instruments (paginated) |
| `GET` | `/api/v1/instruments/{id}` | Get instrument by ID |
| `DELETE` | `/api/v1/instruments/{id}` | Delete instrument |
| `POST` | `/api/v1/instruments/bonds` | Create bond |
| `GET` | `/api/v1/instruments/bonds/{id}` | Get bond by ID |
| `POST` | `/api/v1/instruments/swaps` | Create swap |
| `GET` | `/api/v1/instruments/swaps/{id}` | Get swap by ID |

---

## Usage Examples

### List All Instruments
```bash
curl http://localhost:8000/api/v1/instruments
```

### Filter by Type
```bash
curl "http://localhost:8000/api/v1/instruments?instrument_type=BOND"
```

### Create Bond
```bash
curl -X POST http://localhost:8000/api/v1/instruments/bonds \
  -H "Content-Type: application/json" \
  -d '{
    "isin": "US912810XY99",
    "notional": 2000000.00,
    "coupon_rate": 0.0425,
    "maturity_date": "2035-06-15",
    "payment_frequency": "SEMI_ANNUAL"
  }'
```

### Create Swap
```bash
curl -X POST http://localhost:8000/api/v1/instruments/swaps \
  -H "Content-Type: application/json" \
  -d '{
    "notional": 50000000.00,
    "fixed_rate": 0.0395,
    "tenor": "7Y",
    "trade_date": "2026-01-29",
    "maturity_date": "2033-01-29",
    "pay_receive": "PAY"
  }'
```

### Delete Instrument
```bash
curl -X DELETE http://localhost:8000/api/v1/instruments/{uuid}
```

---

## Data Models

### Bond Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `isin` | string(12) | Yes | ISIN identifier |
| `notional` | decimal | Yes | Face value |
| `currency` | string(3) | No | Default: USD |
| `coupon_rate` | decimal | Yes | Rate as decimal (0.0375 = 3.75%) |
| `maturity_date` | date | Yes | Maturity date |
| `issue_date` | date | No | Issue date |
| `payment_frequency` | enum | No | ANNUAL, SEMI_ANNUAL, QUARTERLY, MONTHLY |
| `day_count_convention` | enum | No | ACT_ACT, ACT_360, ACT_365, 30_360 |

### Swap Fields
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `notional` | decimal | Yes | Notional amount |
| `currency` | string(3) | No | Default: USD |
| `fixed_rate` | decimal | Yes | Fixed rate as decimal |
| `tenor` | string | Yes | Format: "5Y", "18M" |
| `trade_date` | date | Yes | Trade date |
| `maturity_date` | date | Yes | Maturity date |
| `effective_date` | date | No | Effective date |
| `pay_receive` | enum | Yes | PAY or RECEIVE |
| `float_index` | enum | No | SOFR, LIBOR, EURIBOR |
| `payment_frequency` | enum | No | Default: QUARTERLY |

---

## Running Tests

```bash
cd /Users/liuyuxuan/risk_monitor/security_master
PYTHONPATH=. pytest tests/ -v
```

---

## API Documentation

When the service is running, access:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

---

## Acceptance Criteria

- [x] FastAPI application structure created
- [x] SQLAlchemy models for Instrument, Bond, Swap
- [x] Pydantic schemas with validation
- [x] CRUD endpoints for bonds and swaps
- [x] Pagination support
- [x] Input validation and error handling
- [x] Unit tests (15 tests passing)
- [x] Docker container builds and runs
- [x] API responds correctly to requests
- [x] Health check endpoint working

---

## Next Phase

**Phase 3: Market Data Feed** - Python generator to replay historical yield curves into Kafka.

---

**Completed:** 2026-01-29
