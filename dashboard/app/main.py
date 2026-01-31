"""Risk Monitor Dashboard - Streamlit Application."""

import time
from datetime import datetime

import streamlit as st
import pandas as pd

from app.config import settings
from app.data import RiskDataFetcher, PortfolioAggregates


# Page configuration
st.set_page_config(
    page_title="Risk Monitor",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background-color: #1e1e1e;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
    }
    .big-number {
        font-size: 2.5em;
        font-weight: bold;
    }
    .positive { color: #00cc00; }
    .negative { color: #ff4444; }
</style>
""", unsafe_allow_html=True)


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
        return "🔴 Disconnected"

    if updated_at == 0:
        return "🟡 Waiting for data..."

    age_seconds = (time.time() * 1000 - updated_at) / 1000
    if age_seconds < 10:
        return "🟢 Live"
    elif age_seconds < 60:
        return f"🟡 {int(age_seconds)}s ago"
    else:
        return f"🔴 {int(age_seconds/60)}m ago"


def render_dashboard():
    """Render the main dashboard."""
    # Initialize data fetcher
    fetcher = RiskDataFetcher(settings.redis_host, settings.redis_port)

    # Header
    col1, col2 = st.columns([3, 1])
    with col1:
        st.title("📊 Fixed Income Risk Monitor")
    with col2:
        connected = fetcher.is_connected()
        aggregates = fetcher.get_portfolio_aggregates() if connected else None
        updated_at = aggregates.updated_at if aggregates else 0
        status = get_status_indicator(connected, updated_at)
        st.markdown(f"### {status}")

    st.divider()

    if not connected:
        st.error("Unable to connect to Redis. Please check the connection.")
        return

    if not aggregates:
        st.warning("No risk data available. Waiting for risk engine to publish data...")
        return

    # Portfolio Summary
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

    st.divider()

    # Charts row
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Key Rate Duration Profile")

        krd_data = pd.DataFrame({
            "Tenor": ["2Y", "5Y", "10Y", "30Y"],
            "KRD": [
                aggregates.krd_2y,
                aggregates.krd_5y,
                aggregates.krd_10y,
                aggregates.krd_30y,
            ]
        })

        st.bar_chart(
            krd_data.set_index("Tenor"),
            use_container_width=True,
            color="#4CAF50",
        )

    with col2:
        st.subheader("Risk Distribution")

        # Get trade-level data
        trades_df = fetcher.get_trades_dataframe()

        if not trades_df.empty:
            # DV01 distribution
            dv01_by_trade = trades_df[["Instrument ID", "DV01"]].copy()
            dv01_by_trade["DV01 Abs"] = dv01_by_trade["DV01"].abs()
            dv01_by_trade = dv01_by_trade.sort_values("DV01 Abs", ascending=False)

            st.bar_chart(
                dv01_by_trade.set_index("Instrument ID")["DV01"],
                use_container_width=True,
                color="#2196F3",
            )
        else:
            st.info("No trade-level data available")

    st.divider()

    # Trade-level details
    st.subheader("Trade-Level Risk Details")

    trades_df = fetcher.get_trades_dataframe()

    if not trades_df.empty:
        # Format numbers for display
        display_df = trades_df.copy()
        for col in ["NPV", "DV01", "KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]:
            display_df[col] = display_df[col].apply(lambda x: f"${x:,.2f}")

        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No trade data available")

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
