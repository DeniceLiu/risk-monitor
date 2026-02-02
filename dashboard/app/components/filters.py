"""Dashboard filter components."""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from typing import Tuple, Dict, Any


class PortfolioFilters:
    """Manages dashboard filters."""

    DEFAULT_FILTERS = {
        "currencies": ["USD"],
        "instrument_types": ["BOND", "SWAP"],
        "maturity_min": 0,
        "maturity_max": 30,
        "dv01_min": 0,
    }

    def __init__(self):
        """Initialize filter state."""
        # Applied filters (used for actual filtering)
        if "applied_filters" not in st.session_state:
            st.session_state.applied_filters = self.DEFAULT_FILTERS.copy()

        # Pending filters (current UI selections, not yet applied)
        if "pending_filters" not in st.session_state:
            st.session_state.pending_filters = self.DEFAULT_FILTERS.copy()

    def render_sidebar(self) -> Dict[str, Any]:
        """
        Render filter controls in sidebar.

        Returns:
            dict: Currently applied filter selections
        """
        st.sidebar.header("Filters")

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
            "currencies": currencies if currencies else ["USD"],
            "instrument_types": instrument_types if instrument_types else ["BOND", "SWAP"],
            "maturity_min": maturity_range[0],
            "maturity_max": maturity_range[1],
            "dv01_min": dv01_min,
        }

        # Check if pending differs from applied
        filters_changed = st.session_state.pending_filters != st.session_state.applied_filters

        # Apply and Reset buttons
        col1, col2 = st.sidebar.columns(2)

        with col1:
            if st.button(
                "Apply Filters",
                type="primary" if filters_changed else "secondary",
                use_container_width=True,
            ):
                st.session_state.applied_filters = st.session_state.pending_filters.copy()
                st.rerun()

        with col2:
            if st.button("Reset", use_container_width=True):
                st.session_state.pending_filters = self.DEFAULT_FILTERS.copy()
                st.session_state.applied_filters = self.DEFAULT_FILTERS.copy()
                st.rerun()

        # Show indicator if filters are pending
        if filters_changed:
            st.sidebar.caption("*Filters changed - click Apply to update*")

        return st.session_state.applied_filters

    def render_date_selector(self) -> Tuple[datetime, datetime]:
        """
        Render date range selector.

        Returns:
            Tuple of (start_date, end_date)
        """
        st.sidebar.subheader("Date Range")

        # Preset options
        preset = st.sidebar.selectbox(
            "Quick Select",
            ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Custom"],
        )

        now = datetime.now()

        if preset == "Last Hour":
            start_date = now - timedelta(hours=1)
            end_date = now
        elif preset == "Last 6 Hours":
            start_date = now - timedelta(hours=6)
            end_date = now
        elif preset == "Last 24 Hours":
            start_date = now - timedelta(days=1)
            end_date = now
        elif preset == "Last 7 Days":
            start_date = now - timedelta(days=7)
            end_date = now
        else:  # Custom
            col1, col2 = st.sidebar.columns(2)
            with col1:
                start_date_input = st.date_input(
                    "From", value=now - timedelta(days=7), max_value=now.date()
                )
            with col2:
                end_date_input = st.date_input("To", value=now.date(), max_value=now.date())

            # Convert date to datetime
            start_date = datetime.combine(start_date_input, datetime.min.time())
            end_date = datetime.combine(end_date_input, datetime.max.time())

        return start_date, end_date

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
