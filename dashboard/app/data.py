"""Data fetching from Redis."""

import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import redis
import pandas as pd


@dataclass
class TradeRisk:
    """Risk data for a single trade."""
    instrument_id: str
    npv: float
    dv01: float
    krd_2y: float
    krd_5y: float
    krd_10y: float
    krd_30y: float
    curve_timestamp: int
    updated_at: int


@dataclass
class PortfolioAggregates:
    """Aggregated portfolio risk."""
    total_npv: float
    total_dv01: float
    instrument_count: int
    krd_2y: float
    krd_5y: float
    krd_10y: float
    krd_30y: float
    updated_at: int


class RiskDataFetcher:
    """Fetches risk data from Redis."""

    def __init__(self, host: str, port: int):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )

    def get_portfolio_aggregates(self) -> Optional[PortfolioAggregates]:
        """Get portfolio-level aggregates."""
        data = self.client.hgetall("portfolio:aggregates")
        if not data:
            return None

        return PortfolioAggregates(
            total_npv=float(data.get("total_npv", 0)),
            total_dv01=float(data.get("total_dv01", 0)),
            instrument_count=int(data.get("instrument_count", 0)),
            krd_2y=float(data.get("total_krd_2y", 0)),
            krd_5y=float(data.get("total_krd_5y", 0)),
            krd_10y=float(data.get("total_krd_10y", 0)),
            krd_30y=float(data.get("total_krd_30y", 0)),
            updated_at=int(data.get("updated_at", 0)),
        )

    def get_all_trade_risks(self) -> List[TradeRisk]:
        """Get all trade-level risk data."""
        trades = []
        cursor = 0

        while True:
            cursor, keys = self.client.scan(cursor, match="trade:*:risk", count=100)

            pipe = self.client.pipeline()
            for key in keys:
                pipe.hgetall(key)

            values = pipe.execute()

            for key, data in zip(keys, values):
                if not data:
                    continue

                instrument_id = key.split(":")[1]
                try:
                    trade = TradeRisk(
                        instrument_id=instrument_id,
                        npv=float(data.get("npv", 0)),
                        dv01=float(data.get("dv01", 0)),
                        krd_2y=float(data.get("krd_2y", 0)),
                        krd_5y=float(data.get("krd_5y", 0)),
                        krd_10y=float(data.get("krd_10y", 0)),
                        krd_30y=float(data.get("krd_30y", 0)),
                        curve_timestamp=int(data.get("curve_timestamp", 0)),
                        updated_at=int(data.get("updated_at", 0)),
                    )
                    trades.append(trade)
                except (ValueError, TypeError):
                    continue

            if cursor == 0:
                break

        return trades

    def get_trades_dataframe(self) -> pd.DataFrame:
        """Get trade risks as a pandas DataFrame."""
        trades = self.get_all_trade_risks()

        if not trades:
            return pd.DataFrame()

        data = []
        for t in trades:
            # Try to get additional metadata from Redis
            meta_key = f"trade:{t.instrument_id}:meta"
            try:
                meta = self.client.hgetall(meta_key)
            except redis.RedisError:
                meta = {}

            data.append({
                "Instrument ID": t.instrument_id[:8] + "...",
                "Full ID": t.instrument_id,
                "Type": meta.get("type", "BOND"),  # Default to BOND
                "Currency": meta.get("currency", "USD"),  # Default to USD
                "NPV": t.npv,
                "DV01": t.dv01,
                "KRD 2Y": t.krd_2y,
                "KRD 5Y": t.krd_5y,
                "KRD 10Y": t.krd_10y,
                "KRD 30Y": t.krd_30y,
            })

        df = pd.DataFrame(data)
        return df.sort_values("DV01", ascending=False)

    def is_connected(self) -> bool:
        """Check Redis connection."""
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            return False

    def get_historical_dv01(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical DV01 data for date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataFrame with columns: timestamp, dv01
        """
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        # Get data from sorted set
        try:
            results = self.client.zrangebyscore(
                "portfolio:dv01_history", start_ts, end_ts, withscores=True
            )
        except redis.RedisError:
            return pd.DataFrame(columns=["timestamp", "dv01"])

        if not results:
            return pd.DataFrame(columns=["timestamp", "dv01"])

        data = []
        for value, score in results:
            data.append(
                {"timestamp": datetime.fromtimestamp(score / 1000), "dv01": float(value)}
            )

        return pd.DataFrame(data)

    def get_historical_npv(
        self, start_date: datetime, end_date: datetime
    ) -> pd.DataFrame:
        """
        Get historical NPV data for date range.

        Args:
            start_date: Start of date range
            end_date: End of date range

        Returns:
            DataFrame with columns: timestamp, npv
        """
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)

        try:
            results = self.client.zrangebyscore(
                "portfolio:npv_history", start_ts, end_ts, withscores=True
            )
        except redis.RedisError:
            return pd.DataFrame(columns=["timestamp", "npv"])

        if not results:
            return pd.DataFrame(columns=["timestamp", "npv"])

        data = []
        for value, score in results:
            data.append(
                {"timestamp": datetime.fromtimestamp(score / 1000), "npv": float(value)}
            )

        return pd.DataFrame(data)

    def store_historical_snapshot(self, dv01: float, npv: float) -> None:
        """
        Store current DV01 and NPV values for historical tracking.

        Args:
            dv01: Current portfolio DV01
            npv: Current portfolio NPV
        """
        timestamp = int(time.time() * 1000)

        try:
            # Store DV01
            self.client.zadd("portfolio:dv01_history", {str(dv01): timestamp})
            # Store NPV
            self.client.zadd("portfolio:npv_history", {str(npv): timestamp})

            # Keep only last 7 days of data (cleanup old entries)
            week_ago = timestamp - (7 * 24 * 60 * 60 * 1000)
            self.client.zremrangebyscore("portfolio:dv01_history", "-inf", week_ago)
            self.client.zremrangebyscore("portfolio:npv_history", "-inf", week_ago)
        except redis.RedisError:
            pass  # Silently fail for historical storage
