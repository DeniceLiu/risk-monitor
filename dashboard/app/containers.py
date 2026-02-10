"""Container management for flash-free dashboard updates."""

import streamlit as st
from dataclasses import dataclass


@dataclass
class DashboardContainers:
    """
    All dashboard containers for in-place updates.
    
    These st.empty() containers are created once and updated in-place,
    preventing the white flash from page reloads.
    
    Order matches visual layout from top to bottom.
    """
    header: st.delta_generator.DeltaGenerator
    alerts: st.delta_generator.DeltaGenerator
    summary_metrics: st.delta_generator.DeltaGenerator
    live_monitors: st.delta_generator.DeltaGenerator
    holdings_table: st.delta_generator.DeltaGenerator
    risk_analytics: st.delta_generator.DeltaGenerator
    portfolio_breakdown: st.delta_generator.DeltaGenerator
    concentration: st.delta_generator.DeltaGenerator
    heatmap: st.delta_generator.DeltaGenerator
    historical: st.delta_generator.DeltaGenerator
    footer: st.delta_generator.DeltaGenerator


def create_container_structure() -> DashboardContainers:
    """
    Create all placeholder containers once at startup.
    
    These containers will be updated in-place in the infinite loop,
    avoiding full page reloads and eliminating white flash.
    
    Order matches visual layout from top to bottom:
    1. Header (title + live badge)
    2. Alerts (risk limit warnings)
    3. Summary metrics (total NPV, DV01, etc.)
    4. Live monitors (DV01 ticker + yield curve)
    5. Holdings table (portfolio selector + data table)
    6. Risk analytics (KRD profile + issuer distribution)
    7. Portfolio breakdown (DV01 by portfolio charts)
    8. Concentration (top risk contributors)
    9. Heatmap (KRD by instrument)
    10. Historical (time series charts)
    11. Footer
    
    Returns:
        DashboardContainers: Object containing all empty containers
    """
    return DashboardContainers(
        header=st.empty(),
        alerts=st.empty(),
        summary_metrics=st.empty(),
        live_monitors=st.empty(),
        holdings_table=st.empty(),
        risk_analytics=st.empty(),
        portfolio_breakdown=st.empty(),
        concentration=st.empty(),
        heatmap=st.empty(),
        historical=st.empty(),
        footer=st.empty(),
    )
