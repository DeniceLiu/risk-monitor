# Phase 3: Market Data Feed

**Duration:** Days 7-9
**Status:** ✅ Complete
**Prerequisites:** Phase 1 infrastructure (Kafka) running

---

## Overview

The Market Data Feed replays historical yield curve data into Kafka using Python's generator pattern for memory-efficient O(1) streaming. It simulates real-time market data updates that the Risk Engine will consume.

---

## Directory Structure

```
market_data_feed/
├── Dockerfile
├── requirements.txt
├── app/
│   ├── __init__.py
│   ├── main.py          ← Entry point
│   ├── config.py        ← Settings
│   ├── generator.py     ← Generator pattern implementation
│   └── producer.py      ← Kafka producer
└── tests/
    ├── __init__.py
    └── test_generator.py
```

---

## Key Design: Generator Pattern

The generator pattern provides O(1) memory usage regardless of file size:

```python
def market_data_generator(file_path: str, replay_speed: float = 1.0):
    """
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

---

## Kafka Message Format

```json
{
  "timestamp": 1769590800000,
  "curve_date": "2026-01-28",
  "curve_type": "USD_SOFR",
  "rates": {
    "1M": 0.0525,
    "3M": 0.0520,
    "6M": 0.0510,
    "1Y": 0.0480,
    "2Y": 0.0420,
    "5Y": 0.0410,
    "10Y": 0.0420,
    "30Y": 0.0450
  }
}
```

---

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `KAFKA_BOOTSTRAP_SERVERS` | `localhost:9092` | Kafka broker |
| `KAFKA_TOPIC` | `yield_curve_ticks` | Topic name |
| `REPLAY_SPEED` | `1.0` | Speed multiplier (10.0 = 10x faster) |
| `DATA_FILE` | `data/yield_curves.csv` | Source file |
| `LOOP_FOREVER` | `true` | Restart when file ends |
| `LOG_LEVEL` | `INFO` | Logging level |

---

## Sample Data

Located at `data/yield_curves.csv`:
- 61 yield curve snapshots
- 1-minute intervals
- USD SOFR curve with tenors: 1M, 3M, 6M, 1Y, 2Y, 3Y, 5Y, 7Y, 10Y, 20Y, 30Y
- Simulates market movement with rate changes

---

## Usage

### Start with Docker Compose
```bash
# Start at 10x speed
REPLAY_SPEED=10.0 docker-compose up -d market-data-feed

# Check logs
docker-compose logs -f market-data-feed
```

### Verify Messages
```bash
# Consume from Kafka
docker exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic yield_curve_ticks \
  --max-messages 5
```

### Run Locally
```bash
cd market_data_feed
pip install -r requirements.txt

# Set environment
export KAFKA_BOOTSTRAP_SERVERS=localhost:9092
export REPLAY_SPEED=10.0
export DATA_FILE=../data/yield_curves.csv

python -m app.main
```

---

## Tests

```bash
cd /Users/liuyuxuan/risk_monitor/market_data_feed
PYTHONPATH=. pytest tests/ -v
```

11 tests covering:
- Timestamp parsing (ISO, date-only, Unix ms)
- Message formatting
- Generator behavior
- Error handling

---

## Acceptance Criteria

- [x] Python generator pattern for memory-efficient replay
- [x] Configurable replay speed
- [x] Kafka producer with proper configuration
- [x] Sample yield curve data (61 snapshots)
- [x] Loop forever mode for continuous testing
- [x] 11 unit tests passing
- [x] Docker container builds and runs
- [x] Messages published to Kafka topic

---

## Next Phase

**Phase 4: Risk Engine** - QuantLib-based pricing engine that consumes yield curve updates from Kafka and calculates DV01/KRD.

---

**Completed:** 2026-01-30
