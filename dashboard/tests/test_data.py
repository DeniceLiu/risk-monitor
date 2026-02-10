"""Tests for data fetching module."""

import pytest
from unittest.mock import MagicMock, patch, PropertyMock
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Setup path and mocks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Mock streamlit
mock_st = MagicMock()
mock_st.session_state = {}
mock_st.cache_data = lambda ttl=None: lambda func: func
sys.modules['streamlit'] = mock_st


class TestTradeRisk:
    """Tests for TradeRisk dataclass."""

    def test_trade_risk_creation(self):
        """Test creating TradeRisk object."""
        from data import TradeRisk
        trade = TradeRisk(
            instrument_id="test-123",
            npv=1000000.0,
            dv01=12500.0,
            krd_2y=2500.0,
            krd_5y=4000.0,
            krd_10y=4000.0,
            krd_30y=2000.0,
            curve_timestamp=1704067200000,
            updated_at=1704067200000,
        )
        assert trade.instrument_id == "test-123"
        assert trade.npv == 1000000.0
        assert trade.dv01 == 12500.0

    def test_trade_risk_negative_dv01(self):
        """Test TradeRisk with negative DV01 (short duration)."""
        from data import TradeRisk
        trade = TradeRisk(
            instrument_id="test-456",
            npv=500000.0,
            dv01=-8500.0,
            krd_2y=-1500.0,
            krd_5y=-2500.0,
            krd_10y=-3000.0,
            krd_30y=-1500.0,
            curve_timestamp=1704067200000,
            updated_at=1704067200000,
        )
        assert trade.dv01 < 0


class TestPortfolioAggregates:
    """Tests for PortfolioAggregates dataclass."""

    def test_portfolio_aggregates_creation(self):
        """Test creating PortfolioAggregates object."""
        from data import PortfolioAggregates
        agg = PortfolioAggregates(
            total_npv=100000000.0,
            total_dv01=500000.0,
            instrument_count=100,
            krd_2y=100000.0,
            krd_5y=150000.0,
            krd_10y=175000.0,
            krd_30y=75000.0,
            updated_at=1704067200000,
        )
        assert agg.total_npv == 100000000.0
        assert agg.instrument_count == 100


class TestPortfolio:
    """Tests for Portfolio dataclass."""

    def test_portfolio_creation(self):
        """Test creating Portfolio object."""
        from data import Portfolio
        portfolio = Portfolio(
            id="CREDIT_IG",
            name="Investment Grade Credit",
            description="High quality bonds",
            strategy_type="credit",
            bond_count=50,
            total_notional=50000000.0,
        )
        assert portfolio.id == "CREDIT_IG"
        assert portfolio.bond_count == 50

    def test_portfolio_default_values(self):
        """Test Portfolio default values."""
        from data import Portfolio
        portfolio = Portfolio(
            id="TEST",
            name="Test Portfolio",
            description="",
            strategy_type="",
        )
        assert portfolio.bond_count == 0
        assert portfolio.total_notional == 0.0


