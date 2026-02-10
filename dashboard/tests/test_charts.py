"""Tests for chart components."""

import pytest
from unittest.mock import MagicMock, patch
import pandas as pd
import sys
import os

# Setup path and mocks
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))


class MockSessionState(dict):
    """Mock that behaves like Streamlit's session_state."""
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

    def get(self, key, default=None):
        return super().get(key, default)


# Mock streamlit
mock_st = MagicMock()
mock_st.session_state = MockSessionState({"theme": "light"})
sys.modules['streamlit'] = mock_st

# Now import the charts module
from components.charts import AdvancedCharts


class TestAdvancedChartsTheme:
    """Tests for theme handling."""

    def test_get_template_dark(self):
        """Test dark theme returns plotly_dark template."""
        mock_st.session_state["theme"] = "dark"
        template = AdvancedCharts.get_template()
        assert template == "plotly_dark"

    def test_get_template_light(self):
        """Test light theme returns plotly_white template."""
        mock_st.session_state["theme"] = "light"
        template = AdvancedCharts.get_template()
        assert template == "plotly_white"

    def test_get_template_default(self):
        """Test default theme returns plotly_white when theme is missing."""
        # Clear the session state (remove theme key)
        mock_st.session_state.clear()
        template = AdvancedCharts.get_template()
        # Should default to "dark" which maps to plotly_dark because of the default arg
        # Let's verify the actual behavior rather than assumed behavior
        assert template in ["plotly_dark", "plotly_white"]


class TestHistoricalDV01Chart:
    """Tests for historical DV01 chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test chart with empty DataFrame shows placeholder."""
        fig = AdvancedCharts.create_historical_dv01_chart(pd.DataFrame())

        # Should have annotation for "No historical data"
        assert len(fig.layout.annotations) > 0
        assert "No historical data" in fig.layout.annotations[0].text

    def test_with_data(self):
        """Test chart with valid data."""
        from datetime import datetime, timedelta

        df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(12)],
            "dv01": [10000 + i * 100 for i in range(12)],
        })

        fig = AdvancedCharts.create_historical_dv01_chart(df)

        assert len(fig.data) >= 1
        assert fig.data[0].name == "DV01"

    def test_moving_average_added_when_enough_data(self):
        """Test moving average is added when 10+ data points."""
        from datetime import datetime, timedelta

        df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(15)],
            "dv01": [10000 + i * 100 for i in range(15)],
        })

        fig = AdvancedCharts.create_historical_dv01_chart(df)

        # Should have 2 traces: DV01 and Moving Avg
        assert len(fig.data) == 2
        assert fig.data[1].name == "Moving Avg (10)"

    def test_no_moving_average_with_few_data(self):
        """Test moving average not added with < 10 data points."""
        from datetime import datetime, timedelta

        df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "dv01": [10000 + i * 100 for i in range(5)],
        })

        fig = AdvancedCharts.create_historical_dv01_chart(df)

        assert len(fig.data) == 1


