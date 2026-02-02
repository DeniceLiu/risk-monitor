"""Risk Monitor Dashboard - Streamlit Application with Enhanced Features."""

import time
from datetime import datetime

import streamlit as st
import pandas as pd

from config import settings
from data import RiskDataFetcher
from components.filters import PortfolioFilters
from components.charts import AdvancedCharts
from components.alerts import RiskAlerts
from components.themes import ThemeManager
from utils.export import ExcelExporter


# Page configuration
st.set_page_config(
    page_title="Risk Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)


def format_currency(value: float, decimals: int = 0) -> str:
    """Format a number as currency."""
    if abs(value) >= 1_000_000:
        return f"${value/1_000_000:,.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"${value/1_000:,.{decimals}f}K"
    else:
        return f"${value:,.{decimals}f}"


def get_status_indicator(connected: bool, updated_at: int) -> str:
    """Get status indicator based on connection and freshness."""
    if not connected:
        return "Disconnected"

    if updated_at == 0:
        return "Waiting for data..."

    age_seconds = (time.time() * 1000 - updated_at) / 1000
    if age_seconds < 10:
        return "Live"
    elif age_seconds < 60:
        return f"{int(age_seconds)}s ago"
    else:
        return f"{int(age_seconds/60)}m ago"


def render_sidebar(fetcher: RiskDataFetcher, aggregates, trades_df: pd.DataFrame):
    """Render sidebar with all controls."""
    # Theme toggle
    theme_manager = ThemeManager()
    theme_manager.render_toggle()
    theme_manager.apply_theme()

    st.sidebar.divider()

    # Filters
    filters_manager = PortfolioFilters()
    active_filters = filters_manager.render_sidebar()

    st.sidebar.divider()

    # Date range selector
    start_date, end_date = filters_manager.render_date_selector()

    st.sidebar.divider()

    # Risk limits configuration
    alert_manager = RiskAlerts()
    alert_manager.configure_limits()

    # Apply All / Reset All buttons (unified for filters, date range, and risk limits)
    filters_manager.render_apply_buttons()

    st.sidebar.divider()

    # Export section
    st.sidebar.subheader("Export Data")

    if aggregates and not trades_df.empty:
        # Generate Excel file
        excel_file = ExcelExporter.create_portfolio_export(
            trades_df,
            {
                "instrument_count": aggregates.instrument_count,
                "total_npv": aggregates.total_npv,
                "total_dv01": aggregates.total_dv01,
                "krd_2y": aggregates.krd_2y,
                "krd_5y": aggregates.krd_5y,
                "krd_10y": aggregates.krd_10y,
                "krd_30y": aggregates.krd_30y,
            },
        )

        st.sidebar.download_button(
            label="Download Excel Report",
            data=excel_file,
            file_name=f"portfolio_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

    return active_filters, start_date, end_date, alert_manager, filters_manager


def render_dashboard():
    """Render the main dashboard."""
    # Initialize data fetcher
    fetcher = RiskDataFetcher(settings.redis_host, settings.redis_port)

    # Check connection
    connected = fetcher.is_connected()
    aggregates = fetcher.get_portfolio_aggregates() if connected else None

    # Get trades data
    trades_df = fetcher.get_trades_dataframe() if connected else pd.DataFrame()

    # Render sidebar and get settings
    active_filters, start_date, end_date, alert_manager, filters_manager = render_sidebar(
        fetcher, aggregates, trades_df
    )

    # Apply filters to trades
    if not trades_df.empty:
        filtered_trades_df = filters_manager.apply_filters(trades_df, active_filters)
    else:
        filtered_trades_df = trades_df

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("Fixed Income Risk Monitor")
    with col2:
        updated_at = aggregates.updated_at if aggregates else 0
        status = get_status_indicator(connected, updated_at)

        if "Live" in status:
            st.success(f"Status: {status}")
        elif "Disconnected" in status or "ago" in status:
            st.warning(f"Status: {status}")
        else:
            st.info(f"Status: {status}")

    # Connection error handling
    if not connected:
        st.error("Unable to connect to Redis. Please check the connection.")
        return

    if not aggregates:
        st.warning("No risk data available. Waiting for risk engine to publish data...")
        return

    # Risk Alerts section
    st.divider()
    if not trades_df.empty:
        max_idx = trades_df["DV01"].abs().idxmax()
        max_trade_dv01 = trades_df.loc[max_idx, "DV01"]
        max_trade_id = trades_df.loc[max_idx, "Full ID"]
    else:
        max_trade_dv01 = 0
        max_trade_id = ""

    alert_manager.render_alerts(
        aggregates.total_dv01, aggregates.total_npv, max_trade_dv01, max_trade_id
    )

    # Portfolio Summary
    st.divider()
    st.subheader("Portfolio Summary")
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.metric(
            label="Instruments",
            value=f"{aggregates.instrument_count}",
        )

    with col2:
        st.metric(
            label="Total NPV",
            value=format_currency(aggregates.total_npv),
        )

    with col3:
        dv01_color = "inverse" if aggregates.total_dv01 < 0 else "normal"
        st.metric(
            label="Total DV01",
            value=format_currency(aggregates.total_dv01),
            delta=f"{'Long' if aggregates.total_dv01 > 0 else 'Short'} duration",
            delta_color=dv01_color,
        )

    with col4:
        last_update = datetime.fromtimestamp(aggregates.updated_at / 1000)
        st.metric(
            label="Last Update",
            value=last_update.strftime("%H:%M:%S"),
        )

    # Store historical data snapshot
    fetcher.store_historical_snapshot(aggregates.total_dv01, aggregates.total_npv)

    # Charts row
    st.divider()
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Key Rate Duration Profile")

        krd_data = pd.DataFrame(
            {
                "Tenor": ["2Y", "5Y", "10Y", "30Y"],
                "KRD": [
                    aggregates.krd_2y,
                    aggregates.krd_5y,
                    aggregates.krd_10y,
                    aggregates.krd_30y,
                ],
            }
        )

        st.bar_chart(
            krd_data.set_index("Tenor"),
            use_container_width=True,
            color="#4CAF50",
        )

    with col2:
        st.subheader("Risk Distribution")

        if not filtered_trades_df.empty:
            # DV01 distribution
            dv01_by_trade = filtered_trades_df[["Instrument ID", "DV01"]].copy()
            dv01_by_trade["DV01 Abs"] = dv01_by_trade["DV01"].abs()
            dv01_by_trade = dv01_by_trade.sort_values("DV01 Abs", ascending=False)

            st.bar_chart(
                dv01_by_trade.set_index("Instrument ID")["DV01"],
                use_container_width=True,
                color="#2196F3",
            )
        else:
            st.info("No trade-level data available")

    # Concentration Risk Analysis
    st.divider()
    st.subheader("Concentration Risk Analysis")

    col1, col2 = st.columns(2)

    with col1:
        concentration_chart = AdvancedCharts.create_concentration_chart(
            filtered_trades_df, top_n=10
        )
        st.plotly_chart(concentration_chart, use_container_width=True)

    with col2:
        concentration_pie = AdvancedCharts.create_concentration_pie(
            filtered_trades_df, top_n=5
        )
        st.plotly_chart(concentration_pie, use_container_width=True)

    # Risk Heatmap
    st.divider()
    st.subheader("Risk Heatmap Analysis")

    krd_heatmap = AdvancedCharts.create_krd_heatmap(filtered_trades_df)
    st.plotly_chart(krd_heatmap, use_container_width=True)

    # Historical Risk Analysis
    st.divider()
    st.subheader("Historical Risk Analysis")

    historical_dv01 = fetcher.get_historical_dv01(start_date, end_date)
    historical_npv = fetcher.get_historical_npv(start_date, end_date)

    if not historical_dv01.empty:
        col1, col2 = st.columns(2)

        with col1:
            dv01_chart = AdvancedCharts.create_historical_dv01_chart(historical_dv01)
            st.plotly_chart(dv01_chart, use_container_width=True)

        with col2:
            dual_chart = AdvancedCharts.create_dual_axis_chart(historical_dv01, historical_npv)
            st.plotly_chart(dual_chart, use_container_width=True)
    else:
        st.info(
            "No historical data available for selected date range. "
            "Historical data will accumulate as the dashboard runs."
        )

    # Trade-level details
    st.divider()
    st.subheader("Trade-Level Risk Details")

    if not filtered_trades_df.empty:
        # Format numbers for display
        display_df = filtered_trades_df.drop(columns=["Full ID"], errors="ignore").copy()
        for col in ["NPV", "DV01", "KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]:
            if col in display_df.columns:
                display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No trade data available (or all filtered out)")

    # Footer
    st.divider()
    st.caption(
        f"Risk Monitor Dashboard | "
        f"Refresh interval: {settings.refresh_interval}s | "
        f"Data source: Redis @ {settings.redis_host}:{settings.redis_port}"
    )


def main():
    """Main entry point."""
    render_dashboard()

    # Auto-refresh
    time.sleep(settings.refresh_interval)
    st.rerun()


if __name__ == "__main__":
    main()
