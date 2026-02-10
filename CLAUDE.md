# Risk Monitor Project - Context for Claude

**Project:** Distributed Real-Time Fixed Income & Derivatives Risk Engine
**Status:** COMPLETE - All 5 Phases + V2 Dashboard Enhancements
**Live:** https://risk-monitor.ngrok.app
**Local:** http://localhost:8501
**Repo:** https://github.com/DeniceLiu/risk-monitor

---

## 🎯 What This Project Is

A production-grade risk management system that:
- Monitors portfolios of **Bonds** and **Interest Rate Swaps**
- Calculates real-time risk metrics (**DV01**, **Key Rate Duration**)
- Processes streaming market data via **Apache Kafka**
- Uses **QuantLib** for industry-standard pricing (dual-curve framework)
- Displays results on real-time **Streamlit dashboard**

**Why it matters:** Demonstrates event-driven architecture, microservices, quantitative finance, and real-time data processing.

---

## 🏗️ Architecture (Approved Design)

```
CSV Files → Market Data Feed (Python Generator)
                ↓
          Apache Kafka (Event Bus)
                ↓
    Risk Workers (QuantLib) × N (horizontally scalable)
                ↓
          Redis (Aggregation Cache)
                ↓
          Streamlit Dashboard

Security Master (FastAPI + PostgreSQL) ← Workers load portfolio at startup
```

**Key Patterns:**
- **Event-Driven:** Kafka as central message bus
- **Stateless Workers:** Each caches full portfolio, easy horizontal scaling
- **Dual-Curve Pricing:** OIS (discounting) + IBOR (forecasting)
- **Cache-Aside:** Redis for computed risk metrics

---

## 📋 Implementation Status

### Completed ✅
- [x] System design document created
- [x] Architecture decisions documented (ADRs)
- [x] Design review completed and approved
- [x] Project structure organized
- [x] **Phase 1: Infrastructure Setup** (Completed 2026-01-29)
  - [x] docker-compose.yml with Kafka, Zookeeper, PostgreSQL, Redis
  - [x] PostgreSQL schema with instruments, bonds, swaps tables
  - [x] Sample data loaded (3 bonds, 2 swaps)
  - [x] Kafka topic `yield_curve_ticks` created
  - [x] All services verified healthy

- [x] **Phase 2: Security Master API** (Completed 2026-01-29)
  - [x] FastAPI application with SQLAlchemy ORM
  - [x] Pydantic schemas with validation
  - [x] CRUD endpoints for bonds and swaps
  - [x] 15 unit tests passing
  - [x] Docker container running on port 8000
  - [x] API docs at http://localhost:8000/docs

- [x] **Phase 3: Market Data Feed** (Completed 2026-01-30)
  - [x] Python generator pattern for O(1) memory usage
  - [x] Configurable replay speed (default 10x)
  - [x] Kafka producer with snappy compression
  - [x] Sample yield curve data (61 snapshots)
  - [x] 11 unit tests passing
  - [x] Messages flowing to `yield_curve_ticks` topic

- [x] **Phase 4: Risk Engine** (Completed 2026-01-31)
  - [x] Kafka consumer for yield curve updates
  - [x] QuantLib dual-curve framework
  - [x] Bond and swap pricing
  - [x] DV01 and KRD via bump-and-reprice
  - [x] Redis writer for trade/portfolio risk
  - [x] 8 unit tests passing
  - [x] Consumer group support for horizontal scaling

- [x] **Phase 5: Dashboard** (Completed 2026-01-31)
  - [x] Streamlit real-time visualization
  - [x] Portfolio summary (NPV, DV01, instrument count)
  - [x] Key Rate Duration profile chart
  - [x] Risk distribution by instrument chart
  - [x] Trade-level details table
  - [x] Auto-refresh every 2 seconds
  - [x] Docker container on port 8501

- [x] **V2 Dashboard Enhancements** (Completed 2026-02)
  - [x] Live streaming indicator with pulsing badge
  - [x] Table-first layout with issuer names (ISIN mapping)
  - [x] Inline portfolio selector
  - [x] Live yield curve visualization
  - [x] Live DV01 sparkline monitor
  - [x] Concentration risk analysis charts
  - [x] KRD heatmap
  - [x] Historical DV01/NPV time series
  - [x] Dark/light theme toggle
  - [x] Excel/CSV export
  - [x] Risk alerts with configurable limits

