# System Design Document (SDD)
## Distributed Real-Time Fixed Income & Derivatives Risk Engine

**Version:** 1.0 (Draft for Review)  
**Date:** January 28, 2026  
**Status:** 🟡 Awaiting Review  
**Reviewers:** Technical Lead, Architecture Team

---

## Document Purpose

This System Design Document presents the **architectural design** for review and approval. After approval, detailed implementation documents will be generated for each phase.

**Review Focus Areas:**
- ✅ Architecture patterns and technology choices
- ✅ Component boundaries and responsibilities
- ✅ Data flow and integration points
- ✅ Scalability and performance approach
- ✅ Risk mitigation strategies

---

## 1. System Overview

### 1.1 High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                        RISK MONITORING SYSTEM                        │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┐         ┌──────────────────────────────────────┐
│  Static Market   │ ──────> │  Market Data Feed (Python)           │
│  Data Files      │         │  • Generator Pattern                 │
│  (CSV/JSON)      │         │  • Configurable Replay Speed         │
└──────────────────┘         └──────────────────────────────────────┘
                                            │
                                            ▼
                             ┌──────────────────────────────────────┐
                             │  Apache Kafka                        │
                             │  Topic: yield_curve_ticks            │
                             │  • Event Streaming Bus               │
                             │  • Consumer Groups                   │
                             └──────────────────────────────────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
              ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
              │  Risk Worker 1  │  │  Risk Worker 2  │  │  Risk Worker N  │
              │  (Python +      │  │  (Python +      │  │  (Python +      │
              │   QuantLib)     │  │   QuantLib)     │  │   QuantLib)     │
              └─────────────────┘  └─────────────────┘  └─────────────────┘
                        │                   │                   │
                        └───────────────────┼───────────────────┘
                                            ▼
                             ┌──────────────────────────────────────┐
                             │  Redis                               │
                             │  • Per-Trade Risk Cache              │
                             │  • Portfolio Aggregates              │
                             │  • Pub/Sub Notifications             │
                             └──────────────────────────────────────┘
                                            │
                        ┌───────────────────┼───────────────────┐
                        ▼                   ▼                   ▼
              ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
              │   Aggregator    │  │   Dashboard     │  │   API Gateway   │
              │   Service       │  │   (Streamlit)   │  │   (Future)      │
              └─────────────────┘  └─────────────────┘  └─────────────────┘

┌──────────────────────────────────────────────────────────────────────┐
│  Security Master (FastAPI)                                           │
│  • PostgreSQL Database                                               │
│  • Instrument Reference Data (Bonds, Swaps)                         │
│  • REST API for CRUD Operations                                     │
└──────────────────────────────────────────────────────────────────────┘
         ▲
         │ (Startup: Load Portfolio)
         │
    Risk Workers
```

### 1.2 Key Design Principles

| Principle | Implementation | Benefit |
|-----------|---------------|---------|
| **Event-Driven** | Kafka as central message bus | Loose coupling, scalability |
| **Stateless Workers** | Risk workers cache portfolio in-memory | Horizontal scalability |
| **Separation of Concerns** | Independent microservices | Independent deployment, testing |
| **Single Source of Truth** | Security Master for instrument data | Data consistency |
| **Cache-Aside Pattern** | Redis for computed risk metrics | Low-latency reads |

---

## 2. Component Design

### 2.1 Component Overview

| Component | Type | Language | Responsibility | Scalability |
|-----------|------|----------|----------------|-------------|
| **Market Data Feed** | Producer | Python 3.11 | Replay historical curves into Kafka | Single instance (sufficient) |
| **Security Master** | REST API | Python/FastAPI | Instrument reference data CRUD | Horizontal (stateless) |
| **Risk Worker** | Consumer | Python/QuantLib | Price instruments, calculate DV01/KRD | Horizontal (consumer group) |
| **Aggregator** | Service | Python | Sum portfolio-level risk | Single instance (sufficient) |
| **Dashboard** | Web UI | Python/Streamlit | Real-time visualization | Multiple instances |
| **PostgreSQL** | Database | SQL | Persistent instrument storage | Single primary (read replicas optional) |
| **Redis** | Cache | In-memory | Risk metrics cache + pub/sub | Single instance (cluster optional) |
| **Kafka** | Message Bus | JVM | Event streaming backbone | Cluster (1 broker for dev) |

---

### 2.2 Component: Market Data Feed

**Purpose:** Simulate real-time market data by replaying historical yield curves

#### 2.2.1 Design Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Implementation Pattern** | Python Generator | Memory-efficient, natural backpressure | Load all to memory (rejected: OOM risk) |
| **Data Source** | Static CSV files | No vendor costs, reproducible testing | Bloomberg API (too expensive for demo) |
| **Replay Speed** | Configurable multiplier | Support multiple test scenarios | Fixed rate (rejected: inflexible) |
| **Message Format** | JSON | Human-readable, schema evolution | Avro (overkill for initial version) |

#### 2.2.2 Technical Specifications

```python
# Core Generator Pattern
def market_data_generator(file_path: str, replay_speed: float = 1.0):
    """
    Yields market data snapshots with timing control.
    
    Memory: O(1) - only one row in memory at a time
    Timing: Sleeps between yields to simulate real-time
    """
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        prev_timestamp = None
        
        for row in reader:
            current_timestamp = parse_timestamp(row['timestamp'])
            
            if prev_timestamp:
                time_delta = (current_timestamp - prev_timestamp).total_seconds()
                sleep_duration = time_delta / replay_speed
                time.sleep(sleep_duration)
            
            yield format_kafka_message(row)
            prev_timestamp = current_timestamp
