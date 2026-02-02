"""Risk alert components."""

import streamlit as st
from typing import Dict


class RiskAlerts:
    """Manages risk limit alerts."""

    def __init__(self):
        """Initialize with default limits."""
        if "risk_limits" not in st.session_state:
            st.session_state.risk_limits = {
                "dv01_limit": 2_000_000,
                "npv_limit": 1_000_000_000,
                "concentration_limit": 0.20,  # 20% max in single trade
            }

    def configure_limits(self):
        """Render limit configuration in sidebar."""
        st.sidebar.subheader("Risk Limits")

        dv01_limit = st.sidebar.number_input(
            "DV01 Limit ($)",
            min_value=0,
            value=st.session_state.risk_limits["dv01_limit"],
            step=100_000,
            help="Alert when portfolio DV01 exceeds this value",
        )

        npv_limit = st.sidebar.number_input(
            "NPV Limit ($)",
            min_value=0,
            value=st.session_state.risk_limits["npv_limit"],
            step=100_000_000,
            help="Alert when portfolio NPV exceeds this value",
        )

        concentration_limit = (
            st.sidebar.slider(
                "Concentration Limit (%)",
                min_value=0,
                max_value=100,
                value=int(st.session_state.risk_limits["concentration_limit"] * 100),
                help="Alert when single trade exceeds this % of total DV01",
            )
            / 100
        )

        st.session_state.risk_limits = {
            "dv01_limit": dv01_limit,
            "npv_limit": npv_limit,
            "concentration_limit": concentration_limit,
        }

    def check_limits(
        self, total_dv01: float, total_npv: float, max_trade_dv01: float
    ) -> Dict[str, bool]:
        """
        Check if any limits are breached.

        Args:
            total_dv01: Total portfolio DV01
            total_npv: Total portfolio NPV
            max_trade_dv01: Largest single trade DV01

        Returns:
            Dict of limit_name: is_breached
        """
        limits = st.session_state.risk_limits

        breaches = {
            "dv01": abs(total_dv01) > limits["dv01_limit"],
            "npv": abs(total_npv) > limits["npv_limit"],
            "concentration": (
                (abs(max_trade_dv01) / abs(total_dv01)) > limits["concentration_limit"]
                if total_dv01 != 0
                else False
            ),
        }

        return breaches

    def render_alerts(
        self,
        total_dv01: float,
        total_npv: float,
        max_trade_dv01: float,
        max_trade_id: str = "",
    ):
        """
        Render alert banners for breached limits.

        Args:
            total_dv01: Total portfolio DV01
            total_npv: Total portfolio NPV
            max_trade_dv01: Largest single trade DV01
            max_trade_id: ID of largest trade
        """
        breaches = self.check_limits(total_dv01, total_npv, max_trade_dv01)
        limits = st.session_state.risk_limits

        alert_shown = False

        # DV01 limit breach
        if breaches["dv01"]:
            st.error(
                f"**DV01 LIMIT BREACH** | "
                f"Portfolio DV01: ${abs(total_dv01):,.0f} | "
                f"Limit: ${limits['dv01_limit']:,.0f} | "
                f"Excess: ${abs(total_dv01) - limits['dv01_limit']:,.0f}"
            )
            alert_shown = True

        # NPV limit breach
        if breaches["npv"]:
            st.error(
                f"**NPV LIMIT BREACH** | "
                f"Portfolio NPV: ${abs(total_npv):,.0f} | "
                f"Limit: ${limits['npv_limit']:,.0f} | "
                f"Excess: ${abs(total_npv) - limits['npv_limit']:,.0f}"
            )
            alert_shown = True

        # Concentration limit breach
        if breaches["concentration"] and total_dv01 != 0:
            concentration_pct = (abs(max_trade_dv01) / abs(total_dv01)) * 100
            st.warning(
                f"**CONCENTRATION RISK** | "
                f"Single trade ({max_trade_id[:8]}...) represents {concentration_pct:.1f}% of portfolio DV01 | "
                f"Limit: {limits['concentration_limit']*100:.0f}%"
            )
            alert_shown = True

        # All clear message
        if not alert_shown:
            st.success("All risk limits within acceptable ranges")