- [x] **Portfolio & Real Bonds** (Completed 2026-02)
  - [x] Portfolio routes in Security Master API
  - [x] 27 real bonds seeded (US Treasury, Apple, Microsoft, JPMorgan, etc.)
  - [x] Portfolio filtering in dashboard
  - [x] Issuer name mapping utility

- [x] **Cloud Deployment** (Completed 2026-02)
  - [x] EC2 t3.medium instance
  - [x] ngrok tunnel at risk-monitor.ngrok.app
  - [x] systemd services for auto-restart

### PROJECT COMPLETE

All 5 phases + V2 enhancements implemented. System is live at risk-monitor.ngrok.app.

---

## 🛠️ Tech Stack (Approved)

| Component | Technology | Purpose |
|-----------|-----------|---------|
| Event Streaming | Apache Kafka 3.x | Distribute market data updates |
| API Framework | FastAPI 0.104+ | Security Master REST API |
| Database | PostgreSQL 15+ | Persistent instrument storage |
| Cache | Redis 7+ | Risk metrics aggregation |
| Pricing | QuantLib 1.32+ | Bond/swap pricing, sensitivities |
| Language | Python 3.11+ | All services |
| Dashboard | Streamlit 1.28+ | Real-time visualization |
| Orchestration | Docker Compose | Local development |

---

## 📂 Project Structure

```
risk_monitor/
├── CLAUDE.md                    ← YOU ARE HERE (context for Claude)
├── START_HERE.md                ← Human-readable project entry
├── README.md                    ← Project overview, quick start
├── .cursorrules                 ← Rules for Cursor IDE (ignore for CLI)
│
├── docs/
│   ├── design/                  ← ✅ APPROVED design documents
│   │   ├── README.md
│   │   ├── System_Design_Document.md          (architecture)
│   │   ├── Architecture_Decision_Records.md   (key decisions)
│   │   └── Design_Review_Checklist.md
│   │
│   └── implementation/          ← To be created per phase
│       ├── Phase_1_Infrastructure.md
│       ├── Phase_2_SecurityMaster.md
│       ├── Phase_3_MarketDataFeed.md
│       ├── Phase_4_RiskEngine.md
│       └── Phase_5_Aggregation.md
│
├── security_master/             ← To be created in Phase 2
├── market_data_feed/            ← To be created in Phase 3
├── risk_engine/                 ← To be created in Phase 4
├── aggregator/                  ← To be created in Phase 5
├── dashboard/                   ← To be created in Phase 5
├── data/                        ← Static market data files
├── tests/                       ← Integration tests
└── docker-compose.yml           ← To be created in Phase 1
```

---

## 🎓 Key Architectural Decisions (from ADRs)

### ADR-001: Apache Kafka for Event Streaming
**Why:** High throughput, message replay, consumer groups for auto-scaling  
**Alternative Considered:** Redis Pub/Sub (rejected: no persistence/replay)

### ADR-002: QuantLib for Pricing
**Why:** Industry standard, dual-curve support, proven accuracy  
**Alternative Considered:** Custom implementation (rejected: too risky/time-consuming)

### ADR-003: Stateless Risk Workers
**Why:** Easy horizontal scaling, simple design, Kafka handles load balancing  
**Trade-off:** Higher memory per worker (acceptable)

### ADR-004: Python Generator Pattern for Data Feed
**Why:** Memory-efficient (O(1)), natural backpressure, lazy evaluation  
**Alternative Considered:** Load all to memory (rejected: memory inefficient)

### ADR-005: Redis for Aggregation Cache
**Why:** Sub-ms latency, rich data structures, pub/sub support  
**Trade-off:** In-memory only (acceptable for transient risk data)

---

## 📖 How to Help with Implementation

### When Starting a New Phase:

1. **Check current phase** (see "Implementation Status" above)
2. **Create implementation document** for that phase:
   - Detailed step-by-step instructions
   - Code examples and boilerplate
   - File structure
   - Testing requirements
   - Acceptance criteria

3. **Implementation pattern:**
   ```
   For Phase X:
   1. Create docs/implementation/Phase_X_[Name].md
   2. Include:
      - Overview and goals
      - Prerequisites
      - Step-by-step instructions with code
      - Testing instructions
      - Acceptance criteria checklist
      - Troubleshooting guide
   ```

4. **Follow backend-first approach:**
   - Infrastructure → Database → API → Processing → UI
   - Each component independently testable

### When Implementing Code:

**Standards:**
- Python 3.11+ with type hints
- Google-style docstrings
- Black formatting (line length 100)
- 80%+ test coverage

