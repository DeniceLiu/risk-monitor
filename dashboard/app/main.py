"""Risk Monitor Dashboard V2 - Flash-free real-time updates."""

import time
from datetime import datetime, timedelta

import streamlit as st
import pandas as pd

from config import settings
from data import RiskDataFetcher, PortfolioService
from components.filters import PortfolioFilters
from components.alerts import RiskAlerts
from components.themes import ThemeManager
from utils.export import ExcelExporter
from containers import create_container_structure
from updaters import (
    update_header,
    update_alerts,
    update_summary_metrics,
    update_live_monitors,
    update_portfolio_breakdown,
    update_holdings_table,
    update_risk_analytics,
    update_concentration,
    update_heatmap,
    update_historical,
    update_footer,
)


# Page configuration
st.set_page_config(
    page_title="Fixed Income Risk Monitor",
    page_icon="💹",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Apply anti-flash CSS immediately
st.markdown("""
<style>
    /* Prevent white flash during auto-refresh */
    html, body {
        background-color: #0e1117 !important;
        transition: none !important;
    }
    
    .stApp {
        background-color: #0e1117 !important;
    }
</style>
""", unsafe_allow_html=True)


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


def setup_sidebar(portfolio_service):
    """
    Set up sidebar controls (called once at startup).
    
    Returns:
        Tuple of (portfolios, filters_manager, alert_manager, start_date, end_date)
    """
    # Get portfolios
    portfolios = portfolio_service.get_portfolios()
    
    # Theme toggle
    theme_manager = ThemeManager()
    theme_manager.render_toggle()
    theme_manager.apply_theme()
    
    st.sidebar.divider()
    
    # Filters
    filters_manager = PortfolioFilters()
    filters_manager.render_sidebar(portfolios=portfolios)
    
    st.sidebar.divider()
    
    # Date selector
    start_date, end_date = filters_manager.render_date_selector()
    
    st.sidebar.divider()
    
    # Alerts configuration
    alert_manager = RiskAlerts()
    alert_manager.configure_limits()
    filters_manager.render_apply_buttons()
    
    st.sidebar.divider()
    
    # Export placeholder (will update in loop)
    st.sidebar.subheader("Export Data")
    export_placeholder = st.sidebar.empty()
    
    return portfolios, filters_manager, alert_manager, start_date, end_date, export_placeholder


def main():
    """
    Main entry point - flash-free dashboard using infinite loop.
    
    This approach eliminates white flash by:
    1. Creating all containers once at startup
    2. Updating containers in-place in an infinite loop
    3. Never calling st.rerun() which causes page reload
    """
    
    # ========================================
    # ONE-TIME SETUP
    # ========================================
    
    # Initialize services
    portfolio_service = PortfolioService(settings.security_master_url)
    
    # Create all containers ONCE
    containers = create_container_structure()
    
    # Set up sidebar ONCE
    portfolios, filters_manager, alert_manager, start_date, end_date, export_placeholder = \
        setup_sidebar(portfolio_service)
    
    # ========================================
    # INFINITE UPDATE LOOP (NO RELOAD!)
    # ========================================
    
    refresh_count = 0
    
    while True:  # ← Never exits, no page reload!
        try:
            refresh_count += 1
            
            # ── Fetch fresh data ──
            fetcher = RiskDataFetcher(
                settings.redis_host,
                settings.redis_port,
                portfolio_service=portfolio_service
            )
            
            connected = fetcher.is_connected()
            aggregates = fetcher.get_portfolio_aggregates() if connected else None
            trades_df = fetcher.get_trades_dataframe() if connected else pd.DataFrame()
            
            # Check connection
            if not connected:
                with containers.header.container():
                    st.error("Unable to connect to Redis. Please check the connection.")
                time.sleep(settings.refresh_interval)
                continue
            
            if not aggregates:
                with containers.header.container():
                    st.warning("No risk data available. Waiting for risk engine to publish data...")
                time.sleep(settings.refresh_interval)
                continue
            
            # Store historical snapshot
            fetcher.store_historical_snapshot(aggregates.total_dv01, aggregates.total_npv)
            
            # ── Get active filters from session state ──
            active_filters = {
                "portfolio": st.session_state.get("portfolio_filter", "ALL"),
                "instrument_type": st.session_state.get("instrument_type_filter", "ALL"),
                "currency": st.session_state.get("currency_filter", "ALL"),
            }
            
            # Apply filters
            filtered_trades_df = (
                filters_manager.apply_filters(trades_df, active_filters)
                if not trades_df.empty else trades_df
            )
            
            # Get selected portfolio
            selected_portfolio_id = active_filters.get("portfolio", "ALL")
            selected_portfolio = None
            if selected_portfolio_id != "ALL":
                for p in portfolios:
                    if p.id == selected_portfolio_id:
                        selected_portfolio = p
                        break
            
            # ── Update all containers in-place ──
            
            update_header(
                containers.header,
                connected,
                aggregates.updated_at,
                selected_portfolio
            )
            
            update_alerts(
                containers.alerts,
                alert_manager,
                aggregates,
                trades_df
            )
            
            update_summary_metrics(
                containers.summary_metrics,
                aggregates,
                filtered_trades_df,
                selected_portfolio
            )
            
            update_live_monitors(
                containers.live_monitors,
                fetcher,
                refresh_count
            )
            
            update_portfolio_breakdown(
                containers.portfolio_breakdown,
                trades_df,
                portfolios,
                selected_portfolio_id,
                refresh_count
            )
            
            update_holdings_table(
                containers.holdings_table,
                filtered_trades_df,
                trades_df,
                portfolios,
                refresh_count
            )
            
            # Update charts every refresh (they're fast enough)
            update_risk_analytics(
                containers.risk_analytics,
                filtered_trades_df,
                aggregates,
                refresh_count
            )
            
            update_concentration(
                containers.concentration,
                filtered_trades_df,
                refresh_count
            )
            
            update_heatmap(
                containers.heatmap,
                filtered_trades_df,
                refresh_count
            )
            
            update_historical(
                containers.historical,
                fetcher,
                start_date,
                end_date,
                refresh_count
            )
            
            update_footer(
                containers.footer,
                settings
            )
            
            # ── Update export button ──
            if aggregates and not trades_df.empty:
                with export_placeholder.container():
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
                    st.download_button(
                        label="Download Excel Report",
                        data=excel_file,
                        file_name=f"portfolio_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        key=f"excel_export_{refresh_count}",
                    )
            
        except Exception as e:
            # Handle errors gracefully without crashing
            with containers.header.container():
                st.error(f"Update error: {e}")
        
        # ========================================
        # SLEEP (NO RELOAD!)
        # ========================================
        
        time.sleep(settings.refresh_interval)  # ← Just wait, don't reload!


if __name__ == "__main__":
    main()