```

**Output Schema:**
```json
{
  "timestamp": 1706486400000,      // Unix epoch milliseconds
  "curve_date": "2026-01-28",
  "curve_type": "USD_SOFR",
  "rates": {
    "2Y": 0.0410,
    "5Y": 0.0430,
    "10Y": 0.0450,
    "30Y": 0.0470
  }
}
```

**Performance Targets:**
- Replay speed accuracy: ±10ms jitter
- Memory usage: <50MB regardless of file size
- Throughput at max speed: >1000 msg/sec

---

### 2.3 Component: Security Master

**Purpose:** RESTful API providing the "Golden Source" of instrument reference data

#### 2.3.1 Design Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Framework** | FastAPI | Async support, auto-docs, type safety | Flask (no async), Django (too heavy) |
| **Database** | PostgreSQL | ACID, mature, JSON support | MongoDB (schema flexibility not needed) |
| **ORM** | SQLAlchemy | Industry standard, type-safe | Raw SQL (harder to maintain) |
| **API Style** | REST | Widely understood, HTTP standard | GraphQL (overkill for simple CRUD) |

#### 2.3.2 Data Model (Simplified)

```sql
-- Parent table for all instruments
CREATE TABLE instruments (
    id UUID PRIMARY KEY,
    instrument_type VARCHAR(10),  -- 'BOND' or 'SWAP'
    notional DECIMAL(18, 2),
    currency VARCHAR(3),
    created_at TIMESTAMP
);

-- Child table for bonds
CREATE TABLE bonds (
    instrument_id UUID REFERENCES instruments(id),
    isin VARCHAR(12) UNIQUE,
    coupon_rate DECIMAL(8, 6),
    maturity_date DATE,
    payment_frequency VARCHAR(20),
    day_count_convention VARCHAR(20)
);

-- Child table for swaps
CREATE TABLE interest_rate_swaps (
    instrument_id UUID REFERENCES instruments(id),
    fixed_rate DECIMAL(8, 6),
    tenor VARCHAR(10),
    trade_date DATE,
    maturity_date DATE,
    pay_receive VARCHAR(10)
);
```

**Key API Endpoints:**
- `POST /api/v1/instruments/bonds` - Create bond
- `POST /api/v1/instruments/swaps` - Create swap
- `GET /api/v1/instruments` - List all instruments (paginated)
- `GET /api/v1/instruments/{id}` - Get by ID
- `DELETE /api/v1/instruments/{id}` - Delete instrument

**Performance Targets:**
- GET single instrument: <10ms
- POST new instrument: <50ms
- List 100 instruments: <50ms

---

### 2.4 Component: Risk Worker

**Purpose:** Consume market data updates, price instruments, calculate sensitivities

#### 2.4.1 Design Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Pricing Library** | QuantLib | Industry standard, dual-curve support | Custom implementation (too complex) |
| **Consumer Pattern** | Kafka Consumer Group | Automatic load balancing | Manual partition assignment (complex) |
| **Portfolio Loading** | In-memory cache | Fast pricing, no DB queries per tick | Query DB per instrument (too slow) |
| **Sensitivity Method** | Bump-and-reprice | Numerically stable, accurate | Analytical Greeks (not available for all) |

#### 2.4.2 Processing Flow

```
1. STARTUP PHASE:
   ├─ Load portfolio from Security Master API
   ├─ Create QuantLib instrument objects
   └─ Initialize Quote objects for curve rates

