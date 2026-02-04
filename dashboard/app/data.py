"""Data fetching from Redis and Security Master API."""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

import redis
import pandas as pd
import httpx
import streamlit as st


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


@dataclass
class Portfolio:
    """Portfolio metadata from Security Master."""
    id: str
    name: str
    description: str
    strategy_type: str
    bond_count: int = 0
    total_notional: float = 0.0


class PortfolioService:
    """Fetches portfolio data from Security Master API."""

    def __init__(self, api_url: str):
        """Initialize with API URL."""
        self.api_url = api_url.rstrip("/")
        self._portfolios_cache: Optional[List[Portfolio]] = None
        self._instruments_cache: Optional[Dict[int, Dict]] = None
        self._cache_time: float = 0
        self._cache_ttl: float = 30  # Cache for 30 seconds

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        return time.time() - self._cache_time < self._cache_ttl

    @st.cache_data(ttl=30)
    def get_portfolios(_self) -> List[Portfolio]:
        """Fetch all portfolios from Security Master."""
        try:
            with httpx.Client(timeout=10.0) as client:
                # Fetch portfolios
                response = client.get(f"{_self.api_url}/api/v1/portfolios")
                if response.status_code != 200:
                    # Portfolios endpoint might not exist, get from instruments
                    return _self._get_portfolios_from_instruments()

                data = response.json()
                portfolios = []
                for p in data:
                    portfolios.append(Portfolio(
                        id=p["id"],
                        name=p["name"],
                        description=p.get("description", ""),
                        strategy_type=p.get("strategy_type", ""),
                        bond_count=p.get("bond_count", 0),
                        total_notional=float(p.get("total_notional", 0)),
                    ))
                return portfolios
        except Exception:
            return _self._get_portfolios_from_instruments()

    def _get_portfolios_from_instruments(self) -> List[Portfolio]:
        """Extract unique portfolios from instruments."""
        try:
            with httpx.Client(timeout=30.0) as client:
                portfolio_stats: Dict[str, Dict] = {}
                page = 1
                page_size = 100  # API limit is 100

                while True:
                    response = client.get(
                        f"{self.api_url}/api/v1/instruments",
                        params={"page": page, "page_size": page_size}
                    )
                    if response.status_code != 200:
                        break

                    data = response.json()
                    for item in data.get("items", []):
                        pid = item.get("portfolio_id")
                        if pid:
                            if pid not in portfolio_stats:
                                portfolio_stats[pid] = {
                                    "count": 0,
                                    "notional": 0.0
                                }
                            portfolio_stats[pid]["count"] += 1
                            portfolio_stats[pid]["notional"] += float(item.get("notional", 0))

                    if page >= data.get("pages", 1):
                        break
                    page += 1

                # Create Portfolio objects
                portfolios = []
                for pid, stats in portfolio_stats.items():
                    portfolios.append(Portfolio(
                        id=pid,
                        name=pid.replace("_", " ").title(),
                        description="",
                        strategy_type="",
                        bond_count=stats["count"],
                        total_notional=stats["notional"],
                    ))

                return sorted(portfolios, key=lambda p: p.bond_count, reverse=True)
        except Exception:
            return []

    @st.cache_data(ttl=30)
    def get_instruments_map(_self) -> Dict[str, Dict]:
        """Get map of instrument_id -> instrument details including portfolio_id."""
        try:
            with httpx.Client(timeout=30.0) as client:
                instruments_map = {}
                page = 1
                page_size = 100  # API limit is 100

                while True:
                    response = client.get(
                        f"{_self.api_url}/api/v1/instruments",
                        params={"page": page, "page_size": page_size}
                    )
                    if response.status_code != 200:
                        break

                    data = response.json()
                    for item in data.get("items", []):
                        instruments_map[item["id"]] = {
                            "portfolio_id": item.get("portfolio_id"),
                            "isin": item.get("isin", ""),
                            "instrument_type": item.get("instrument_type", "BOND"),
                            "notional": float(item.get("notional", 0)),
                            "currency": item.get("currency", "USD"),
                            "coupon_rate": float(item.get("coupon_rate", 0)),
                            "maturity_date": item.get("maturity_date"),
                        }

                    if page >= data.get("pages", 1):
                        break
                    page += 1

                return instruments_map
        except Exception:
            return {}


class RiskDataFetcher:
    """Fetches risk data from Redis."""

    def __init__(self, host: str, port: int, portfolio_service: Optional[PortfolioService] = None):
        """Initialize Redis connection."""
        self.client = redis.Redis(
            host=host,
            port=port,
            decode_responses=True,
        )
        self.portfolio_service = portfolio_service

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

        # Get instrument metadata from Security Master if available
        instruments_map = {}
        if self.portfolio_service:
            instruments_map = self.portfolio_service.get_instruments_map()

        data = []
        for t in trades:
            # Try to get additional metadata from Redis
            meta_key = f"trade:{t.instrument_id}:meta"
            try:
                meta = self.client.hgetall(meta_key)
            except redis.RedisError:
                meta = {}

            # Get instrument info from Security Master (using instrument ID as key)
            inst_info = instruments_map.get(t.instrument_id, {})

            # Use ISIN as display ID if available
            isin = inst_info.get("isin", "")
            display_id = isin[:12] if isin else t.instrument_id[:12]
            if len(display_id) > 10:
                display_id = display_id[:10] + ".."

            # Get portfolio with fallback to default
            portfolio_id = inst_info.get("portfolio_id", "") or "DEFAULT"
            portfolio_name = portfolio_id.replace("_", " ").title() if portfolio_id != "DEFAULT" else "Main Portfolio"
            
            data.append({
                "Instrument ID": display_id,
                "Full ID": t.instrument_id,
                "ISIN": isin,
                "Type": inst_info.get("instrument_type", meta.get("type", "BOND")),
                "Currency": inst_info.get("currency", meta.get("currency", "USD")),
                "Portfolio": portfolio_name,
                "Portfolio ID": portfolio_id,
                "Notional": inst_info.get("notional", 0),
                "Coupon": inst_info.get("coupon_rate", 0),
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

    def get_yield_curve_latest(self) -> Optional[Dict[str, float]]:
        """Get the latest yield curve rates from Redis.

        Returns:
            Dict of tenor -> rate, or None if unavailable
        """
        try:
            data = self.client.hgetall("yield_curve:latest")
            if not data:
                return None
            rates = {}
            for key, val in data.items():
                if key.startswith("rate_"):
                    tenor = key[5:].upper()
                    rates[tenor] = float(val)
            return rates if rates else None
        except redis.RedisError:
            return None

    def get_yield_curve_history(self, minutes: int = 30) -> pd.DataFrame:
        """Get yield curve history for time-series display.

        Args:
            minutes: How many minutes of history to fetch

        Returns:
            DataFrame with columns: timestamp, and one column per tenor
        """
        now_ms = int(time.time() * 1000)
        start_ms = now_ms - minutes * 60 * 1000

        try:
            results = self.client.zrangebyscore(
                "yield_curve:history", start_ms, now_ms, withscores=True
            )
        except redis.RedisError:
            return pd.DataFrame()

        if not results:
            return pd.DataFrame()

        rows = []
        for value, score in results:
            rates = json.loads(value)
            row = {"timestamp": datetime.fromtimestamp(score / 1000)}
            for tenor, rate in rates.items():
                row[tenor] = float(rate)
            rows.append(row)

        return pd.DataFrame(rows)

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