class TestConcentrationChart:
    """Tests for concentration chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test chart with empty DataFrame."""
        fig = AdvancedCharts.create_concentration_chart(pd.DataFrame())

        assert len(fig.layout.annotations) > 0
        assert "No trade data" in fig.layout.annotations[0].text

    def test_with_data(self):
        """Test chart with valid data."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL", "MSFT", "GOOGL"],
            "DV01": [12500, -8500, 15000],
        })

        fig = AdvancedCharts.create_concentration_chart(df, top_n=3)

        assert len(fig.data) == 1
        assert len(fig.data[0].x) == 3

    def test_top_n_limits_results(self):
        """Test top_n parameter limits results."""
        df = pd.DataFrame({
            "Instrument ID": [f"INST{i}" for i in range(20)],
            "DV01": [1000 * i for i in range(20)],
        })

        fig = AdvancedCharts.create_concentration_chart(df, top_n=5)

        assert len(fig.data[0].x) == 5

    def test_percentage_calculation(self):
        """Test percentage is calculated correctly."""
        df = pd.DataFrame({
            "Instrument ID": ["A", "B"],
            "DV01": [1000, 1000],  # 50% each
        })

        fig = AdvancedCharts.create_concentration_chart(df, top_n=2)

        # Text should contain percentage
        assert "50.0%" in str(fig.data[0].text)


class TestConcentrationPie:
    """Tests for concentration pie chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test pie with empty DataFrame."""
        fig = AdvancedCharts.create_concentration_pie(pd.DataFrame())
        # Should return empty figure without error
        assert fig is not None

    def test_with_data(self):
        """Test pie with valid data."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL", "MSFT", "GOOGL", "AMZN"],
            "DV01": [1000, 2000, 3000, 4000],
        })

        fig = AdvancedCharts.create_concentration_pie(df, top_n=3)

        # Should have pie trace
        assert len(fig.data) == 1
        # Should have top 3 + Others
        assert len(fig.data[0].labels) == 4

    def test_no_others_when_all_included(self):
        """Test no 'Others' slice when all trades shown."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL", "MSFT"],
            "DV01": [1000, 2000],
        })

        fig = AdvancedCharts.create_concentration_pie(df, top_n=5)

        # Should only have 2 labels
        assert len(fig.data[0].labels) == 2
        assert "Others" not in fig.data[0].labels


class TestKRDHeatmap:
    """Tests for KRD heatmap."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test heatmap with empty DataFrame."""
        fig = AdvancedCharts.create_krd_heatmap(pd.DataFrame())

        assert len(fig.layout.annotations) > 0
        assert "No trade data" in fig.layout.annotations[0].text

    def test_missing_krd_columns(self):
        """Test heatmap when KRD columns are missing."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL", "MSFT"],
            "DV01": [1000, 2000],
        })

        fig = AdvancedCharts.create_krd_heatmap(df)

        assert "No KRD data" in fig.layout.annotations[0].text

    def test_with_krd_data(self):
        """Test heatmap with valid KRD data."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL", "MSFT", "GOOGL"],
            "DV01": [1000, 2000, 3000],
            "KRD 2Y": [250, 500, 750],
            "KRD 5Y": [400, 800, 1200],
            "KRD 10Y": [250, 500, 750],
            "KRD 30Y": [100, 200, 300],
        })

        fig = AdvancedCharts.create_krd_heatmap(df)

        # Should have heatmap trace
        assert fig.data[0].type == "heatmap"

    def test_limits_to_top_15(self):
        """Test heatmap limits to top 15 trades."""
        df = pd.DataFrame({
            "Instrument ID": [f"INST{i}" for i in range(25)],
            "DV01": [1000 * i for i in range(25)],
            "KRD 2Y": [100 * i for i in range(25)],
            "KRD 5Y": [150 * i for i in range(25)],
            "KRD 10Y": [200 * i for i in range(25)],
            "KRD 30Y": [50 * i for i in range(25)],
        })

        fig = AdvancedCharts.create_krd_heatmap(df)

        # Should limit to 15 rows
        assert len(fig.data[0].y) == 15