2. EVENT LOOP:
   ├─ Poll Kafka for yield curve update
   ├─ Update Quote objects (triggers curve recalibration)
   ├─ FOR EACH instrument in portfolio:
   │   ├─ Calculate NPV
   │   ├─ Calculate DV01 (parallel bump)
   │   ├─ Calculate KRD (tenor-specific bumps)
   │   └─ Write to Redis
   ├─ Commit Kafka offset
   └─ Log processing metrics
```

#### 2.4.3 Dual-Curve Framework

**Mathematical Foundation:**

Post-2008 market practice separates:
- **Discounting Curve (OIS)**: Used to discount all cash flows to present value
- **Forecasting Curve (IBOR)**: Used to project future floating rate fixings

```python
# QuantLib Implementation (Simplified)
import QuantLib as ql

# Step 1: Create mutable quotes (updated when market data arrives)
quote_2y = ql.SimpleQuote(0.0410)
quote_5y = ql.SimpleQuote(0.0430)
quote_10y = ql.SimpleQuote(0.0450)

# Step 2: Wrap in handles
quote_handle_2y = ql.QuoteHandle(quote_2y)
quote_handle_5y = ql.QuoteHandle(quote_5y)
quote_handle_10y = ql.QuoteHandle(quote_10y)

# Step 3: Create rate helpers
helper_2y = ql.SwapRateHelper(quote_handle_2y, ql.Period(2, ql.Years), ...)
helper_5y = ql.SwapRateHelper(quote_handle_5y, ql.Period(5, ql.Years), ...)
helper_10y = ql.SwapRateHelper(quote_handle_10y, ql.Period(10, ql.Years), ...)

# Step 4: Bootstrap curves
ois_curve = ql.PiecewiseLogCubicDiscount(settlement_date, [helper_2y, helper_5y, helper_10y], ql.Actual360())
ibor_curve = ql.PiecewiseLogCubicDiscount(settlement_date, [helper_2y, helper_5y, helper_10y], ql.Actual360())

# Step 5: When new market data arrives, just update quotes
quote_2y.setValue(0.0415)  # QuantLib automatically recalibrates curves!
```

**Performance Targets:**
- Curve bootstrapping: <10ms
- Bond pricing: <1ms per instrument
- Swap pricing: <2ms per instrument
- DV01 calculation: <10ms per instrument
- KRD calculation: <50ms per instrument

---

### 2.5 Component: Aggregator

**Purpose:** Sum individual trade risks into portfolio-level aggregates

#### 2.5.1 Design Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Aggregation Trigger** | Redis Pub/Sub | Event-driven, low latency | Polling Redis (wasteful) |
| **Aggregation Strategy** | Full recalculation | Simple, always accurate | Incremental (risk of drift) |
| **Update Frequency** | On every trade update | Real-time dashboard | Batch (e.g., every 5s) |

#### 2.5.2 Aggregation Logic

```python
def recalculate_portfolio_aggregates():
    """
    Scan all trade risks and compute portfolio totals.
    Complexity: O(N) where N = number of trades
    """
    trade_keys = redis.keys("trade:*:risk")
    
    totals = {
        "dv01": 0.0,
        "npv": 0.0,
        "krd": {"2Y": 0.0, "5Y": 0.0, "10Y": 0.0, "30Y": 0.0}
    }
    
    # Fetch all trade risks in pipeline (single round-trip)
    pipe = redis.pipeline()
    for key in trade_keys:
        pipe.hgetall(key)
    
    results = pipe.execute()
    
    # Sum metrics
    for trade_risk in results:
        totals["dv01"] += float(trade_risk.get(b'dv01', 0))
        totals["npv"] += float(trade_risk.get(b'npv', 0))
        for tenor in ["2Y", "5Y", "10Y", "30Y"]:
            totals["krd"][tenor] += float(trade_risk.get(f'krd_{tenor.lower()}'.encode(), 0))
    
    # Write aggregates atomically
    redis.set("portfolio:total_dv01", totals["dv01"])
    redis.set("portfolio:total_npv", totals["npv"])
    redis.hset("portfolio:total_krd", mapping=totals["krd"])