class TestPortfolioService:
    """Tests for PortfolioService class."""

    def test_init(self):
        """Test PortfolioService initialization."""
        from data import PortfolioService
        service = PortfolioService("http://localhost:8000")
        assert service.api_url == "http://localhost:8000"

    def test_init_strips_trailing_slash(self):
        """Test that trailing slash is stripped from URL."""
        from data import PortfolioService
        service = PortfolioService("http://localhost:8000/")
        assert service.api_url == "http://localhost:8000"

    @patch('httpx.Client')
    def test_get_portfolios_success(self, mock_client_class):
        """Test successful portfolio fetching."""
        from data import PortfolioService

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"id": "CREDIT_IG", "name": "Credit IG", "description": "",
             "strategy_type": "credit", "bond_count": 50, "total_notional": 50000000},
        ]

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        service = PortfolioService("http://localhost:8000")
        portfolios = service.get_portfolios()

        assert len(portfolios) == 1
        assert portfolios[0].id == "CREDIT_IG"

    @patch('httpx.Client')
    def test_get_portfolios_api_error_fallback(self, mock_client_class):
        """Test fallback to instruments when portfolio API fails."""
        from data import PortfolioService

        mock_client = MagicMock()
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)

        # First call returns 404, second call (instruments) returns data
        portfolio_response = MagicMock()
        portfolio_response.status_code = 404

        instruments_response = MagicMock()
        instruments_response.status_code = 200
        instruments_response.json.return_value = {
            "items": [
                {"portfolio_id": "CREDIT_IG", "notional": 1000000},
                {"portfolio_id": "CREDIT_IG", "notional": 2000000},
                {"portfolio_id": "CREDIT_HY", "notional": 500000},
            ],
            "pages": 1,
        }

        mock_client.get.side_effect = [portfolio_response, instruments_response]
        mock_client_class.return_value = mock_client

        service = PortfolioService("http://localhost:8000")
        portfolios = service.get_portfolios()

        # Should have extracted portfolios from instruments
        assert len(portfolios) == 2

    @patch('httpx.Client')
    def test_get_instruments_map_success(self, mock_client_class):
        """Test successful instruments map fetching."""
        from data import PortfolioService

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "items": [
                {
                    "id": "uuid-123",
                    "portfolio_id": "CREDIT_IG",
                    "isin": "US0378331005",
                    "instrument_type": "BOND",
                    "notional": 1000000,
                    "currency": "USD",
                    "coupon_rate": 0.045,
                    "maturity_date": "2030-01-15",
                },
            ],
            "pages": 1,
        }

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        service = PortfolioService("http://localhost:8000")
        instruments_map = service.get_instruments_map()

        assert "uuid-123" in instruments_map
        assert instruments_map["uuid-123"]["portfolio_id"] == "CREDIT_IG"

    @patch('httpx.Client')
    def test_get_instruments_map_pagination(self, mock_client_class):
        """Test instruments map handles pagination."""
        from data import PortfolioService

        page1_response = MagicMock()
        page1_response.status_code = 200
        page1_response.json.return_value = {
            "items": [{"id": "uuid-1", "portfolio_id": "CREDIT_IG"}],
            "pages": 2,
        }

        page2_response = MagicMock()
        page2_response.status_code = 200
        page2_response.json.return_value = {
            "items": [{"id": "uuid-2", "portfolio_id": "CREDIT_HY"}],
            "pages": 2,
        }

        mock_client = MagicMock()
        mock_client.get.side_effect = [page1_response, page2_response]
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        service = PortfolioService("http://localhost:8000")
        instruments_map = service.get_instruments_map()

        assert len(instruments_map) == 2
        assert "uuid-1" in instruments_map
        assert "uuid-2" in instruments_map

    @patch('httpx.Client')
    def test_get_instruments_map_uses_correct_page_size(self, mock_client_class):
        """Test that page_size is 100 or less (API limit)."""
        from data import PortfolioService

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"items": [], "pages": 1}

        mock_client = MagicMock()
        mock_client.get.return_value = mock_response
        mock_client.__enter__ = MagicMock(return_value=mock_client)
        mock_client.__exit__ = MagicMock(return_value=False)
        mock_client_class.return_value = mock_client

        service = PortfolioService("http://localhost:8000")
        service.get_instruments_map()

        # Verify the page_size parameter is <= 100
        call_args = mock_client.get.call_args
        params = call_args.kwargs.get('params', call_args[1].get('params', {}))
        assert params.get('page_size', 100) <= 100


