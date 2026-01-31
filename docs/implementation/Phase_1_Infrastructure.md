# Phase 1: Infrastructure Setup

**Duration:** Days 1-3
**Status:** 🟢 In Progress
**Prerequisites:** Docker Desktop installed, Python 3.11+

---

## Overview

This phase sets up the foundational infrastructure for the Risk Monitor system:

- **Apache Kafka** (with Zookeeper) - Event streaming backbone
- **PostgreSQL** - Persistent instrument storage
- **Redis** - Risk metrics cache

By the end of this phase, all infrastructure services will be running and verified.

---

## Directory Structure Created

```
risk_monitor/
├── docker-compose.yml       ← Docker services configuration
├── .env                     ← Environment variables
├── .env.example             ← Environment template
├── scripts/
│   ├── init_db.sql          ← PostgreSQL schema + sample data
│   └── verify_services.py   ← Service verification script
├── security_master/         ← Phase 2
├── market_data_feed/        ← Phase 3
├── risk_engine/             ← Phase 4
├── aggregator/              ← Phase 5
├── dashboard/               ← Phase 5
├── data/                    ← Market data files
└── tests/                   ← Integration tests
```

---

## Step 1: Start Infrastructure Services

```bash
# Navigate to project root
cd /Users/liuyuxuan/risk_monitor

# Start all services in detached mode
docker-compose up -d

# Check status
docker-compose ps
```

Expected output:
```
NAME        STATUS              PORTS
kafka       running (healthy)   0.0.0.0:9092->9092/tcp
postgres    running (healthy)   0.0.0.0:5432->5432/tcp
redis       running (healthy)   0.0.0.0:6379->6379/tcp
zookeeper   running (healthy)   0.0.0.0:2181->2181/tcp
```

---

## Step 2: Verify Services

### Option A: Automated Verification

```bash
# Install Python dependencies
pip install psycopg2-binary redis confluent-kafka

# Run verification script
python scripts/verify_services.py
```

### Option B: Manual Verification

**PostgreSQL:**
```bash
docker exec -it postgres psql -U riskuser -d risk_db -c "SELECT COUNT(*) FROM instruments;"
# Expected: 5 (sample instruments)
```

**Redis:**
```bash
docker exec -it redis redis-cli ping
# Expected: PONG
```

**Kafka:**
```bash
docker exec -it kafka kafka-topics --list --bootstrap-server localhost:9092
# Expected: yield_curve_ticks (or empty if not created yet)
```

---

## Step 3: Create Kafka Topic

```bash
docker exec -it kafka kafka-topics --create \
  --topic yield_curve_ticks \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1

# Verify
docker exec -it kafka kafka-topics --describe \
  --topic yield_curve_ticks \
  --bootstrap-server localhost:9092
```

---

## Database Schema

The PostgreSQL schema includes:

### Tables

| Table | Purpose |
|-------|---------|
| `instruments` | Parent table for all instruments (bonds, swaps) |
| `bonds` | Bond-specific attributes (ISIN, coupon, maturity) |
| `interest_rate_swaps` | Swap-specific attributes (fixed rate, tenor, pay/receive) |

### Sample Data

5 sample instruments are pre-loaded:
- 3 Treasury bonds (5Y, 10Y, 30Y)
- 2 Interest rate swaps (5Y, 10Y)

---

## Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Kafka | 9092 | External client connections |
| Kafka | 29092 | Internal Docker network |
| PostgreSQL | 5432 | Database connections |
| Redis | 6379 | Cache connections |
| Zookeeper | 2181 | Kafka coordination |

---

## Common Commands

```bash
# View logs
docker-compose logs -f kafka
docker-compose logs -f postgres

# Stop all services
docker-compose down

# Stop and remove volumes (fresh start)
docker-compose down -v

# Restart a specific service
docker-compose restart kafka
```

---

## Troubleshooting

### Kafka fails to start
```bash
# Check Zookeeper is healthy first
docker-compose logs zookeeper

# Restart in order
docker-compose restart zookeeper
sleep 10
docker-compose restart kafka
```

### PostgreSQL connection refused
```bash
# Wait for healthcheck to pass
docker-compose ps

# Check logs
docker-compose logs postgres
```

### Port already in use
```bash
# Find what's using the port (e.g., 5432)
lsof -i :5432

# Kill the process or change the port in docker-compose.yml
```

---

## Acceptance Criteria

- [x] `docker-compose.yml` created with all services
- [x] PostgreSQL schema created with instruments, bonds, swaps tables
- [x] Sample data loaded (5 instruments)
- [x] Project directory structure created
- [ ] All services start successfully
- [ ] Verification script passes
- [ ] Kafka topic `yield_curve_ticks` created

---

## Next Phase

**Phase 2: Security Master API** - FastAPI REST service for instrument CRUD operations.

---

**Last Updated:** 2026-01-29