```

**Performance Targets:**
- Aggregation latency: <10ms for 1000 trades
- Redis write latency: <1ms
- Pub/Sub notification delivery: <5ms

---

### 2.6 Component: Dashboard

**Purpose:** Real-time visualization of portfolio risk metrics

#### 2.6.1 Design Decisions

| Decision | Choice | Rationale | Alternatives Considered |
|----------|--------|-----------|------------------------|
| **Framework** | Streamlit | Rapid development, Python-native | React (longer dev time), Grafana (less custom) |
| **Update Mechanism** | Polling Redis | Simple, reliable | WebSockets (more complex) |
| **Refresh Rate** | 2 seconds | Balance freshness vs. load | 1s (too aggressive), 5s (too stale) |

#### 2.6.2 Dashboard Layout

```
┌─────────────────────────────────────────────────────────────┐
│  Fixed Income Risk Monitor                    [●Live]       │
├─────────────────────────────────────────────────────────────┤
│  Last Update: 2026-01-28 10:15:30 (2s ago)                 │
├─────────────────────────────────────────────────────────────┤
│  PORTFOLIO SUMMARY                                          │
│  ┌──────────────┬──────────────┬──────────────┐            │
│  │ Instruments  │ Total NPV    │ Total DV01   │            │
│  │ 1,500        │ $995M        │ $1.25M       │            │
│  └──────────────┴──────────────┴──────────────┘            │
├─────────────────────────────────────────────────────────────┤
│  DV01 BY TYPE                                               │
│  Bonds (1,000):   $750K  ██████████████████                │
│  Swaps (500):     $500K  ████████████                      │
├─────────────────────────────────────────────────────────────┤
│  KEY RATE DURATION                                          │
│       ██                                                    │
│       ██                                                    │
│  ██   ██   ██   ██                                         │
│  2Y   5Y   10Y  30Y                                        │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. Data Flow

### 3.1 End-to-End Flow

```
T=0ms:   Market Data Feed publishes curve update to Kafka
         ↓
T=5ms:   Risk Worker 1 receives message from Kafka
         ├─ Updates QuantLib Quote objects
         └─ Curves automatically recalibrate
         ↓
T=15ms:  Risk Worker 1 prices 750 instruments
         └─ Calculates NPV, DV01, KRD for each
         ↓
T=20ms:  Risk Worker 1 writes 750 results to Redis
         └─ Publishes notification to "risk_updates" channel
         ↓
T=25ms:  Aggregator receives notification
         ├─ Scans all trade risks
         ├─ Sums portfolio totals
         └─ Updates aggregate keys in Redis
         ↓
T=30ms:  Dashboard polls Redis on next refresh cycle
         └─ Renders updated metrics
         ↓
TOTAL:   ~30-50ms end-to-end latency (target: <100ms P95)
```

### 3.2 Failure Scenarios

| Failure | Detection | Recovery | Data Loss |
|---------|-----------|----------|-----------|
| **Kafka broker down** | Connection timeout | Retry with backoff | None (buffered) |
| **Risk worker crash** | Consumer group rebalance | Other workers pick up partitions | None (Kafka retains) |
| **Redis unavailable** | Connection error | Log failure, continue processing | Risk data (TTL=1hr anyway) |
| **Security Master down** | Startup fails | Use cached portfolio, retry | None (read-only) |
| **QuantLib pricing error** | Exception during NPV calc | Log error, skip trade, continue | Single trade (logged) |

---

## 4. Technology Stack Justification

### 4.1 Core Technologies

#### 4.1.1 Apache Kafka

**Chosen for:**
- ✅ High throughput (millions of messages/sec)
- ✅ Consumer groups for automatic load balancing
- ✅ Message durability (disk persistence)
- ✅ Replay capability (offset management)

**Trade-offs:**
- ❌ Operational complexity (Zookeeper dependency)
- ❌ Higher resource usage vs. Redis Pub/Sub

**Alternatives Considered:**
- RabbitMQ: Less throughput, no replay
- Redis Streams: Less mature ecosystem
- AWS Kinesis: Cloud-only, vendor lock-in

---

#### 4.1.2 QuantLib

