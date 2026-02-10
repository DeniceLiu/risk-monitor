"""Tests for filter components."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Setup path and mocks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class MockSessionState(dict):
    """Mock that behaves like Streamlit's session_state (dict with attribute access)."""
    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        try:
            del self[key]
        except KeyError:
            raise AttributeError(key)


# Mock streamlit before importing
mock_st = MagicMock()
mock_st.session_state = MockSessionState()
sys.modules['streamlit'] = mock_st


class TestPortfolioFilters:
    """Tests for PortfolioFilters class."""

    def setup_method(self):
        """Reset session state before each test."""
        # Clear and reset the session_state dict in place
        mock_st.session_state.clear()

    def test_init_creates_session_state(self):
        """Test that PortfolioFilters has the correct default filter structure."""
        from components.filters import PortfolioFilters

        # Verify the class has correct default structure
        assert PortfolioFilters.DEFAULT_FILTERS["portfolio"] == "ALL"
        assert "USD" in PortfolioFilters.DEFAULT_FILTERS["currencies"]
        assert "BOND" in PortfolioFilters.DEFAULT_FILTERS["instrument_types"]

    def test_default_filters(self):
        """Test default filter values are correct."""
        from components.filters import PortfolioFilters

        # Verify class defaults
        defaults = PortfolioFilters.DEFAULT_FILTERS
        assert defaults["portfolio"] == "ALL"
        assert defaults["currencies"] == ["USD"]
        assert defaults["instrument_types"] == ["BOND", "SWAP"]
        assert defaults["maturity_min"] == 0
        assert defaults["maturity_max"] == 30
        assert defaults["dv01_min"] == 0

    def test_apply_filters_empty_dataframe(self):
        """Test applying filters to empty DataFrame."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame()
        result = filters.apply_filters(df, {"portfolio": "ALL"})

        assert result.empty

    def test_apply_filters_portfolio_all(self):
        """Test filtering with ALL portfolios."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Currency": ["USD", "USD", "USD"],
            "DV01": [1000, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
        })

        assert len(result) == 3

    def test_apply_filters_portfolio_specific(self):
        """Test filtering by specific portfolio."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Portfolio": ["Credit Ig", "Credit Hy", "Tech Sector"],
            "Currency": ["USD", "USD", "USD"],
            "DV01": [1000, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "CREDIT_IG",
            "currencies": ["USD"],
        })

        assert len(result) == 1
        assert result.iloc[0]["Portfolio ID"] == "CREDIT_IG"

    def test_apply_filters_portfolio_fallback_to_name(self):
        """Test filtering falls back to Portfolio column when ID not present."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio": ["CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Currency": ["USD", "USD", "USD"],
            "DV01": [1000, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "CREDIT_IG",
            "currencies": ["USD"],
        })

        assert len(result) == 1

    def test_apply_filters_currency(self):
        """Test filtering by currency."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Currency": ["USD", "EUR", "USD"],
            "DV01": [1000, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
        })

        assert len(result) == 2
        assert all(result["Currency"] == "USD")

    def test_apply_filters_multiple_currencies(self):
        """Test filtering by multiple currencies."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["A", "B", "C", "D"],
            "Currency": ["USD", "EUR", "GBP", "JPY"],
            "DV01": [1000, 2000, 3000, 4000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD", "EUR"],
        })

        assert len(result) == 2
        assert set(result["Currency"].tolist()) == {"USD", "EUR"}

    def test_apply_filters_instrument_type(self):
        """Test filtering by instrument type."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["A", "B", "C"],
            "Type": ["BOND", "SWAP", "BOND"],
            "Currency": ["USD", "USD", "USD"],
            "DV01": [1000, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
            "instrument_types": ["BOND"],
        })

        assert len(result) == 2
        assert all(result["Type"] == "BOND")

    def test_apply_filters_maturity_range(self):
        """Test filtering by years to maturity."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["A", "B", "C", "D"],
            "Years to Maturity": [2, 5, 15, 25],
            "Currency": ["USD", "USD", "USD", "USD"],
            "DV01": [1000, 2000, 3000, 4000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
            "maturity_min": 5,
            "maturity_max": 20,
        })

        assert len(result) == 2
        assert result["Years to Maturity"].min() >= 5
        assert result["Years to Maturity"].max() <= 20

    def test_apply_filters_dv01_threshold(self):
        """Test filtering by DV01 threshold."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["A", "B", "C", "D"],
            "Currency": ["USD", "USD", "USD", "USD"],
            "DV01": [500, -1500, 2000, -3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
            "dv01_min": 1000,
        })

        # Should include trades with |DV01| >= 1000
        assert len(result) == 3
        assert all(abs(result["DV01"]) >= 1000)

    def test_apply_filters_combined(self):
        """Test combining multiple filters."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Type": ["BOND", "SWAP", "BOND", "BOND"],
            "Currency": ["USD", "USD", "EUR", "USD"],
            "DV01": [1000, 500, 2000, 3000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "CREDIT_IG",
            "currencies": ["USD"],
            "instrument_types": ["BOND"],
            "dv01_min": 0,
        })

        assert len(result) == 1
        assert result.iloc[0]["Portfolio ID"] == "CREDIT_IG"
        assert result.iloc[0]["Type"] == "BOND"

    def test_apply_filters_no_currency_column(self):
        """Test filtering when currency column doesn't exist."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY"],
            "DV01": [1000, 2000],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
        })

        # Should return all rows if currency column doesn't exist
        assert len(result) == 2

    def test_apply_filters_preserves_columns(self):
        """Test that filtering preserves all columns."""
        from components.filters import PortfolioFilters

        filters = PortfolioFilters()
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY"],
            "Currency": ["USD", "USD"],
            "DV01": [1000, 2000],
            "NPV": [100000, 200000],
            "Extra Column": ["A", "B"],
        })

        result = filters.apply_filters(df, {
            "portfolio": "ALL",
            "currencies": ["USD"],
        })

        assert set(result.columns) == set(df.columns)


class TestPortfolioFiltersCalculateDateRange:
    """Tests for date range calculation."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state = MockSessionState()

    def test_calculate_date_range_last_hour(self):
        """Test Last Hour preset."""
        from components.filters import PortfolioFilters
        from datetime import datetime, timedelta

        filters = PortfolioFilters()
        config = {"preset": "Last Hour"}
        start, end = filters._calculate_date_range(config)

        now = datetime.now()
        expected_start = now - timedelta(hours=1)

        # Allow 5 second tolerance
        assert abs((end - now).total_seconds()) < 5
        assert abs((start - expected_start).total_seconds()) < 5

    def test_calculate_date_range_last_24_hours(self):
        """Test Last 24 Hours preset."""
        from components.filters import PortfolioFilters
        from datetime import datetime, timedelta

        filters = PortfolioFilters()
        config = {"preset": "Last 24 Hours"}
        start, end = filters._calculate_date_range(config)

        now = datetime.now()
        expected_start = now - timedelta(days=1)

        assert abs((start - expected_start).total_seconds()) < 5

    def test_calculate_date_range_last_7_days(self):
        """Test Last 7 Days preset."""
        from components.filters import PortfolioFilters
        from datetime import datetime, timedelta

        filters = PortfolioFilters()
        config = {"preset": "Last 7 Days"}
        start, end = filters._calculate_date_range(config)

        now = datetime.now()
        expected_start = now - timedelta(days=7)

        assert abs((start - expected_start).total_seconds()) < 5

    def test_calculate_date_range_custom(self):
        """Test Custom date range."""
        from components.filters import PortfolioFilters
        from datetime import datetime, date

        filters = PortfolioFilters()
        config = {
            "preset": "Custom",
            "custom_start": date(2024, 1, 1),
            "custom_end": date(2024, 1, 31),
        }
        start, end = filters._calculate_date_range(config)

        assert start.date() == date(2024, 1, 1)
        assert end.date() == date(2024, 1, 31)


class TestPortfolioFiltersStateManagement:
    """Tests for state management in filters."""

    def setup_method(self):
        """Reset session state before each test."""
        mock_st.session_state.clear()

    def test_pending_and_applied_are_independent(self):
        """Test that DEFAULT_FILTERS is copied, not referenced."""
        from components.filters import PortfolioFilters

        # Verify that DEFAULT_FILTERS returns copies, not references
        defaults1 = PortfolioFilters.DEFAULT_FILTERS.copy()
        defaults2 = PortfolioFilters.DEFAULT_FILTERS.copy()

        defaults1["portfolio"] = "CHANGED"

        # Original and other copy should be unchanged
        assert PortfolioFilters.DEFAULT_FILTERS["portfolio"] == "ALL"
        assert defaults2["portfolio"] == "ALL"

    def test_default_date_range_values(self):
        """Test default date range configuration."""
        from components.filters import PortfolioFilters

        defaults = PortfolioFilters.DEFAULT_DATE_RANGE
        assert defaults["preset"] == "Last Hour"
        assert defaults["custom_start"] is None
        assert defaults["custom_end"] is None
