# Architecture Decision Records (ADR)
## Distributed Real-Time Fixed Income & Derivatives Risk Engine

**Document Purpose:** Record key architectural decisions with context, alternatives, and rationale

**Status:** 🟡 Draft for Review

---

## ADR Index

1. [ADR-001: Use Apache Kafka for Event Streaming](#adr-001)
2. [ADR-002: Use QuantLib for Pricing Engine](#adr-002)
3. [ADR-003: Stateless Risk Workers for Horizontal Scaling](#adr-003)
4. [ADR-004: Python Generator Pattern for Market Data Replay](#adr-004)
5. [ADR-005: Redis for Risk Aggregation Cache](#adr-005)
6. [ADR-006: FastAPI for Security Master API](#adr-006)
7. [ADR-007: PostgreSQL for Instrument Data Store](#adr-007)
8. [ADR-008: Dual-Curve Framework for Swap Pricing](#adr-008)
9. [ADR-009: Streamlit for Initial Dashboard](#adr-009)
10. [ADR-010: Docker Compose for Development Orchestration](#adr-010)

---

## ADR-001: Use Apache Kafka for Event Streaming {#adr-001}

**Status:** ✅ Proposed  
**Date:** 2026-01-28  
**Decision Makers:** Architecture Team

### Context

The system needs to distribute market data updates to multiple risk workers in real-time. Requirements:
- Handle 10-100 market ticks per second
- Support horizontal scaling (multiple consumers)
- Guarantee message delivery and ordering
- Enable replay for debugging/testing
- Loose coupling between producer and consumers

### Decision

**We will use Apache Kafka as the central event streaming platform.**

### Alternatives Considered

#### Option 1: Redis Pub/Sub
**Pros:**
- Simple setup
- Low latency (<1ms)
- Already using Redis for cache

**Cons:**
- ❌ No message persistence (if consumer offline, messages lost)
- ❌ No replay capability
- ❌ No consumer groups (manual load balancing)
- ❌ Fire-and-forget (no delivery guarantees)

**Decision:** Rejected due to lack of durability and replay

#### Option 2: RabbitMQ
**Pros:**
- Mature message broker
- Good developer experience
- Supports multiple messaging patterns

**Cons:**
- ❌ Lower throughput than Kafka (100k vs. 1M msg/sec)
- ❌ No built-in message replay
- ❌ More complex routing vs. Kafka topics

**Decision:** Rejected due to throughput limitations and no replay

#### Option 3: Amazon Kinesis
**Pros:**
- Managed service (no ops)
- Similar to Kafka

**Cons:**
- ❌ Cloud-only (vendor lock-in)
- ❌ Higher cost
- ❌ Cannot run locally

**Decision:** Rejected for local development needs

#### **Option 4: Apache Kafka (SELECTED)**
**Pros:**
- ✅ High throughput (millions of messages/sec)
- ✅ Message durability (disk persistence)
- ✅ Consumer groups for automatic load balancing
- ✅ Offset management for replay
- ✅ Widely adopted (strong ecosystem)

**Cons:**
- ❌ Operational complexity (Zookeeper, configuration)
- ❌ Higher resource usage

**Decision:** **APPROVED** - Benefits outweigh complexity for production-grade system

### Consequences

**Positive:**
- Scalable event distribution architecture
- Can replay historical data for testing
- Industry-standard pattern (demonstrates best practices)

**Negative:**
- Requires Zookeeper (adds complexity)
- Learning curve for team
- Higher resource requirements (4GB RAM minimum)

**Neutral:**
- Need to implement monitoring (consumer lag, etc.)

### Implementation Notes

```yaml
# Kafka configuration
KAFKA_TOPIC: yield_curve_ticks
KAFKA_PARTITIONS: 4  # Supports up to 4 parallel consumers
KAFKA_REPLICATION_FACTOR: 1  # Single-broker dev setup
KAFKA_RETENTION_MS: 604800000  # 7 days
```

---

## ADR-002: Use QuantLib for Pricing Engine {#adr-002}

**Status:** ✅ Proposed  
**Date:** 2026-01-28

### Context

Need to price fixed income instruments (bonds, swaps) and calculate sensitivities (DV01, KRD). Requirements:
- Accurate pricing (±0.01 bps vs. Bloomberg)
- Support dual-curve framework (post-2008 standard)
- Handle complex day count conventions
- Calculate numerical sensitivities

### Decision

**We will use QuantLib as the pricing and risk calculation library.**

### Alternatives Considered

#### Option 1: Custom Implementation
**Pros:**
- Full control over logic
- No external dependencies

**Cons:**
- ❌ Months of development time
- ❌ High risk of calculation errors
- ❌ Need to implement curve bootstrapping, day count conventions, etc.
- ❌ Not validated against industry standards

**Decision:** Rejected - too risky and time-consuming

#### Option 2: FinancePy
**Pros:**
- Pure Python (easier installation)
- Modern API

**Cons:**
- ❌ Less mature than QuantLib
- ❌ Smaller community
- ❌ Limited instrument coverage
- ❌ Not used by major financial institutions

**Decision:** Rejected - insufficient maturity

#### Option 3: Bloomberg API (BPIPE)
**Pros:**
- Industry gold standard
- Highly accurate

**Cons:**
- ❌ Expensive ($2000+/month per user)
- ❌ Not open-source
- ❌ Cannot use for demo/portfolio project

**Decision:** Rejected - cost prohibitive for development

#### **Option 4: QuantLib (SELECTED)**
**Pros:**
- ✅ Industry-standard library (used by Bloomberg internally)
- ✅ Proven accuracy
- ✅ Extensive instrument coverage
- ✅ Dual-curve support out-of-the-box
- ✅ Active community (20+ years development)
- ✅ Open-source (BSD license)

**Cons:**
- ❌ C++ library (Python bindings add complexity)
- ❌ Installation can be challenging
- ❌ Steep learning curve

**Decision:** **APPROVED** - Only realistic option for production-grade pricing

### Consequences

**Positive:**
- Accurate, validated pricing
- Demonstrates industry-standard practices
- Extensive documentation and examples

**Negative:**
- Installation complexity (need C++ compiler, Boost)
- Team needs to learn QuantLib API

**Mitigation:**
- Provide Docker images with pre-built QuantLib
- Create wrapper classes to simplify API
- Document common patterns with examples

### Implementation Notes

```python
# Example: Creating a dual-curve swap engine
import QuantLib as ql

# Mutable quotes (updated on market data)
quote_2y = ql.SimpleQuote(0.0410)
quote_5y = ql.SimpleQuote(0.0430)

# Rate helpers
helper_2y = ql.SwapRateHelper(
    ql.QuoteHandle(quote_2y),
    ql.Period(2, ql.Years),
    calendar, frequency, convention, day_count, ibor_index
)

# Bootstrap curve
curve = ql.PiecewiseLogCubicDiscount(
    settlement_date, [helper_2y, helper_5y], day_count
)

# Update quotes when market data arrives
quote_2y.setValue(0.0415)  # Curve auto-recalibrates!
```

---

## ADR-003: Stateless Risk Workers for Horizontal Scaling {#adr-003}

**Status:** ✅ Proposed  
**Date:** 2026-01-28

### Context

Risk workers need to process market data updates and calculate sensitivities. As portfolio grows, need ability to scale processing capacity. Requirements:
- Support 1000+ instruments
- Process 10-100 market ticks/sec
- Enable horizontal scaling (add more workers)

### Decision

**Risk workers will be stateless, caching portfolio in-memory at startup.**

### Alternatives Considered

#### Option 1: Stateful Workers (Each owns subset of portfolio)
**Pros:**
- Lower memory per worker
- Can shard by instrument type

**Cons:**
- ❌ Complex partition assignment
- ❌ Difficult to rebalance
- ❌ Need state coordination (e.g., Zookeeper)

**Decision:** Rejected - too complex

#### **Option 2: Stateless Workers (SELECTED)**
**Pros:**
- ✅ Simple design (each worker identical)
- ✅ Easy to scale (just add more instances)
- ✅ Kafka consumer groups handle load balancing automatically
- ✅ No coordination needed
- ✅ Fast recovery (just restart worker)

**Cons:**
- ❌ Higher memory per worker (each caches full portfolio)
- ❌ Redundant portfolio loading

**Decision:** **APPROVED** - Simplicity and scalability outweigh memory overhead

### Consequences

**Architecture Pattern:**
```
1. Worker Startup:
   ├─ GET /api/v1/instruments (fetch full portfolio)
   ├─ Create QuantLib objects for all instruments
   └─ Cache in-memory

2. Event Processing:
   ├─ Receive market data from Kafka
   ├─ Update curve quotes
   └─ Reprice ALL instruments (but only publish if assigned partition)

3. Scaling:
   ├─ docker-compose scale risk-worker=5
   └─ Kafka consumer group automatically rebalances partitions
```

**Memory Calculation:**
```
Portfolio size: 1000 instruments
Memory per instrument: ~10KB
Total: ~10MB portfolio data
QuantLib overhead: ~500MB
Total per worker: ~600MB

For 5 workers: 3GB total (acceptable)
```

### Implementation Notes

```python
# Worker initialization
def initialize_portfolio():
    response = requests.get("http://security-master:8000/api/v1/instruments")
    instruments = response.json()
    
    portfolio = {}
    for inst in instruments:
        ql_instrument = create_quantlib_instrument(inst)
        portfolio[inst['id']] = ql_instrument
    
    logger.info(f"Loaded {len(portfolio)} instruments")
    return portfolio

# Startup
portfolio = initialize_portfolio()

# Event loop
for message in kafka_consumer:
    update_curves(message)
    
    for inst_id, ql_inst in portfolio.items():
        risk = calculate_risk(ql_inst)
        publish_to_redis(inst_id, risk)
```

---

## ADR-004: Python Generator Pattern for Market Data Replay {#adr-004}

**Status:** ✅ Proposed  
**Date:** 2026-01-28

### Context

Need to simulate real-time market data by replaying historical yield curves. Requirements:
- Memory-efficient (handle large files)
- Timing control (replay at 1x, 10x, 100x speed)
- Simple implementation

### Decision

**Use Python generator pattern to yield market data snapshots.**

### Alternatives Considered

#### Option 1: Load Entire File to Memory
```python
# Load all data upfront
data = pd.read_csv("market_data.csv")  # Could be 100MB+

for row in data.iterrows():
    produce_to_kafka(row)
```

**Pros:**
- Simple Pandas API

**Cons:**
- ❌ High memory usage (entire file in RAM)
- ❌ Slow startup (wait for full load)
- ❌ Doesn't scale to large files

**Decision:** Rejected - memory inefficient

#### **Option 2: Generator Pattern (SELECTED)**
```python
def market_data_generator(file_path):
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield format_message(row)

# Usage
for message in market_data_generator("data.csv"):
    produce_to_kafka(message)
```

**Pros:**
- ✅ Memory-efficient (O(1) - only one row in memory)
- ✅ Natural backpressure (pauses if consumer slow)
- ✅ Clean code (separation of concerns)
- ✅ Lazy evaluation

**Cons:**
- None significant

**Decision:** **APPROVED** - Best practice for streaming data

### Consequences

**Performance:**
- Memory usage: Constant ~50MB (regardless of file size)
- Can handle multi-GB files
- Startup time: Instant (no pre-loading)

**Code Quality:**
- Pythonic pattern
- Easy to test
- Demonstrates advanced Python knowledge

### Implementation Notes

```python
def market_data_generator(file_path: str, replay_speed: float = 1.0):
    """
    Generator that yields market data with timing control.
    
    Args:
        file_path: Path to CSV file
        replay_speed: Speed multiplier (1.0 = real-time, 10.0 = 10x faster)
    
    Yields:
        dict: Market data snapshot
    """
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        prev_timestamp = None
        
        for row in reader:
            current_timestamp = parse_timestamp(row['timestamp'])
            
            # Sleep to maintain original timing
            if prev_timestamp:
                time_delta = (current_timestamp - prev_timestamp).total_seconds()
                time.sleep(time_delta / replay_speed)
            
            yield {
                "timestamp": int(current_timestamp.timestamp() * 1000),
                "rates": {
                    "2Y": float(row['tenor_2y']),
                    "5Y": float(row['tenor_5y']),
                    "10Y": float(row['tenor_10y']),
                    "30Y": float(row['tenor_30y'])
                }
            }
            
            prev_timestamp = current_timestamp
```

---

## ADR-005: Redis for Risk Aggregation Cache {#adr-005}

**Status:** ✅ Proposed  
**Date:** 2026-01-28

### Context

Need to store per-trade risk metrics and compute portfolio-level aggregates for dashboard. Requirements:
- Sub-10ms read latency
- Support atomic updates
- Pub/Sub for notifications
- TTL for stale data

### Decision

**Use Redis as the risk aggregation cache and notification bus.**

### Alternatives Considered

#### Option 1: PostgreSQL
**Pros:**
- Already using for instruments
- ACID guarantees

**Cons:**
- ❌ Too slow (50ms+ for aggregation queries)
- ❌ No pub/sub
- ❌ Overkill for transient data

**Decision:** Rejected - latency too high

#### Option 2: In-Memory (Worker-local)
**Pros:**
- Fastest possible

**Cons:**
- ❌ No shared state (each worker independent)
- ❌ Dashboard can't access
- ❌ No aggregation across workers

**Decision:** Rejected - need centralized state

#### **Option 3: Redis (SELECTED)**
**Pros:**
- ✅ Sub-millisecond latency
- ✅ Rich data structures (hashes, sets)
- ✅ Pub/Sub for notifications
- ✅ TTL for auto-expiry
- ✅ Simple deployment

**Cons:**
- ❌ In-memory only (no persistence)
- ❌ Data lost on restart

**Decision:** **APPROVED** - Acceptable trade-off (risk data is transient)

### Consequences

**Data Model:**
```
# Per-trade risk (Hash)
HSET trade:{id}:risk
  npv "9987562.31"
  dv01 "12500.45"
  krd_2y "1250.00"
  krd_5y "8500.00"
  timestamp "1706486450123"

EXPIRE trade:{id}:risk 3600  # 1 hour TTL

# Portfolio aggregates
SET portfolio:total_dv01 "1250000.00"
HSET portfolio:total_krd
  2Y "125000.00"
  5Y "850000.00"

# Pub/Sub
PUBLISH risk_updates '{"instrument_id": "uuid", "timestamp": 123}'
```

**Performance:**
- Read latency: <1ms
- Write latency: <1ms
- Aggregation (1000 trades): <10ms

---

## ADR-006: FastAPI for Security Master API {#adr-006}

**Status:** ✅ Proposed  
**Date:** 2026-01-28

### Context

Need RESTful API for instrument CRUD operations. Requirements:
- Async support (high concurrency)
- Auto-generated documentation
- Type safety
- Fast development

### Decision

**Use FastAPI as the API framework.**

### Alternatives Considered

#### Option 1: Flask
**Pros:**
- Mature, widely used
- Simple

**Cons:**
- ❌ No async support (WSGI)
- ❌ No auto-documentation
- ❌ Manual validation

**Decision:** Rejected - missing modern features

#### Option 2: Django REST Framework
**Pros:**
- Full-featured (admin, ORM, auth)

**Cons:**
- ❌ Too heavy for simple API
- ❌ Slower than FastAPI

**Decision:** Rejected - overkill

#### **Option 3: FastAPI (SELECTED)**
**Pros:**
- ✅ High performance (async/ASGI)
- ✅ Automatic OpenAPI docs
- ✅ Type safety (Pydantic)
- ✅ Modern Python (type hints)
- ✅ Fast development

**Cons:**
- Less mature than Flask

**Decision:** **APPROVED**

---

## ADR-007-010: [Abbreviated for Brevity]

**ADR-007:** PostgreSQL for persistent instrument storage  
**ADR-008:** Dual-curve framework for post-2008 swap valuation  
**ADR-009:** Streamlit for rapid dashboard development  
**ADR-010:** Docker Compose for local orchestration  

*(Full details available upon request)*

---

## Review Questions

For each ADR, reviewers should consider:

1. **Is the context clear?** Do we understand the problem?
2. **Are alternatives comprehensive?** Did we consider enough options?
3. **Is the rationale sound?** Do benefits justify the decision?
4. **Are consequences understood?** Do we know the trade-offs?
5. **Is implementation feasible?** Can we actually build this?

---

## Approval

| ADR | Reviewer | Status | Comments |
|-----|----------|--------|----------|
| ADR-001 (Kafka) | _______ | ⬜ Pending | |
| ADR-002 (QuantLib) | _______ | ⬜ Pending | |
| ADR-003 (Stateless) | _______ | ⬜ Pending | |
| ADR-004 (Generator) | _______ | ⬜ Pending | |
| ADR-005 (Redis) | _______ | ⬜ Pending | |

**Overall Status:** 🟡 Draft - Awaiting Review