**Chosen for:**
- ✅ Industry-standard pricing library
- ✅ Dual-curve support out-of-the-box
- ✅ Extensive instrument coverage
- ✅ Proven accuracy (used by Bloomberg)

**Trade-offs:**
- ❌ C++ with Python bindings (installation complexity)
- ❌ Learning curve for non-quants

**Alternatives Considered:**
- Custom implementation: Too complex, error-prone
- FinancePy: Less mature, limited instrument support
- Bloomberg API: Expensive, not open-source

---

#### 4.1.3 FastAPI

**Chosen for:**
- ✅ High performance (async support)
- ✅ Automatic OpenAPI documentation
- ✅ Type safety with Pydantic
- ✅ Modern Python features

**Trade-offs:**
- ❌ Less mature than Flask/Django

**Alternatives Considered:**
- Flask: No async, no auto-docs
- Django: Too heavy for simple API
- Node.js: Team expertise in Python

---

#### 4.1.4 Redis

**Chosen for:**
- ✅ Sub-millisecond latency
- ✅ Rich data structures (hashes, pub/sub)
- ✅ Simple deployment
- ✅ Widely understood

**Trade-offs:**
- ❌ In-memory only (volatile storage)

**Alternatives Considered:**
- Memcached: No data structures, no pub/sub
- DynamoDB: Higher latency, more expensive

---

#### 4.1.5 PostgreSQL

**Chosen for:**
- ✅ ACID compliance
- ✅ JSON support
- ✅ Mature, battle-tested
- ✅ Strong community

**Trade-offs:**
- ❌ Not as scalable as NoSQL for writes

**Alternatives Considered:**
- MongoDB: Schema flexibility not needed
- MySQL: PostgreSQL has better JSON support
- Cassandra: Overkill for workload

---

### 4.2 Programming Language: Python 3.11+

**Chosen for:**
- ✅ QuantLib Python bindings
- ✅ Rich data science ecosystem (Pandas, NumPy)
- ✅ FastAPI and Streamlit support
- ✅ Team expertise

**Trade-offs:**
- ❌ Slower than C++/Java for compute-intensive tasks
- ❌ GIL limits multi-threading (mitigated by multi-process)

**Alternatives Considered:**
- Java: Better Kafka integration, but QuantLib bindings less mature
- C++: Best performance, but slower development
- Go: Fast, but limited quant libraries

---

## 5. Non-Functional Requirements

### 5.1 Performance Requirements

| Metric | Target | Rationale | Measurement Method |
|--------|--------|-----------|-------------------|
| **End-to-end latency (P95)** | <100ms | Traders need sub-second updates | Timestamp tracking from Kafka to Redis |
| **Risk worker throughput** | 100 instruments/sec | Support 1500-trade portfolio | Benchmark with sample portfolio |
| **Curve bootstrapping** | <10ms | Fast recalibration on market update | QuantLib profiling |
| **API response time (GET)** | <50ms | Smooth user experience | HTTP request logging |
| **Dashboard refresh** | 2 seconds | Balance freshness vs. load | Streamlit config |

### 5.2 Scalability Requirements

| Dimension | Target | Strategy |
|-----------|--------|----------|
| **Portfolio size** | 10,000 instruments | Stateless risk workers, horizontal scaling |
| **Market data rate** | 100 ticks/sec | Kafka consumer group parallelism |
| **Concurrent users** | 50 | Stateless API, load balancer |
| **Historical data** | 1 year | Kafka retention policy |

### 5.3 Reliability Requirements

| Requirement | Target | Implementation |
|-------------|--------|----------------|
| **System availability** | 99.9% | Health checks, auto-restart |
| **Data durability** | 99.999% | Kafka replication, PostgreSQL backups |
| **Calculation accuracy** | ±0.01 bps | Validation against Bloomberg |
| **Recovery time** | <5 minutes | Stateless design, fast startup |

---

## 6. Deployment Architecture

### 6.1 Development Environment (Docker Compose)

