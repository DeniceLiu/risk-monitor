"""Shared test fixtures for dashboard tests."""

import pytest
import pandas as pd
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

# Mock streamlit before importing modules that use it
mock_st = MagicMock()
mock_st.session_state = {}
mock_st.cache_data = lambda ttl=None: lambda func: func
sys.modules['streamlit'] = mock_st


@pytest.fixture
def sample_trades_df():
    """Create sample trades DataFrame for testing."""
    return pd.DataFrame({
        "Instrument ID": ["AAPL2030", "MSFT2028", "GOOGL2029", "AMZN2031", "META2027"],
        "Full ID": ["uuid-1", "uuid-2", "uuid-3", "uuid-4", "uuid-5"],
        "ISIN": ["US0378331005", "US5949181045", "US02079K3059", "US0231351067", "US30303M1027"],
        "Type": ["BOND", "BOND", "BOND", "BOND", "BOND"],
        "Currency": ["USD", "USD", "USD", "USD", "EUR"],
        "Portfolio": ["Credit Ig", "Credit Hy", "Tech Sector", "Credit Ig", "Tech Sector"],
        "Portfolio ID": ["CREDIT_IG", "CREDIT_HY", "TECH_SECTOR", "CREDIT_IG", "TECH_SECTOR"],
        "Notional": [1000000, 2000000, 1500000, 3000000, 500000],
        "Coupon": [0.045, 0.065, 0.0525, 0.04, 0.055],
        "NPV": [980000, 1950000, 1480000, 2920000, 495000],
        "DV01": [12500, -8500, 15000, 22000, 5000],
        "KRD 2Y": [2500, -1500, 3000, 4500, 1000],
        "KRD 5Y": [4000, -2500, 5000, 7000, 1500],
        "KRD 10Y": [4000, -3000, 5000, 7000, 1800],
        "KRD 30Y": [2000, -1500, 2000, 3500, 700],
    })


@pytest.fixture
def sample_trades_df_with_defaults():
    """Create sample trades DataFrame with some default portfolios."""
    return pd.DataFrame({
        "Instrument ID": ["AAPL2030", "MSFT2028", "UNASSIGNED1"],
        "Full ID": ["uuid-1", "uuid-2", "uuid-3"],
        "ISIN": ["US0378331005", "US5949181045", ""],
        "Type": ["BOND", "BOND", "BOND"],
        "Currency": ["USD", "USD", "USD"],
        "Portfolio": ["Credit Ig", "Credit Hy", "Main Portfolio"],
        "Portfolio ID": ["CREDIT_IG", "CREDIT_HY", "DEFAULT"],
        "Notional": [1000000, 2000000, 500000],
        "NPV": [980000, 1950000, 490000],
        "DV01": [12500, -8500, 3000],
        "KRD 2Y": [2500, -1500, 600],
        "KRD 5Y": [4000, -2500, 1000],
        "KRD 10Y": [4000, -3000, 1000],
        "KRD 30Y": [2000, -1500, 400],
    })


@pytest.fixture
def empty_trades_df():
    """Create empty trades DataFrame."""
    return pd.DataFrame()


@pytest.fixture
def sample_historical_df():
    """Create sample historical data DataFrame."""
    now = datetime.now()
    return pd.DataFrame({
        "timestamp": [now - timedelta(hours=i) for i in range(24, 0, -1)],
        "dv01": [10000 + i * 100 for i in range(24)],
    })


@pytest.fixture
def sample_npv_historical_df():
    """Create sample NPV historical data DataFrame."""
    now = datetime.now()
    return pd.DataFrame({
        "timestamp": [now - timedelta(hours=i) for i in range(24, 0, -1)],
        "npv": [1000000 + i * 10000 for i in range(24)],
    })


@pytest.fixture
def sample_portfolios():
    """Create sample Portfolio objects."""
    from data import Portfolio
    return [
        Portfolio(id="CREDIT_IG", name="Investment Grade Credit", description="IG bonds",
                  strategy_type="credit", bond_count=50, total_notional=50000000),
        Portfolio(id="CREDIT_HY", name="High Yield Credit", description="HY bonds",
                  strategy_type="credit", bond_count=30, total_notional=30000000),
        Portfolio(id="TECH_SECTOR", name="Technology Sector", description="Tech bonds",
                  strategy_type="sector", bond_count=25, total_notional=25000000),
    ]


@pytest.fixture
def mock_redis_client():
    """Create mock Redis client."""
    client = MagicMock()
    client.ping.return_value = True
    client.hgetall.return_value = {
        "total_npv": "100000000",
        "total_dv01": "500000",
        "instrument_count": "100",
        "total_krd_2y": "100000",
        "total_krd_5y": "150000",
        "total_krd_10y": "175000",
        "total_krd_30y": "75000",
        "updated_at": str(int(datetime.now().timestamp() * 1000)),
    }
    return client


@pytest.fixture
def mock_httpx_client():
    """Create mock httpx client."""
    client = MagicMock()
    return client
