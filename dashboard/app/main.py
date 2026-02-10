"""Risk Monitor Dashboard V2 - Real-time streaming, table-first layout."""

import time
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd
from streamlit_autorefresh import st_autorefresh

from config import settings
from data import RiskDataFetcher, PortfolioService
from components.filters import PortfolioFilters
from components.charts import AdvancedCharts
from components.alerts import RiskAlerts
from components.themes import ThemeManager
from utils.export import ExcelExporter
from utils.issuer_mapping import extract_issuer_name


# Page configuration
st.set_page_config(
    page_title="Fixed Income Risk Monitor",
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


def get_status_indicator(connected: bool, updated_at: int) -> tuple[str, bool]:
    """Return (label, is_live) for the header badge."""
    if not connected:
        return "Disconnected", False
    if updated_at == 0:
        return "Waiting for data...", False
    age_seconds = (time.time() * 1000 - updated_at) / 1000
    if age_seconds < 10:
        return "Live", True
    elif age_seconds < 60:
        return f"{int(age_seconds)}s ago", False
    else:
        return f"{int(age_seconds / 60)}m ago", False


def render_live_badge(label: str, is_live: bool):
    """Render the pulsing LIVE / STALE badge in the header."""
    if is_live:
        html = (
            '<div class="live-banner live">'
            '<div class="live-dot"></div>'
            f'LIVE STREAMING &nbsp;|&nbsp; {datetime.now().strftime("%H:%M:%S")}'
            "</div>"
        )
    else:
        html = (
            '<div class="live-banner stale">'
            f'DATA {label.upper()} &nbsp;|&nbsp; {datetime.now().strftime("%H:%M:%S")}'
            "</div>"
        )
    st.markdown(html, unsafe_allow_html=True)


def render_sidebar(fetcher, aggregates, trades_df, portfolios):
    """Render sidebar with all controls."""
    theme_manager = ThemeManager()
    theme_manager.render_toggle()
    theme_manager.apply_theme()

    st.sidebar.divider()

    filters_manager = PortfolioFilters()
    active_filters = filters_manager.render_sidebar(portfolios=portfolios)

    st.sidebar.divider()
    start_date, end_date = filters_manager.render_date_selector()
    st.sidebar.divider()

    alert_manager = RiskAlerts()
    alert_manager.configure_limits()
    filters_manager.render_apply_buttons()

    st.sidebar.divider()
    st.sidebar.subheader("Export Data")
    if aggregates and not trades_df.empty:
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
    """Main dashboard renderer — V2 layout."""
    # ── data layer ──────────────────────────────────────────────────
    portfolio_service = PortfolioService(settings.security_master_url)
    fetcher = RiskDataFetcher(
        settings.redis_host, settings.redis_port, portfolio_service=portfolio_service
    )
    connected = fetcher.is_connected()
    aggregates = fetcher.get_portfolio_aggregates() if connected else None
    portfolios = portfolio_service.get_portfolios()
    trades_df = fetcher.get_trades_dataframe() if connected else pd.DataFrame()

    # ── sidebar ─────────────────────────────────────────────────────
    active_filters, start_date, end_date, alert_manager, filters_manager = render_sidebar(
        fetcher, aggregates, trades_df, portfolios
    )

    filtered_trades_df = (
        filters_manager.apply_filters(trades_df, active_filters)
        if not trades_df.empty
        else trades_df
    )

    selected_portfolio_id = active_filters.get("portfolio", "ALL")
    selected_portfolio = None
    if selected_portfolio_id != "ALL":
        for p in portfolios:
            if p.id == selected_portfolio_id:
                selected_portfolio = p
                break

    # ================================================================
    # 1. HEADER — title + live badge
    # ================================================================
    col1, col2 = st.columns([3, 1])
    with col1:
        title = "Fixed Income Risk Monitor"
        if selected_portfolio:
            title = f"Risk Monitor — {selected_portfolio.name}"
        st.title(title)
    with col2:
        updated_at = aggregates.updated_at if aggregates else 0
        label, is_live = get_status_indicator(connected, updated_at)
        render_live_badge(label, is_live)

    if not connected:
        st.error("Unable to connect to Redis. Please check the connection.")
        return
    if not aggregates:
        st.warning("No risk data available. Waiting for risk engine to publish data...")
        return

    # ── store historical snapshot ───────────────────────────────────
    fetcher.store_historical_snapshot(aggregates.total_dv01, aggregates.total_npv)

    # ================================================================
    # 2. RISK ALERTS
    # ================================================================
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

    # ================================================================
    # 3. PORTFOLIO SUMMARY METRICS (with deltas)
    # ================================================================
    st.divider()
    if not filtered_trades_df.empty:
        filt_count = len(filtered_trades_df)
        filt_npv = filtered_trades_df["NPV"].sum()
        filt_dv01 = filtered_trades_df["DV01"].sum()
        filt_notional = (
            filtered_trades_df["Notional"].sum()
            if "Notional" in filtered_trades_df.columns
            else 0
        )
    else:
        filt_count = aggregates.instrument_count
        filt_npv = aggregates.total_npv
        filt_dv01 = aggregates.total_dv01
        filt_notional = 0

    # Delta tracking
    prev_dv01 = st.session_state.get("prev_dv01")
    prev_npv = st.session_state.get("prev_npv")
    st.session_state.prev_dv01 = filt_dv01
    st.session_state.prev_npv = filt_npv

    summary_title = "Portfolio Summary"
    if selected_portfolio:
        summary_title = f"Portfolio: {selected_portfolio.name}"
    st.subheader(summary_title)

    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.metric(
            "Instruments",
            f"{filt_count:,}",
            delta=f"of {aggregates.instrument_count:,} total" if selected_portfolio else None,
        )
    with c2:
        st.metric(
            "Total Notional",
            format_currency(filt_notional) if filt_notional else "N/A",
        )
    with c3:
        npv_delta = None
        if prev_npv is not None:
            d = filt_npv - prev_npv
            if abs(d) > 0.5:
                npv_delta = f"${d:+,.0f}"
        st.metric("Total NPV", format_currency(filt_npv), delta=npv_delta)
    with c4:
        dv01_delta = None
        if prev_dv01 is not None:
            d = filt_dv01 - prev_dv01
            if abs(d) > 0.5:
                dv01_delta = f"${d:+,.0f}"
        st.metric(
            "Total DV01",
            format_currency(filt_dv01),
            delta=dv01_delta,
            delta_color="inverse",
        )
    with c5:
        last_update = datetime.fromtimestamp(aggregates.updated_at / 1000)
        st.metric("Last Update", last_update.strftime("%H:%M:%S"))

    # ================================================================
    # 4. LIVE MONITORS — DV01 sparkline + Yield Curve
    # ================================================================
    st.divider()
    live_col1, live_col2 = st.columns(2)

    with live_col1:
        st.subheader("Live DV01 Monitor")
        hist_mini = fetcher.get_historical_dv01(
            datetime.now() - timedelta(minutes=5), datetime.now()
        )
        if not hist_mini.empty and len(hist_mini) > 1:
            mini_chart = AdvancedCharts.create_mini_live_chart(hist_mini)
            st.plotly_chart(mini_chart, use_container_width=True, key="live_dv01")
        else:
            st.info("Building real-time history...")

    with live_col2:
        st.subheader("Live Yield Curve")
        yield_rates = fetcher.get_yield_curve_latest()
        if yield_rates:
            yc_chart = AdvancedCharts.create_yield_curve_chart(yield_rates)
            st.plotly_chart(yc_chart, use_container_width=True, key="live_yc")
        else:
            st.info("Waiting for yield curve data...")

    # Yield curve time series (rates over time)
    yc_history = fetcher.get_yield_curve_history(minutes=30)
    if not yc_history.empty and len(yc_history) > 1:
        st.plotly_chart(
            AdvancedCharts.create_yield_curve_timeseries(yc_history),
            use_container_width=True,
            key="yc_ts",
        )

    # ================================================================
    # 5. PORTFOLIO BREAKDOWN (when viewing all)
    # ================================================================
    if selected_portfolio_id == "ALL" and not trades_df.empty and portfolios:
        st.divider()
        st.subheader("Portfolio Breakdown")
        metric_col, _ = st.columns([1, 3])
        with metric_col:
            breakdown_metric = st.selectbox(
                "View by",
                options=["DV01", "NPV", "Notional", "Count"],
                index=0,
                key="breakdown_metric",
            )
        b1, b2 = st.columns(2)
        with b1:
            st.plotly_chart(
                AdvancedCharts.create_portfolio_breakdown_chart(trades_df, metric=breakdown_metric),
                use_container_width=True,
            )
        with b2:
            st.plotly_chart(
                AdvancedCharts.create_portfolio_pie_chart(trades_df, metric=breakdown_metric),
                use_container_width=True,
            )

    # ================================================================
    # 6. PORTFOLIO HOLDINGS TABLE (manager's primary view)
    # ================================================================
    st.divider()
    st.subheader("Portfolio Holdings")

    # Inline portfolio selector for the table
    hold_col1, hold_col2 = st.columns([1, 3])
    with hold_col1:
        table_portfolio_options = ["All Portfolios"]
        table_portfolio_map = {"All Portfolios": "ALL"}
        for p in portfolios:
            label = f"{p.name} ({p.bond_count})"
            table_portfolio_options.append(label)
            table_portfolio_map[label] = p.id

        # Sync default with sidebar selection
        default_idx = 0
        if selected_portfolio:
            for i, opt in enumerate(table_portfolio_options):
                if table_portfolio_map.get(opt) == selected_portfolio.id:
                    default_idx = i
                    break

        table_portfolio_choice = st.selectbox(
            "Select Portfolio",
            options=table_portfolio_options,
            index=default_idx,
            key="holdings_portfolio",
        )
        table_pid = table_portfolio_map.get(table_portfolio_choice, "ALL")

    # Apply holdings-level filter
    if table_pid != "ALL" and not trades_df.empty:
        holdings_df = trades_df[trades_df["Portfolio ID"] == table_pid].copy() if "Portfolio ID" in trades_df.columns else filtered_trades_df
    else:
        holdings_df = filtered_trades_df

    if not holdings_df.empty:
        display_df = holdings_df.copy()

        # Issuer column from ISIN
        if "ISIN" in display_df.columns:
            display_df["Issuer"] = display_df["ISIN"].apply(
                lambda x: extract_issuer_name(x) if x else "Unknown"
            )
        else:
            display_df["Issuer"] = "Corporate Bond"

        column_order = [
            "Issuer", "Portfolio", "Type", "Currency", "Notional",
            "Coupon", "NPV", "DV01", "KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y",
        ]
        display_columns = [c for c in column_order if c in display_df.columns]
        table_df = display_df[display_columns].copy()

        # Format currency columns
        for col in ["Notional", "NPV", "DV01", "KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]:
            if col in table_df.columns:
                table_df[col] = table_df[col].apply(lambda x: f"${x:,.2f}")
        if "Coupon" in table_df.columns:
            table_df["Coupon"] = table_df["Coupon"].apply(
                lambda x: f"{x * 100:.3f}%" if x > 0 else "-"
            )

        # Summary row above table — computed from holdings_df (unformatted)
        h_npv = holdings_df["NPV"].sum()
        h_dv01 = holdings_df["DV01"].sum()
        h_notional = holdings_df["Notional"].sum() if "Notional" in holdings_df.columns else 0

        tc1, tc2, tc3, tc4 = st.columns(4)
        with tc1:
            st.metric("Positions", f"{len(table_df):,}")
        with tc2:
            st.metric("Total Notional", f"${h_notional / 1e9:.2f}B")
        with tc3:
            st.metric("Total NPV", format_currency(h_npv))
        with tc4:
            st.metric("Total DV01", format_currency(h_dv01))

        st.dataframe(
            table_df,
            use_container_width=True,
            hide_index=True,
            height=500,
        )

        csv = table_df.to_csv(index=False)
        col_dl, col_info = st.columns([1, 4])
        with col_dl:
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )
        with col_info:
            st.caption(
                f"Showing {len(table_df):,} of {len(trades_df):,} instruments | "
                f"Last updated: {datetime.now().strftime('%H:%M:%S')}"
            )
    else:
        st.info("No positions in selected portfolio or all filtered out")

    # ================================================================
    # 7. RISK ANALYTICS & VISUALIZATIONS (after table)
    # ================================================================
    st.divider()
    st.subheader("Risk Analytics")

    # KRD profile + Risk Distribution
    v1, v2 = st.columns(2)
    with v1:
        st.markdown("**Key Rate Duration Profile**")
        krd_data = pd.DataFrame({
            "Tenor": ["2Y", "5Y", "10Y", "30Y"],
            "KRD": [aggregates.krd_2y, aggregates.krd_5y, aggregates.krd_10y, aggregates.krd_30y],
        })
        st.bar_chart(krd_data.set_index("Tenor"), use_container_width=True, color="#4CAF50")

    with v2:
        st.markdown("**Risk Distribution by Issuer**")
        if not filtered_trades_df.empty:
            dist_df = filtered_trades_df.copy()
            if "ISIN" in dist_df.columns:
                dist_df["Issuer"] = dist_df["ISIN"].apply(
                    lambda x: extract_issuer_name(x) if x else "Unknown"
                )
            else:
                dist_df["Issuer"] = dist_df["Instrument ID"]
            dv01_by_issuer = dist_df[["Issuer", "DV01"]].copy()
            dv01_by_issuer["DV01 Abs"] = dv01_by_issuer["DV01"].abs()
            dv01_by_issuer = dv01_by_issuer.sort_values("DV01 Abs", ascending=False)
            st.bar_chart(
                dv01_by_issuer.set_index("Issuer")["DV01"],
                use_container_width=True,
                color="#2196F3",
            )
        else:
            st.info("No trade-level data available")

    # Concentration
    st.divider()
    st.subheader("Concentration Risk Analysis")
    cr1, cr2 = st.columns(2)
    with cr1:
        st.plotly_chart(
            AdvancedCharts.create_concentration_chart(filtered_trades_df, top_n=10),
            use_container_width=True,
        )
    with cr2:
        st.plotly_chart(
            AdvancedCharts.create_concentration_pie(filtered_trades_df, top_n=5),
            use_container_width=True,
        )

    # Heatmap
    st.divider()
    st.subheader("Risk Heatmap Analysis")
    st.plotly_chart(
        AdvancedCharts.create_krd_heatmap(filtered_trades_df), use_container_width=True
    )

    # Historical
    st.divider()
    st.subheader("Historical Risk Analysis")
    historical_dv01 = fetcher.get_historical_dv01(start_date, end_date)
    historical_npv = fetcher.get_historical_npv(start_date, end_date)
    if not historical_dv01.empty:
        h1, h2 = st.columns(2)
        with h1:
            st.plotly_chart(
                AdvancedCharts.create_historical_dv01_chart(historical_dv01),
                use_container_width=True,
            )
        with h2:
            st.plotly_chart(
                AdvancedCharts.create_dual_axis_chart(historical_dv01, historical_npv),
                use_container_width=True,
            )
    else:
        st.info(
            "No historical data available for selected date range. "
            "Historical data will accumulate as the dashboard runs."
        )

    # Footer
    st.divider()
    st.caption(
        f"Risk Monitor Dashboard v2 | "
        f"Refresh interval: {settings.refresh_interval}s | "
        f"Data source: Redis @ {settings.redis_host}:{settings.redis_port}"
    )


def main():
    """Main entry point."""
    # Auto-refresh using streamlit-autorefresh (avoids recursion issues)
    st_autorefresh(interval=settings.refresh_interval * 1000, key="data_refresh")
    render_dashboard()


if __name__ == "__main__":
    main()