```yaml
# Simplified docker-compose.yml
services:
  zookeeper:
    image: confluentinc/cp-zookeeper:7.5.0
  
  kafka:
    image: confluentinc/cp-kafka:7.5.0
    depends_on: [zookeeper]
  
  postgres:
    image: postgres:15-alpine
  
  redis:
    image: redis:7-alpine
  
  security-master:
    build: ./security_master
    depends_on: [postgres]
  
  market-data-feed:
    build: ./market_data_feed
    depends_on: [kafka]
  
  risk-worker:
    build: ./risk_engine
    depends_on: [kafka, redis, security-master]
    deploy:
      replicas: 2  # Scale horizontally
  
  aggregator:
    build: ./aggregator
    depends_on: [redis]
  
  dashboard:
    build: ./dashboard
    depends_on: [redis]
```

### 6.2 Resource Requirements

| Service | CPU | Memory | Storage | Notes |
|---------|-----|--------|---------|-------|
| Kafka + Zookeeper | 2 cores | 4GB | 20GB | Message retention |
| PostgreSQL | 1 core | 2GB | 10GB | Instrument data |
| Redis | 1 core | 2GB | - | In-memory |
| Security Master | 0.5 cores | 512MB | - | Stateless |
| Risk Worker (each) | 2 cores | 2GB | - | QuantLib heavy |
| Aggregator | 0.5 cores | 512MB | - | Lightweight |
| Dashboard | 0.5 cores | 512MB | - | Streamlit |
| **TOTAL (2 workers)** | **10 cores** | **16GB** | **30GB** | Development setup |

---

## 7. Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **QuantLib installation fails** | High | High | Provide Docker images, conda install, detailed docs |
| **Kafka operational complexity** | Medium | High | Use managed Kafka (Confluent Cloud) for prod |
| **Calculation accuracy issues** | Medium | Critical | Extensive validation vs. Bloomberg, unit tests |
| **Performance targets not met** | Low | High | Early prototyping, profiling, optimization |
| **Scope creep (options, etc.)** | High | Medium | Strict MVP scope, deferred backlog |

---

## 8. Open Questions for Review

### 8.1 Architecture Decisions

1. **Kafka vs. Simpler Message Queue?**
   - Current: Apache Kafka
   - Alternative: Redis Streams or RabbitMQ
   - Trade-off: Operational complexity vs. scalability
   - **Question:** Is Kafka overkill for initial scale?

2. **Aggregation Strategy?**
   - Current: Full recalculation on every update
   - Alternative: Incremental updates (track deltas)
   - Trade-off: Simplicity vs. performance at scale
   - **Question:** When to optimize to incremental?

3. **Dashboard Technology?**
   - Current: Streamlit (Python)
   - Alternative: React + REST API
   - Trade-off: Development speed vs. customization
   - **Question:** Is Streamlit sufficient for demo?

### 8.2 Scope Clarifications

4. **Multi-Currency Support?**
   - Current: Single currency (USD) for V1
   - Question: Should we support EUR/GBP now?

5. **Real-Time vs. Batch?**
   - Current: Real-time (every market tick)
   - Alternative: Batch (every 5 seconds)
   - Question: Is true real-time necessary?

6. **Historical Risk Storage?**
   - Current: Redis with 1-hour TTL (no history)
   - Alternative: Time-series DB for risk history
   - Question: Do we need historical risk trends?

---

## 9. Next Steps (After Approval)

Once this design is reviewed and approved:

1. ✅ **Create Detailed Implementation Documents**
   - Phase 1: Infrastructure & Database
   - Phase 2: Security Master API
   - Phase 3: Market Data Feed
   - Phase 4: Risk Engine
   - Phase 5: Aggregation & Dashboard

2. ✅ **Begin Phase-by-Phase Implementation**
   - Backend-first approach
   - Each phase independently testable
   - Clear acceptance criteria per phase

3. ✅ **Establish Testing Strategy**
   - Unit tests per component
   - Integration tests per phase
   - End-to-end validation

---

## 10. Review Sign-Off

| Reviewer | Role | Status | Comments | Date |
|----------|------|--------|----------|------|
| _________ | Technical Lead | ⬜ Pending | | |
| _________ | Architecture Team | ⬜ Pending | | |
| _________ | Risk SME | ⬜ Pending | | |

**Approval Criteria:**
- [ ] Architecture pattern appropriate for requirements
- [ ] Technology choices justified
- [ ] Performance targets achievable
- [ ] Risks identified and mitigated
- [ ] Scope clearly defined

---

**Document Status:** 🟡 Draft - Awaiting Review  
**Next Revision:** After review feedback incorporated  
**Target Approval Date:** [TBD]