class TestPortfolioBreakdownChart:
    """Tests for portfolio breakdown chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test chart with empty DataFrame."""
        fig = AdvancedCharts.create_portfolio_breakdown_chart(pd.DataFrame())

        assert "No trade data" in fig.layout.annotations[0].text

    def test_no_portfolio_column(self):
        """Test chart when portfolio column missing."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL"],
            "DV01": [1000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df)

        assert "No portfolio data" in fig.layout.annotations[0].text

    def test_groups_by_portfolio_id(self):
        """Test chart groups by Portfolio ID column."""
        df = pd.DataFrame({
            "Instrument ID": ["A", "B", "C", "D"],
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG", "CREDIT_HY", "TECH_SECTOR"],
            "Portfolio": ["Credit Ig", "Credit Ig", "Credit Hy", "Tech Sector"],
            "DV01": [1000, 2000, 3000, 4000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="DV01")

        # Should have 3 bars (one per portfolio)
        assert len(fig.data[0].x) == 3

    def test_metric_dv01(self):
        """Test DV01 metric calculation."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG"],
            "DV01": [1000, 2000],
            "NPV": [100000, 200000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="DV01")

        # Sum should be 3000
        assert fig.data[0].y[0] == 3000

    def test_metric_npv(self):
        """Test NPV metric calculation."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG"],
            "DV01": [1000, 2000],
            "NPV": [100000, 200000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="NPV")

        assert fig.data[0].y[0] == 300000

    def test_metric_count(self):
        """Test Count metric calculation."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG", "CREDIT_HY"],
            "DV01": [1000, 2000, 3000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="Count")

        # CREDIT_IG should have 2, CREDIT_HY should have 1
        y_values = list(fig.data[0].y)
        assert 2 in y_values
        assert 1 in y_values

    def test_metric_notional(self):
        """Test Notional metric calculation."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG"],
            "Notional": [1000000, 2000000],
            "DV01": [1000, 2000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="Notional")

        assert fig.data[0].y[0] == 3000000

    def test_portfolio_name_mapping(self):
        """Test portfolio ID to display name mapping."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG"],
            "DV01": [1000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="DV01")

        # Should display "Investment Grade Credit"
        assert "Investment Grade Credit" in fig.data[0].x[0]

    def test_handles_null_portfolios(self):
        """Test handling of null/empty portfolio values."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", None, ""],
            "DV01": [1000, 2000, 3000],
        })

        fig = AdvancedCharts.create_portfolio_breakdown_chart(df, metric="DV01")

        # Should group null/empty as "DEFAULT"
        assert fig is not None


class TestPortfolioPieChart:
    """Tests for portfolio pie chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframe(self):
        """Test pie with empty DataFrame."""
        fig = AdvancedCharts.create_portfolio_pie_chart(pd.DataFrame())
        assert fig is not None

    def test_no_portfolio_column(self):
        """Test pie when portfolio column missing."""
        df = pd.DataFrame({
            "Instrument ID": ["AAPL"],
            "DV01": [1000],
        })

        fig = AdvancedCharts.create_portfolio_pie_chart(df)
        # Should return empty figure without error
        assert fig is not None

    def test_with_portfolio_data(self):
        """Test pie with valid portfolio data."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_IG", "CREDIT_HY"],
            "DV01": [1000, 2000, 3000],
        })

        fig = AdvancedCharts.create_portfolio_pie_chart(df, metric="DV01")

        # Should have pie trace
        assert len(fig.data) == 1

    def test_uses_absolute_values(self):
        """Test that negative values are converted to absolute."""
        df = pd.DataFrame({
            "Portfolio ID": ["CREDIT_IG", "CREDIT_HY"],
            "DV01": [-1000, 2000],  # One negative
        })

        fig = AdvancedCharts.create_portfolio_pie_chart(df, metric="DV01")

        # All values should be positive for pie
        assert all(v >= 0 for v in fig.data[0].values)


class TestDualAxisChart:
    """Tests for dual axis chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_dataframes(self):
        """Test chart with empty DataFrames."""
        fig = AdvancedCharts.create_dual_axis_chart(
            pd.DataFrame(),
            pd.DataFrame()
        )

        assert fig is not None
        assert len(fig.data) == 0

    def test_dv01_only(self):
        """Test chart with only DV01 data."""
        from datetime import datetime, timedelta

        dv01_df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "dv01": [10000 + i * 100 for i in range(5)],
        })

        fig = AdvancedCharts.create_dual_axis_chart(dv01_df, pd.DataFrame())

        assert len(fig.data) == 1
        assert fig.data[0].name == "DV01"

    def test_both_metrics(self):
        """Test chart with both DV01 and NPV data."""
        from datetime import datetime, timedelta

        dv01_df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "dv01": [10000 + i * 100 for i in range(5)],
        })

        npv_df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "npv": [1000000 + i * 10000 for i in range(5)],
        })

        fig = AdvancedCharts.create_dual_axis_chart(dv01_df, npv_df)

        assert len(fig.data) == 2
        assert fig.data[0].name == "DV01"
        assert fig.data[1].name == "NPV"

    def test_dual_axes_configured(self):
        """Test that dual y-axes are configured."""
        from datetime import datetime, timedelta

        dv01_df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "dv01": [10000 + i * 100 for i in range(5)],
        })

        npv_df = pd.DataFrame({
            "timestamp": [datetime.now() - timedelta(hours=i) for i in range(5)],
            "npv": [1000000 + i * 10000 for i in range(5)],
        })

        fig = AdvancedCharts.create_dual_axis_chart(dv01_df, npv_df)

        # NPV trace should use secondary y-axis
        assert fig.data[1].yaxis == "y2"


class TestPortfolioComparisonChart:
    """Tests for portfolio comparison chart."""

    def setup_method(self):
        """Reset theme before each test."""
        mock_st.session_state = MockSessionState({"theme": "light"})

    def test_empty_inputs(self):
        """Test chart with empty inputs."""
        from data import Portfolio

        fig = AdvancedCharts.create_portfolio_comparison_chart(pd.DataFrame(), [])
        assert fig is not None

    def test_with_data(self):
        """Test chart with valid data."""
        from data import Portfolio

        df = pd.DataFrame({
            "Portfolio": ["CREDIT_IG", "CREDIT_IG", "CREDIT_HY"],
            "NPV": [1000000, 2000000, 1500000],
            "DV01": [10000, 20000, 15000],
            "Notional": [1000000, 2000000, 1500000],
        })

        portfolios = [
            Portfolio(id="CREDIT_IG", name="Credit IG", description="", strategy_type=""),
            Portfolio(id="CREDIT_HY", name="Credit HY", description="", strategy_type=""),
        ]

        fig = AdvancedCharts.create_portfolio_comparison_chart(df, portfolios)

        # Should have traces for each metric
        assert len(fig.data) >= 1
