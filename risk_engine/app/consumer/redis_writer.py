"""Redis writer for risk metrics."""

import json
import logging
import time
from typing import Dict, Any, Optional

import redis

from app.pricing.risk import RiskMetrics

logger = logging.getLogger(__name__)


class RedisWriter:
    """Writes risk metrics to Redis."""

    def __init__(self, host: str, port: int, ttl: int = 3600):
        """Initialize Redis connection.

        Args:
            host: Redis host
            port: Redis port
            ttl: Time-to-live for risk data in seconds
        """
        self.ttl = ttl
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

        # Verify connection
        self.client.ping()
        logger.info(f"Redis connected: {host}:{port}")

    def write_risk(self, metrics: RiskMetrics, curve_timestamp: int) -> None:
        """Write risk metrics to Redis.

        Storage pattern:
        - trade:{id}:risk -> hash with npv, dv01, krd values
        - trade:{id}:updated -> timestamp of last update

        Args:
            metrics: Risk metrics to write
            curve_timestamp: Timestamp of the curve data
        """
        key = f"trade:{metrics.instrument_id}:risk"

        # Flatten KRD to individual fields
        data = {
            "npv": str(metrics.npv),
            "dv01": str(metrics.dv01),
            "curve_timestamp": str(curve_timestamp),
            "updated_at": str(int(time.time() * 1000)),
        }

        # Add KRD values
        for tenor, value in metrics.krd.items():
            data[f"krd_{tenor.lower()}"] = str(value)

        # Write to Redis
        pipe = self.client.pipeline()
        pipe.hset(key, mapping=data)
        pipe.expire(key, self.ttl)
        pipe.execute()

        # Publish notification for aggregator
        self.client.publish("risk_updates", json.dumps({
            "instrument_id": metrics.instrument_id,
            "timestamp": curve_timestamp,
        }))

        logger.debug(f"Wrote risk for {metrics.instrument_id}: DV01={metrics.dv01:.2f}")

    def get_all_trade_risks(self) -> Dict[str, Dict[str, str]]:
        """Get all trade risk data for aggregation.

        Returns:
            Dict mapping instrument IDs to their risk data
        """
        result = {}
        cursor = 0

        while True:
            cursor, keys = self.client.scan(cursor, match="trade:*:risk", count=100)

            pipe = self.client.pipeline()
            for key in keys:
                pipe.hgetall(key)

            values = pipe.execute()

            for key, data in zip(keys, values):
                # Extract instrument ID from key
                instrument_id = key.split(":")[1]
                result[instrument_id] = data

            if cursor == 0:
                break

        return result

    def write_portfolio_aggregates(self, aggregates: Dict[str, Any]) -> None:
        """Write portfolio-level aggregates.

        Args:
            aggregates: Dict with total_npv, total_dv01, krd sums
        """
        key = "portfolio:aggregates"

        data = {
            "total_npv": str(aggregates.get("total_npv", 0)),
            "total_dv01": str(aggregates.get("total_dv01", 0)),
            "instrument_count": str(aggregates.get("instrument_count", 0)),
            "updated_at": str(int(time.time() * 1000)),
        }

        # Add KRD totals
        for tenor, value in aggregates.get("krd", {}).items():
            data[f"total_krd_{tenor.lower()}"] = str(value)

        self.client.hset(key, mapping=data)
        logger.info(f"Portfolio aggregates updated: DV01={aggregates.get('total_dv01', 0):.2f}")

    def write_yield_curve(self, rates: Dict[str, float], curve_timestamp: int) -> None:
        """Write latest yield curve snapshot to Redis.

        Args:
            rates: Tenor -> rate mapping (e.g. {"2Y": 0.0420, ...})
            curve_timestamp: Kafka message timestamp (ms)
        """
        data = {f"rate_{tenor.lower()}": str(rate) for tenor, rate in rates.items()}
        data["timestamp"] = str(curve_timestamp)
        data["updated_at"] = str(int(time.time() * 1000))

        pipe = self.client.pipeline()
        pipe.hset("yield_curve:latest", mapping=data)

        # Store history as JSON in sorted set (score = timestamp)
        curve_json = json.dumps({tenor: rate for tenor, rate in rates.items()})
        pipe.zadd("yield_curve:history", {curve_json: curve_timestamp})

        # Keep only last 1 hour of curve history
        hour_ago = int(time.time() * 1000) - 3600_000
        pipe.zremrangebyscore("yield_curve:history", "-inf", hour_ago)

        pipe.execute()
        logger.debug(f"Wrote yield curve at {curve_timestamp}")

    def close(self) -> None:
        """Close Redis connection."""
        self.client.close()
        logger.info("Redis connection closed")