class TestRiskDataFetcher:
    """Tests for RiskDataFetcher class."""

    @patch('redis.Redis')
    def test_init(self, mock_redis_class):
        """Test RiskDataFetcher initialization."""
        from data import RiskDataFetcher
        mock_redis_class.return_value = MagicMock()

        fetcher = RiskDataFetcher("localhost", 6379)
        assert fetcher.client is not None

    @patch('redis.Redis')
    def test_is_connected_success(self, mock_redis_class):
        """Test connection check returns True when connected."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.ping.return_value = True
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        assert fetcher.is_connected() is True

    @patch('redis.Redis')
    def test_is_connected_failure(self, mock_redis_class):
        """Test connection check returns False when disconnected."""
        from data import RiskDataFetcher
        import redis

        mock_client = MagicMock()
        mock_client.ping.side_effect = redis.ConnectionError("Connection refused")
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        assert fetcher.is_connected() is False

    @patch('redis.Redis')
    def test_get_portfolio_aggregates_success(self, mock_redis_class):
        """Test getting portfolio aggregates."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.hgetall.return_value = {
            "total_npv": "100000000",
            "total_dv01": "500000",
            "instrument_count": "100",
            "total_krd_2y": "100000",
            "total_krd_5y": "150000",
            "total_krd_10y": "175000",
            "total_krd_30y": "75000",
            "updated_at": "1704067200000",
        }
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        aggregates = fetcher.get_portfolio_aggregates()

        assert aggregates is not None
        assert aggregates.total_npv == 100000000.0
        assert aggregates.total_dv01 == 500000.0
        assert aggregates.instrument_count == 100

    @patch('redis.Redis')
    def test_get_portfolio_aggregates_empty(self, mock_redis_class):
        """Test getting portfolio aggregates when empty."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.hgetall.return_value = {}
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        aggregates = fetcher.get_portfolio_aggregates()

        assert aggregates is None

    @patch('redis.Redis')
    def test_get_all_trade_risks(self, mock_redis_class):
        """Test getting all trade risks."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.scan.return_value = (0, ["trade:uuid-1:risk", "trade:uuid-2:risk"])

        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [
            {
                "npv": "1000000",
                "dv01": "12500",
                "krd_2y": "2500",
                "krd_5y": "4000",
                "krd_10y": "4000",
                "krd_30y": "2000",
                "curve_timestamp": "1704067200000",
                "updated_at": "1704067200000",
            },
            {
                "npv": "500000",
                "dv01": "-8500",
                "krd_2y": "-1500",
                "krd_5y": "-2500",
                "krd_10y": "-3000",
                "krd_30y": "-1500",
                "curve_timestamp": "1704067200000",
                "updated_at": "1704067200000",
            },
        ]
        mock_client.pipeline.return_value = mock_pipe
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        trades = fetcher.get_all_trade_risks()

        assert len(trades) == 2
        assert trades[0].instrument_id == "uuid-1"
        assert trades[1].dv01 == -8500.0

    @patch('redis.Redis')
    def test_get_trades_dataframe(self, mock_redis_class):
        """Test getting trades as DataFrame."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.scan.return_value = (0, ["trade:uuid-1:risk"])
        mock_client.hgetall.side_effect = [
            {},  # Meta call returns empty
        ]

        mock_pipe = MagicMock()
        mock_pipe.execute.return_value = [
            {
                "npv": "1000000",
                "dv01": "12500",
                "krd_2y": "2500",
                "krd_5y": "4000",
                "krd_10y": "4000",
                "krd_30y": "2000",
                "curve_timestamp": "1704067200000",
                "updated_at": "1704067200000",
            },
        ]
        mock_client.pipeline.return_value = mock_pipe
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        df = fetcher.get_trades_dataframe()

        assert not df.empty
        assert "Instrument ID" in df.columns
        assert "DV01" in df.columns

    @patch('redis.Redis')
    def test_get_trades_dataframe_empty(self, mock_redis_class):
        """Test getting empty trades DataFrame."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.scan.return_value = (0, [])
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        df = fetcher.get_trades_dataframe()

        assert df.empty

    @patch('redis.Redis')
    def test_get_historical_dv01(self, mock_redis_class):
        """Test getting historical DV01 data."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.zrangebyscore.return_value = [
            ("10000", 1704067200000),
            ("11000", 1704070800000),
            ("10500", 1704074400000),
        ]
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()
        df = fetcher.get_historical_dv01(start, end)

        assert len(df) == 3
        assert "timestamp" in df.columns
        assert "dv01" in df.columns

    @patch('redis.Redis')
    def test_get_historical_dv01_empty(self, mock_redis_class):
        """Test getting historical DV01 when no data."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_client.zrangebyscore.return_value = []
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        start = datetime.now() - timedelta(hours=1)
        end = datetime.now()
        df = fetcher.get_historical_dv01(start, end)

        assert df.empty

    @patch('redis.Redis')
    def test_store_historical_snapshot(self, mock_redis_class):
        """Test storing historical snapshot."""
        from data import RiskDataFetcher

        mock_client = MagicMock()
        mock_redis_class.return_value = mock_client

        fetcher = RiskDataFetcher("localhost", 6379)
        fetcher.store_historical_snapshot(dv01=500000, npv=100000000)

        # Verify zadd was called for both dv01 and npv
        assert mock_client.zadd.call_count == 2
