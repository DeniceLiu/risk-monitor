"""Dashboard filter components."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any, List, Optional


class PortfolioFilters:
    """Manages dashboard filters."""

    DEFAULT_FILTERS = {
        "portfolio": "ALL",
        "currencies": ["USD"],
        "instrument_types": ["BOND", "SWAP"],
        "maturity_min": 0,
        "maturity_max": 30,
        "dv01_min": 0,
    }

    DEFAULT_DATE_RANGE = {
        "preset": "Last Hour",
        "custom_start": None,
        "custom_end": None,
    }

    def __init__(self):
        """Initialize filter state."""
        # Applied filters (used for actual filtering)
        if "applied_filters" not in st.session_state:
            st.session_state.applied_filters = self.DEFAULT_FILTERS.copy()

        # Pending filters (current UI selections, not yet applied)
        if "pending_filters" not in st.session_state:
            st.session_state.pending_filters = self.DEFAULT_FILTERS.copy()

        # Applied date range
        if "applied_date_range" not in st.session_state:
            st.session_state.applied_date_range = self.DEFAULT_DATE_RANGE.copy()

        # Pending date range
        if "pending_date_range" not in st.session_state:
            st.session_state.pending_date_range = self.DEFAULT_DATE_RANGE.copy()

    def render_sidebar(self, portfolios: Optional[List] = None) -> Dict[str, Any]:
        """
        Render filter controls in sidebar.

        Args:
            portfolios: List of Portfolio objects from PortfolioService

        Returns:
            dict: Currently applied filter selections
        """
        st.sidebar.header("Filters")

        # Portfolio selector (prominent at top)
        portfolio_options = ["ALL"]
        portfolio_labels = {"ALL": "All Portfolios"}

        if portfolios:
            for p in portfolios:
                portfolio_options.append(p.id)
                portfolio_labels[p.id] = f"{p.name} ({p.bond_count})"

        current_portfolio = st.session_state.pending_filters.get("portfolio", "ALL")
        if current_portfolio not in portfolio_options:
            current_portfolio = "ALL"

        selected_portfolio = st.sidebar.selectbox(
            "Portfolio",
            options=portfolio_options,
            index=portfolio_options.index(current_portfolio),
            format_func=lambda x: portfolio_labels.get(x, x),
            help="Select a portfolio to view",
        )

        st.sidebar.divider()

        # Currency filter
        currencies = st.sidebar.multiselect(
            "Currency",
            options=["USD", "EUR", "GBP", "JPY"],
            default=st.session_state.pending_filters["currencies"],
            help="Select one or more currencies to display",
        )

        # Instrument type filter
        instrument_types = st.sidebar.multiselect(
            "Instrument Type",
            options=["BOND", "SWAP"],
            default=st.session_state.pending_filters["instrument_types"],
            help="Filter by instrument type",
        )

        # Maturity range slider
        st.sidebar.subheader("Years to Maturity")
        maturity_range = st.sidebar.slider(
            "Range",
            min_value=0,
            max_value=30,
            value=(
                st.session_state.pending_filters["maturity_min"],
                st.session_state.pending_filters["maturity_max"],
            ),
            help="Filter by years remaining to maturity",
        )

        # DV01 threshold filter
        dv01_min = st.sidebar.number_input(
            "Min DV01 to Display ($)",
            min_value=0,
            value=st.session_state.pending_filters["dv01_min"],
            step=1000,
            help="Only show trades with DV01 above this threshold",
        )

        # Update pending filters with current selections
        st.session_state.pending_filters = {
            "portfolio": selected_portfolio,
            "currencies": currencies if currencies else ["USD"],
            "instrument_types": instrument_types if instrument_types else ["BOND", "SWAP"],
            "maturity_min": maturity_range[0],
            "maturity_max": maturity_range[1],
            "dv01_min": dv01_min,
        }

        return st.session_state.applied_filters

    def render_date_selector(self) -> Tuple[datetime, datetime]:
        """
        Render date range selector.

        Returns:
            Tuple of (start_date, end_date) from applied settings
        """
        st.sidebar.subheader("Date Range")

        # Preset options
        preset = st.sidebar.selectbox(
            "Quick Select",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Custom"],
            index=["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Custom"].index(
                st.session_state.pending_date_range.get("preset", "Last Hour")
            ),
        )

        now = datetime.now()
        custom_start = None
        custom_end = None

        if preset == "Custom":
            col1, col2 = st.sidebar.columns(2)
            with col1:
                stored_start = st.session_state.pending_date_range.get("custom_start")
                default_start = stored_start if stored_start else (now - timedelta(days=7)).date()
                custom_start = st.date_input("From", value=default_start, max_value=now.date())
            with col2:
                stored_end = st.session_state.pending_date_range.get("custom_end")
                default_end = stored_end if stored_end else now.date()
                custom_end = st.date_input("To", value=default_end, max_value=now.date())

        # Update pending date range
        st.session_state.pending_date_range = {
            "preset": preset,
            "custom_start": custom_start,
            "custom_end": custom_end,
        }

        # Return applied date range
        return self._calculate_date_range(st.session_state.applied_date_range)

    def _calculate_date_range(self, date_config: Dict) -> Tuple[datetime, datetime]:
        """Calculate actual datetime range from config."""
        now = datetime.now()
        preset = date_config.get("preset", "Last Hour")

        if preset == "Last Hour":
            return now - timedelta(hours=1), now
        elif preset == "Last 6 Hours":
            return now - timedelta(hours=6), now
        elif preset == "Last 24 Hours":
            return now - timedelta(days=1), now
        elif preset == "Last 7 Days":
            return now - timedelta(days=7), now
        else:  # Custom
            custom_start = date_config.get("custom_start") or (now - timedelta(days=7)).date()
            custom_end = date_config.get("custom_end") or now.date()
            return (
                datetime.combine(custom_start, datetime.min.time()),
                datetime.combine(custom_end, datetime.max.time()),
            )

    def render_apply_buttons(self) -> bool:
        """
        Render Apply and Reset buttons.

        Returns:
            bool: True if settings were just applied
        """
        # Check if any pending settings differ from applied
        filters_changed = st.session_state.pending_filters != st.session_state.applied_filters
        date_changed = st.session_state.pending_date_range != st.session_state.applied_date_range
        limits_changed = (
            st.session_state.get("pending_risk_limits", {})
            != st.session_state.get("applied_risk_limits", {})
        )

        any_changed = filters_changed or date_changed or limits_changed

        st.sidebar.divider()

        # Apply and Reset buttons
        col1, col2 = st.sidebar.columns(2)

        applied = False
        with col1:
            if st.button(
                "Apply All",
                type="primary" if any_changed else "secondary",
                use_container_width=True,
            ):
                st.session_state.applied_filters = st.session_state.pending_filters.copy()
                st.session_state.applied_date_range = st.session_state.pending_date_range.copy()
                if "pending_risk_limits" in st.session_state:
                    st.session_state.applied_risk_limits = st.session_state.pending_risk_limits.copy()
                applied = True
                st.rerun()

        with col2:
            if st.button("Reset All", use_container_width=True):
                st.session_state.pending_filters = self.DEFAULT_FILTERS.copy()
                st.session_state.applied_filters = self.DEFAULT_FILTERS.copy()
                st.session_state.pending_date_range = self.DEFAULT_DATE_RANGE.copy()
                st.session_state.applied_date_range = self.DEFAULT_DATE_RANGE.copy()
                if "pending_risk_limits" in st.session_state:
                    from .alerts import RiskAlerts
                    st.session_state.pending_risk_limits = RiskAlerts.DEFAULT_LIMITS.copy()
                    st.session_state.applied_risk_limits = RiskAlerts.DEFAULT_LIMITS.copy()
                st.rerun()

        # Show indicator if settings are pending
        if any_changed:
            st.sidebar.caption("*Settings changed - click Apply All to update*")

        return applied

    def apply_filters(self, df: pd.DataFrame, filters: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply filters to DataFrame.

        Args:
            df: Trades DataFrame
            filters: Filter criteria

        Returns:
            Filtered DataFrame
        """
        if df.empty:
            return df

        result = df.copy()

        # Filter by portfolio (most important filter)
        portfolio = filters.get("portfolio", "ALL")
        if portfolio != "ALL":
            # Use Portfolio ID column for filtering (contains the actual ID like "CREDIT_IG")
            if "Portfolio ID" in result.columns:
                result = result[result["Portfolio ID"] == portfolio]
            elif "Portfolio" in result.columns:
                # Fallback to Portfolio name column
                result = result[result["Portfolio"] == portfolio]

        # Filter by currency (if column exists)
        if "Currency" in result.columns and filters.get("currencies"):
            result = result[result["Currency"].isin(filters["currencies"])]

        # Filter by instrument type (if column exists)
        if "Type" in result.columns and filters.get("instrument_types"):
            result = result[result["Type"].isin(filters["instrument_types"])]

        # Filter by maturity (if column exists)
        if "Years to Maturity" in result.columns:
            result = result[
                (result["Years to Maturity"] >= filters.get("maturity_min", 0))
                & (result["Years to Maturity"] <= filters.get("maturity_max", 30))
            ]

        # Filter by DV01 threshold
        if filters.get("dv01_min", 0) > 0 and "DV01" in result.columns:
            result = result[abs(result["DV01"]) >= filters["dv01_min"]]

        return result