**Key Patterns to Follow:**

```python
# 1. Kafka Producer (Data Feed)
def produce_to_kafka(message: dict) -> None:
    producer.produce(
        topic="yield_curve_ticks",
        key=message["curve_type"],
        value=json.dumps(message)
    )
    producer.flush()

# 2. Kafka Consumer (Risk Worker)
for message in consumer:
    data = json.loads(message.value())
    process_market_update(data)
    consumer.commit()  # Manual commit after success

# 3. QuantLib Pattern (Update quotes, not curves)
quote_2y = ql.SimpleQuote(0.0410)
curve = ql.PiecewiseLogCubicDiscount(...)

# When market data arrives:
quote_2y.setValue(0.0415)  # Curve auto-recalibrates!

# 4. Redis Pattern (Store as strings for precision)
redis.hset(f"trade:{id}:risk", mapping={
    "dv01": str(12500.45),  # Not float!
    "npv": str(9987562.31),
    "timestamp": str(int(time.time() * 1000))
})
redis.expire(f"trade:{id}:risk", 3600)  # TTL
```

---

## ⚠️ Important Constraints

### DO (Approved Design)
✅ Use Kafka for event streaming  
✅ Stateless risk workers  
✅ QuantLib for ALL pricing  
✅ FastAPI for APIs  
✅ Redis for caching  
✅ Python generators for data replay  
✅ Docker Compose for orchestration  

### DON'T (Not Approved)
❌ Use RabbitMQ or Redis Pub/Sub instead of Kafka  
❌ Make workers stateful  
❌ Implement custom pricing algorithms  
❌ Use Flask/Django instead of FastAPI  
❌ Load entire CSV files into memory  
❌ Deviate from approved architecture without discussion  

---

## 🎯 Performance Targets

| Metric | Target | Why |
|--------|--------|-----|
| End-to-end latency (P95) | < 100ms | Traders need sub-second updates |
| Curve bootstrapping | < 10ms | Fast recalibration on market tick |
| Bond pricing | < 1ms | High-frequency portfolio repricing |
| Risk worker throughput | 100 inst/sec | Support 1500-instrument portfolio |
| API response (GET) | < 50ms | Smooth user experience |

---

## 📚 Reference Documents

- `docs/design/System_Design_Document.md` - Complete architecture
- `docs/design/Architecture_Decision_Records.md` - Key decisions (ADRs)
- `README.md` - Quick start and overview

---

## 🔑 Quick Command Reference

```bash
# Check what's already running
docker ps

# Start all services
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f [service-name]

# Stop everything
docker-compose down

# Kafka: List topics
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092

# PostgreSQL: Connect
docker exec -it postgres psql -U riskuser -d risk_db

# Redis: Connect
docker exec -it redis redis-cli

# Run tests
pytest tests/ -v --cov
```

---

## 📊 Success Criteria (Overall)

Project complete when:
- ✅ All 5 phases implemented
- ✅ Market data flows through Kafka at 10 msg/sec
- ✅ Risk workers calculate DV01/KRD accurately
- ✅ Dashboard displays real-time portfolio risk
- ✅ End-to-end latency < 100ms (P95)
- ✅ Bond pricing within $0.01 of Bloomberg
- ✅ Swap pricing within 0.01bps of Bloomberg
- ✅ All tests passing (80%+ coverage)
- ✅ System runs 1 hour without errors

---

## 🎓 Financial Concepts (Quick Reference)

**DV01 (Dollar Value of 1 Basis Point):**
- Change in instrument value for +1bp parallel curve shift
- Example: DV01 = $12,500 means lose $12,500 if rates ↑ 1bp

**Key Rate Duration (KRD):**
- Sensitivity to specific curve tenors (2Y, 5Y, 10Y, 30Y)
- Identifies which maturity drives risk
- Used for targeted hedging

**Dual-Curve Framework:**
- Post-2008 market standard
- **OIS Curve:** Discounting (risk-free rate)
- **IBOR Curve:** Forecasting (benchmark rate with credit risk)
- Necessary for accurate swap valuation

**Bump-and-Reprice:**
- Numerical method for calculating sensitivities
- Bump rate by 1bp → Reprice → Measure difference
- More stable than analytical derivatives

---

**Last Updated:** 2026-02-09
**Status:** COMPLETE - All phases + V2 + Cloud deployed
**Live URL:** https://risk-monitor.ngrok.app
