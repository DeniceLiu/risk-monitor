# Real-Time Fixed Income Risk Monitor

A production-grade, event-driven risk management system that monitors a portfolio of 27 real corporate and government bonds in real-time. Calculates DV01, Key Rate Duration, and NPV using QuantLib dual-curve pricing, with a live Streamlit dashboard.

**Live Demo:** [risk-monitor.ngrok.app](https://risk-monitor.ngrok.app)

---

## Architecture

```
Market Data Feed (Python Generator)
        |
  Apache Kafka (yield_curve_ticks)
        |
  Risk Engine (QuantLib dual-curve pricing)
        |
  Redis (risk metrics cache)
        |
  Streamlit Dashboard (2s auto-refresh)

Security Master (FastAPI + PostgreSQL) <-- instruments loaded at startup
```

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Streaming | Apache Kafka 3.x | Event distribution |
| API | FastAPI | Instrument reference data (Security Master) |
| Database | PostgreSQL 15 | Persistent instrument storage |
| Cache | Redis 7 | Low-latency risk aggregation |
| Pricing | QuantLib 1.32+ | Industry-standard dual-curve framework |
| Dashboard | Streamlit | Real-time visualization |
| Orchestration | Docker Compose | All services containerized |

## Dashboard Features

- **Live streaming indicator** with pulsing badge and data freshness
- **Portfolio summary metrics** with real-time deltas (NPV, DV01, notional)
- **Live DV01 monitor** sparkline chart (5-minute rolling window)
- **Live yield curve** visualization from market data feed
- **Holdings table** with issuer names, sortable columns, CSV export
- **KRD profile** bar chart (2Y, 5Y, 10Y, 30Y tenors)
- **Risk distribution by issuer** showing DV01 concentration
- **Concentration risk analysis** with top-N charts
- **KRD heatmap** across all positions
- **Historical DV01/NPV** time series with dual-axis charts
- **Portfolio filtering** by portfolio, instrument type, currency
- **Excel/CSV export** for offline analysis
- **Dark/light theme** toggle

## Portfolio

27 real bonds from major issuers, seeded automatically:

| Issuer | Bonds | Maturity Range |
|--------|-------|---------------|
| US Treasury | 4 | 2026 - 2053 |
| Apple Inc. | 2 | 2026 - 2029 |
| Microsoft Corp. | 2 | 2027 - 2035 |
| JPMorgan Chase | 2 | 2027 - 2034 |
| Bank of America | 2 | 2026 - 2035 |
| Amazon.com | 2 | 2027 - 2034 |
| Goldman Sachs, Wells Fargo, Alphabet, Coca-Cola, J&J, P&G, Walmart, Verizon, AT&T, Comcast | 1 each | 2027 - 2030 |

Total notional: ~$215M across maturities from 2026 to 2053.

---

## Quick Start

### Prerequisites
- Docker Desktop with Docker Compose

### Run Locally

```bash
git clone https://github.com/DeniceLiu/risk-monitor.git
cd risk-monitor

# Start all 7 services
docker compose up -d --build

# Wait ~60s for all services to become healthy
docker compose ps

# Open dashboard
open http://localhost:8501
```

All 27 bonds are automatically seeded into PostgreSQL on first startup. The market data feed replays yield curve snapshots through Kafka, the risk engine prices all bonds via QuantLib, and the dashboard displays results with 2-second refresh.

### Cloud Deployment (EC2)

The system runs on a `t3.medium` EC2 instance with ngrok for public access. See the deployment setup in the repo history for systemd service configurations.

---

## Services

| Service | Port | Description |
|---------|------|-------------|
| `dashboard` | 8501 | Streamlit real-time UI |
| `security-master` | 8000 | FastAPI instrument API ([docs](http://localhost:8000/docs)) |
| `risk-engine` | - | QuantLib pricing, Kafka consumer, Redis writer |
| `market-data-feed` | - | Yield curve replay into Kafka |
| `kafka` | 9092 | Event streaming |
| `postgres` | 5432 | Instrument storage |
| `redis` | 6379 | Risk metrics cache |

## API

Security Master API docs: http://localhost:8000/docs

Key endpoints:
- `GET /api/v1/instruments` - List all instruments (paginated)
- `POST /api/v1/instruments/bonds` - Create a bond
- `GET /api/v1/portfolios` - List portfolios
- `GET /health` - Health check

---

## Key Concepts

### Dual-Curve Framework
Post-2008 standard: OIS curve for discounting, IBOR curve for forecasting. QuantLib handles curve bootstrapping and recalibration when market data updates arrive.

### DV01 (Dollar Value of 1 Basis Point)
Change in instrument value for a +1bp parallel curve shift. Calculated via bump-and-reprice.

### Key Rate Duration (KRD)
Sensitivity to specific curve tenors (2Y, 5Y, 10Y, 30Y). Identifies which maturity bucket drives portfolio risk.

---

## Project Structure

```
risk_monitor/
├── dashboard/           # Streamlit V2 dashboard
│   └── app/
│       ├── main.py              # Main dashboard layout
│       ├── data.py              # Redis data fetcher
│       ├── config.py            # Settings
│       ├── components/
│       │   ├── charts.py        # Plotly visualizations
│       │   ├── filters.py       # Portfolio/type/currency filters
│       │   ├── alerts.py        # Risk limit alerts
│       │   └── themes.py        # Dark/light theme
│       └── utils/
│           ├── export.py        # Excel export
│           └── issuer_mapping.py # ISIN-to-issuer name mapping
├── security_master/     # FastAPI instrument API
│   └── app/
│       ├── main.py
│       ├── models/              # SQLAlchemy models
│       ├── schemas/             # Pydantic schemas
│       └── routes/              # API routes (instruments, portfolios)
├── risk_engine/         # QuantLib pricing engine
│   └── app/
│       ├── main.py              # Kafka consumer loop
│       ├── pricing/             # Curve building, bond/swap pricing
│       ├── portfolio.py         # Portfolio loader
│       └── consumer/            # Kafka consumer, Redis writer
├── market_data_feed/    # Yield curve data replay
│   └── app/
│       ├── main.py
│       ├── generator.py         # Python generator (O(1) memory)
│       └── producer.py          # Kafka producer
├── data/                # Static market data CSV files
├── scripts/
│   ├── init_db.sql              # Schema + 27 bond seed data
│   └── load_real_bonds.py       # API-based bond loader
├── docker-compose.yml
└── .env.example
```

---

## Performance

| Metric | Target |
|--------|--------|
| End-to-end latency (P95) | < 100ms |
| Curve bootstrapping | < 10ms |
| Bond pricing | < 1ms |
| Risk worker throughput | 100+ instruments/sec |

---

**Built by Denice Liu** | Last Updated: February 2026
