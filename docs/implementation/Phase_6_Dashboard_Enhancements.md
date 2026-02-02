# Phase 6: Dashboard Enhancement Features
## Advanced UI & Analytics Implementation

**Version:** 1.0  
**Date:** January 29, 2026  
**Status:** Ready for Implementation  
**Estimated Time:** 2-3 days

---

## 📋 Overview

This document provides detailed implementation instructions for 8 advanced dashboard features that will transform the risk monitor from a basic display to a professional analytics platform.

### Features to Implement

1. ✅ **Dropdown Filters** - Filter by currency, instrument type, maturity
2. ✅ **Date Range Selector** - Historical data viewing
3. ✅ **Risk Limit Alerts** - Visual warnings when limits breached
4. ✅ **Export to Excel** - Download portfolio data
5. ✅ **Dark/Light Theme Toggle** - User preference themes
6. ✅ **Historical Risk Chart** - Time-series DV01 visualization
7. ✅ **Concentration Risk** - Top risk contributors
8. ✅ **Risk Heatmap** - Instrument vs. tenor sensitivity matrix

---

## 🎯 Enhancement Goals

**User Experience:**
- Make dashboard more interactive
- Enable data exploration
- Provide actionable insights

**Analytics Depth:**
- Historical trend analysis
- Risk concentration identification
- Multi-dimensional views

**Professional Polish:**
- Export capabilities
- Customizable appearance
- Alert mechanisms

---

## 🏗️ Architecture Changes

### New Files to Create

```
dashboard/
├── app/
│   ├── main.py              (UPDATE - add features)
│   ├── data.py              (UPDATE - add historical methods)
│   ├── config.py            (UPDATE - add new settings)
│   ├── components/          (NEW)
│   │   ├── __init__.py
│   │   ├── filters.py       (NEW - filter components)
│   │   ├── charts.py        (NEW - advanced charts)
│   │   ├── alerts.py        (NEW - alert logic)
│   │   └── themes.py        (NEW - theme styles)
│   └── utils/               (NEW)
│       ├── __init__.py
│       └── export.py        (NEW - Excel export)
└── requirements.txt         (UPDATE - add new packages)
```

### New Redis Data Structure

```
# Historical data storage
ZADD portfolio:dv01_history SCORE timestamp "dv01_value"
ZADD portfolio:npv_history SCORE timestamp "npv_value"

# User preferences
HSET user:preferences
  "theme" "dark"
  "dv01_limit" "2000000"
  "refresh_interval" "2"
```

---

## 📦 Updated Dependencies

Update `dashboard/requirements.txt`:

```txt
streamlit==1.29.0
redis==5.0.1
pandas==2.1.4
plotly==5.18.0          # NEW - for advanced charts
openpyxl==3.1.2         # NEW - for Excel export
xlsxwriter==3.1.9       # NEW - for Excel formatting
python-dateutil==2.8.2  # NEW - for date handling
```

---

## 🔧 Feature 1: Dropdown Filters

### Goal
Allow users to filter portfolio view by currency, instrument type, and maturity range.

### Implementation

**File:** `dashboard/app/components/filters.py`

```python
"""Dashboard filter components."""

import streamlit as st
from typing import Tuple, List, Optional


class PortfolioFilters:
    """Manages dashboard filters."""
    
    def __init__(self):
        """Initialize filter state."""
        if 'filters' not in st.session_state:
            st.session_state.filters = {
                'currencies': [],
                'instrument_types': [],
                'maturity_min': 0,
                'maturity_max': 30,
            }
    
    def render_sidebar(self) -> dict:
        """
        Render filter controls in sidebar.
        
        Returns:
            dict: Current filter selections
        """
        st.sidebar.header("🔍 Filters")
        
        # Currency filter
        currencies = st.sidebar.multiselect(
            "Currency",
            options=["USD", "EUR", "GBP", "JPY"],
            default=st.session_state.filters['currencies'] or ["USD"],
            help="Select one or more currencies to display"
        )
        
        # Instrument type filter
        instrument_types = st.sidebar.multiselect(
            "Instrument Type",
            options=["BOND", "SWAP"],
            default=st.session_state.filters['instrument_types'] or ["BOND", "SWAP"],
            help="Filter by instrument type"
        )
        
        # Maturity range slider
        st.sidebar.subheader("Years to Maturity")
        maturity_range = st.sidebar.slider(
            "Range",
            min_value=0,
            max_value=30,
            value=(
                st.session_state.filters['maturity_min'],
                st.session_state.filters['maturity_max']
            ),
            help="Filter by years remaining to maturity"
        )
        
        # DV01 threshold filter
        dv01_min = st.sidebar.number_input(
            "Min DV01 to Display ($)",
            min_value=0,
            value=0,
            step=1000,
            help="Only show trades with DV01 above this threshold"
        )
        
        # Update session state
        filters = {
            'currencies': currencies,
            'instrument_types': instrument_types,
            'maturity_min': maturity_range[0],
            'maturity_max': maturity_range[1],
            'dv01_min': dv01_min,
        }
        
        st.session_state.filters = filters
        
        # Reset button
        if st.sidebar.button("Reset Filters"):
            st.session_state.filters = {
                'currencies': ["USD"],
                'instrument_types': ["BOND", "SWAP"],
                'maturity_min': 0,
                'maturity_max': 30,
                'dv01_min': 0,
            }
            st.rerun()
        
        return filters
    
    def apply_filters(self, df, filters: dict):
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
        
        # Filter by currency
        if filters['currencies']:
            df = df[df['Currency'].isin(filters['currencies'])]
        
        # Filter by instrument type
        if filters['instrument_types']:
            df = df[df['Type'].isin(filters['instrument_types'])]
        
        # Filter by maturity
        if 'Years to Maturity' in df.columns:
            df = df[
                (df['Years to Maturity'] >= filters['maturity_min']) &
                (df['Years to Maturity'] <= filters['maturity_max'])
            ]
        
        # Filter by DV01 threshold
        if filters.get('dv01_min', 0) > 0:
            df = df[abs(df['DV01']) >= filters['dv01_min']]
        
        return df
```

### Integration into main.py

```python
# Add at top of main.py
from components.filters import PortfolioFilters

# In render_dashboard():
filters_manager = PortfolioFilters()
active_filters = filters_manager.render_sidebar()

# Apply filters to trades
trades_df = fetcher.get_trades_dataframe()
if not trades_df.empty:
    trades_df = filters_manager.apply_filters(trades_df, active_filters)
```

---

## 📅 Feature 2: Date Range Selector

### Goal
Allow users to view historical risk metrics over custom date ranges.

### Implementation

**File:** `dashboard/app/data.py` (UPDATE)

Add historical data methods:

```python
from datetime import datetime, timedelta
from typing import List, Tuple

class RiskDataFetcher:
    """Fetches risk data from Redis."""
    
    # ... existing methods ...
    
    def get_historical_dv01(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """
        Get historical DV01 data for date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            DataFrame with columns: timestamp, dv01
        """
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        # Get data from sorted set
        results = self.client.zrangebyscore(
            "portfolio:dv01_history",
            start_ts,
            end_ts,
            withscores=True
        )
        
        if not results:
            return pd.DataFrame(columns=['timestamp', 'dv01'])
        
        data = []
        for value, score in results:
            data.append({
                'timestamp': datetime.fromtimestamp(score / 1000),
                'dv01': float(value)
            })
        
        return pd.DataFrame(data)
    
    def get_historical_npv(self, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Get historical NPV data for date range."""
        start_ts = int(start_date.timestamp() * 1000)
        end_ts = int(end_date.timestamp() * 1000)
        
        results = self.client.zrangebyscore(
            "portfolio:npv_history",
            start_ts,
            end_ts,
            withscores=True
        )
        
        if not results:
            return pd.DataFrame(columns=['timestamp', 'npv'])
        
        data = []
        for value, score in results:
            data.append({
                'timestamp': datetime.fromtimestamp(score / 1000),
                'npv': float(value)
            })
        
        return pd.DataFrame(data)
```

**File:** `dashboard/app/components/filters.py` (UPDATE)

Add date range selector:

```python
def render_date_selector(self) -> Tuple[datetime, datetime]:
    """
    Render date range selector.
    
    Returns:
        Tuple of (start_date, end_date)
    """
    st.sidebar.subheader("📅 Date Range")
    
    # Preset options
    preset = st.sidebar.selectbox(
        "Quick Select",
        ["Last Hour", "Last 6 Hours", "Last 24 Hours", "Last 7 Days", "Custom"]
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
            start_date = st.date_input(
                "From",
                value=now - timedelta(days=7),
                max_value=now
            )
        with col2:
            end_date = st.date_input(
                "To",
                value=now,
                max_value=now
            )
        
        # Convert date to datetime
        start_date = datetime.combine(start_date, datetime.min.time())
        end_date = datetime.combine(end_date, datetime.max.time())
    
    return start_date, end_date
```

---

## 🚨 Feature 3: Risk Limit Alerts

### Goal
Display visual alerts when portfolio risk exceeds configured limits.

### Implementation

**File:** `dashboard/app/components/alerts.py`

```python
"""Risk alert components."""

import streamlit as st
from typing import Dict, Optional


class RiskAlerts:
    """Manages risk limit alerts."""
    
    def __init__(self):
        """Initialize with default limits."""
        if 'risk_limits' not in st.session_state:
            st.session_state.risk_limits = {
                'dv01_limit': 2_000_000,
                'npv_limit': 1_000_000_000,
                'concentration_limit': 0.20,  # 20% max in single trade
            }
    
    def configure_limits(self):
        """Render limit configuration in sidebar."""
        st.sidebar.subheader("⚠️ Risk Limits")
        
        dv01_limit = st.sidebar.number_input(
            "DV01 Limit ($)",
            min_value=0,
            value=st.session_state.risk_limits['dv01_limit'],
            step=100_000,
            help="Alert when portfolio DV01 exceeds this value"
        )
        
        npv_limit = st.sidebar.number_input(
            "NPV Limit ($)",
            min_value=0,
            value=st.session_state.risk_limits['npv_limit'],
            step=100_000_000,
            help="Alert when portfolio NPV exceeds this value"
        )
        
        concentration_limit = st.sidebar.slider(
            "Concentration Limit (%)",
            min_value=0,
            max_value=100,
            value=int(st.session_state.risk_limits['concentration_limit'] * 100),
            help="Alert when single trade exceeds this % of total DV01"
        ) / 100
        
        st.session_state.risk_limits = {
            'dv01_limit': dv01_limit,
            'npv_limit': npv_limit,
            'concentration_limit': concentration_limit,
        }
    
    def check_limits(self, total_dv01: float, total_npv: float, 
                     max_trade_dv01: float) -> Dict[str, bool]:
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
            'dv01': abs(total_dv01) > limits['dv01_limit'],
            'npv': abs(total_npv) > limits['npv_limit'],
            'concentration': (abs(max_trade_dv01) / abs(total_dv01)) > limits['concentration_limit'] if total_dv01 != 0 else False,
        }
        
        return breaches
    
    def render_alerts(self, total_dv01: float, total_npv: float, 
                     max_trade_dv01: float, max_trade_id: str = ""):
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
        if breaches['dv01']:
            st.error(
                f"🚨 **DV01 LIMIT BREACH** | "
                f"Portfolio DV01: ${abs(total_dv01):,.0f} | "
                f"Limit: ${limits['dv01_limit']:,.0f} | "
                f"Excess: ${abs(total_dv01) - limits['dv01_limit']:,.0f}"
            )
            alert_shown = True
        
        # NPV limit breach
        if breaches['npv']:
            st.error(
                f"🚨 **NPV LIMIT BREACH** | "
                f"Portfolio NPV: ${abs(total_npv):,.0f} | "
                f"Limit: ${limits['npv_limit']:,.0f} | "
                f"Excess: ${abs(total_npv) - limits['npv_limit']:,.0f}"
            )
            alert_shown = True
        
        # Concentration limit breach
        if breaches['concentration'] and total_dv01 != 0:
            concentration_pct = (abs(max_trade_dv01) / abs(total_dv01)) * 100
            st.warning(
                f"⚠️ **CONCENTRATION RISK** | "
                f"Single trade ({max_trade_id[:8]}...) represents {concentration_pct:.1f}% of portfolio DV01 | "
                f"Limit: {limits['concentration_limit']*100:.0f}%"
            )
            alert_shown = True
        
        # All clear message
        if not alert_shown:
            st.success("✅ All risk limits within acceptable ranges")
```

### Integration into main.py

```python
from components.alerts import RiskAlerts

# In render_dashboard():
alert_manager = RiskAlerts()
alert_manager.configure_limits()

# After getting aggregates
if aggregates:
    # Find max trade DV01
    trades_df = fetcher.get_trades_dataframe()
    if not trades_df.empty:
        max_idx = trades_df['DV01'].abs().idxmax()
        max_trade_dv01 = trades_df.loc[max_idx, 'DV01']
        max_trade_id = trades_df.loc[max_idx, 'Instrument ID']
    else:
        max_trade_dv01 = 0
        max_trade_id = ""
    
    # Render alerts
    alert_manager.render_alerts(
        aggregates.total_dv01,
        aggregates.total_npv,
        max_trade_dv01,
        max_trade_id
    )
```

---

## 📊 Feature 4: Export to Excel

### Goal
Allow users to download portfolio data as formatted Excel file.

### Implementation

**File:** `dashboard/app/utils/export.py`

```python
"""Excel export utilities."""

import pandas as pd
from io import BytesIO
from datetime import datetime
import xlsxwriter


class ExcelExporter:
    """Handles Excel export with formatting."""
    
    @staticmethod
    def create_portfolio_export(trades_df: pd.DataFrame, aggregates: dict) -> BytesIO:
        """
        Create formatted Excel file with portfolio data.
        
        Args:
            trades_df: Trade-level data
            aggregates: Portfolio aggregates
            
        Returns:
            BytesIO: Excel file buffer
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            workbook = writer.book
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4CAF50',
                'font_color': 'white',
                'border': 1
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'border': 1
            })
            
            number_format = workbook.add_format({
                'num_format': '#,##0',
                'border': 1
            })
            
            # Sheet 1: Portfolio Summary
            summary_df = pd.DataFrame({
                'Metric': [
                    'Report Date',
                    'Total Instruments',
                    'Total NPV',
                    'Total DV01',
                    'Total KRD 2Y',
                    'Total KRD 5Y',
                    'Total KRD 10Y',
                    'Total KRD 30Y',
                ],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    aggregates.get('instrument_count', 0),
                    aggregates.get('total_npv', 0),
                    aggregates.get('total_dv01', 0),
                    aggregates.get('krd_2y', 0),
                    aggregates.get('krd_5y', 0),
                    aggregates.get('krd_10y', 0),
                    aggregates.get('krd_30y', 0),
                ]
            })
            
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
            summary_sheet = writer.sheets['Summary']
            summary_sheet.set_column('A:A', 20)
            summary_sheet.set_column('B:B', 20)
            
            # Sheet 2: Trade Details
            if not trades_df.empty:
                trades_df.to_excel(writer, sheet_name='Trade Details', index=False)
                trades_sheet = writer.sheets['Trade Details']
                
                # Format columns
                for idx, col in enumerate(trades_df.columns):
                    trades_sheet.write(0, idx, col, header_format)
                    
                    if col in ['NPV', 'DV01', 'KRD 2Y', 'KRD 5Y', 'KRD 10Y', 'KRD 30Y']:
                        trades_sheet.set_column(idx, idx, 15, currency_format)
                    else:
                        trades_sheet.set_column(idx, idx, 15)
            
            # Sheet 3: Risk Breakdown
            if not trades_df.empty:
                # By instrument type
                type_breakdown = trades_df.groupby('Type').agg({
                    'NPV': 'sum',
                    'DV01': 'sum'
                }).reset_index()
                
                type_breakdown.to_excel(writer, sheet_name='Risk Breakdown', index=False, startrow=0)
                
                # By currency (if available)
                if 'Currency' in trades_df.columns:
                    currency_breakdown = trades_df.groupby('Currency').agg({
                        'NPV': 'sum',
                        'DV01': 'sum'
                    }).reset_index()
                    
                    currency_breakdown.to_excel(
                        writer, 
                        sheet_name='Risk Breakdown', 
                        index=False, 
                        startrow=len(type_breakdown) + 3
                    )
        
        output.seek(0)
        return output
    
    @staticmethod
    def create_historical_export(historical_df: pd.DataFrame) -> BytesIO:
        """
        Create Excel file with historical data.
        
        Args:
            historical_df: Historical risk data
            
        Returns:
            BytesIO: Excel file buffer
        """
        output = BytesIO()
        
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            historical_df.to_excel(writer, sheet_name='Historical Data', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Historical Data']
            
            # Add chart
            chart = workbook.add_chart({'type': 'line'})
            chart.add_series({
                'name': 'DV01',
                'categories': ['Historical Data', 1, 0, len(historical_df), 0],
                'values': ['Historical Data', 1, 1, len(historical_df), 1],
            })
            chart.set_title({'name': 'Portfolio DV01 Over Time'})
            chart.set_x_axis({'name': 'Date'})
            chart.set_y_axis({'name': 'DV01 ($)'})
            
            worksheet.insert_chart('D2', chart)
        
        output.seek(0)
        return output
```

### Integration into main.py

```python
from utils.export import ExcelExporter

# Add export section
st.sidebar.subheader("📥 Export Data")

if st.sidebar.button("Export to Excel"):
    with st.spinner("Generating Excel file..."):
        excel_file = ExcelExporter.create_portfolio_export(
            trades_df,
            {
                'instrument_count': aggregates.instrument_count,
                'total_npv': aggregates.total_npv,
                'total_dv01': aggregates.total_dv01,
                'krd_2y': aggregates.krd_2y,
                'krd_5y': aggregates.krd_5y,
                'krd_10y': aggregates.krd_10y,
                'krd_30y': aggregates.krd_30y,
            }
        )
        
        st.sidebar.download_button(
            label="Download Excel",
            data=excel_file,
            file_name=f"portfolio_risk_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
```

---

## 🎨 Feature 5: Dark/Light Theme Toggle

### Goal
Allow users to switch between dark and light themes.

### Implementation

**File:** `dashboard/app/components/themes.py`

```python
"""Theme management for dashboard."""

import streamlit as st


class ThemeManager:
    """Manages dashboard themes."""
    
    DARK_THEME = """
    <style>
        /* Dark theme styles */
        .stApp {
            background-color: #0e1117;
        }
        
        .metric-card {
            background-color: #1e1e1e;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #333;
        }
        
        h1, h2, h3 {
            color: #fafafa;
        }
        
        .stMetric {
            background-color: #262730;
            padding: 10px;
            border-radius: 5px;
        }
        
        [data-testid="stSidebar"] {
            background-color: #262730;
        }
    </style>
    """
    
    LIGHT_THEME = """
    <style>
        /* Light theme styles */
        .stApp {
            background-color: #ffffff;
        }
        
        .metric-card {
            background-color: #f0f2f6;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e0e0e0;
        }
        
        h1, h2, h3 {
            color: #262730;
        }
        
        .stMetric {
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 5px;
            border: 1px solid #dee2e6;
        }
        
        [data-testid="stSidebar"] {
            background-color: #f8f9fa;
        }
    </style>
    """
    
    def __init__(self):
        """Initialize theme manager."""
        if 'theme' not in st.session_state:
            st.session_state.theme = 'dark'
    
    def render_toggle(self):
        """Render theme toggle in sidebar."""
        st.sidebar.subheader("🎨 Theme")
        
        theme = st.sidebar.radio(
            "Select Theme",
            options=["Dark", "Light"],
            index=0 if st.session_state.theme == 'dark' else 1,
            horizontal=True
        )
        
        st.session_state.theme = theme.lower()
    
    def apply_theme(self):
        """Apply selected theme."""
        if st.session_state.theme == 'dark':
            st.markdown(self.DARK_THEME, unsafe_allow_html=True)
        else:
            st.markdown(self.LIGHT_THEME, unsafe_allow_html=True)
```

### Integration into main.py

```python
from components.themes import ThemeManager

# At start of main():
theme_manager = ThemeManager()
theme_manager.render_toggle()
theme_manager.apply_theme()
```

---

## 📈 Feature 6: Historical Risk Chart

### Goal
Display time-series chart showing DV01 evolution over time.

### Implementation

**File:** `dashboard/app/components/charts.py`

```python
"""Advanced chart components."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
from datetime import datetime


class AdvancedCharts:
    """Creates advanced plotly charts."""
    
    @staticmethod
    def create_historical_dv01_chart(historical_df: pd.DataFrame) -> go.Figure:
        """
        Create line chart showing DV01 over time.
        
        Args:
            historical_df: DataFrame with columns [timestamp, dv01]
            
        Returns:
            Plotly figure
        """
        if historical_df.empty:
            # Empty chart placeholder
            fig = go.Figure()
            fig.add_annotation(
                text="No historical data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False
            )
            return fig
        
        fig = go.Figure()
        
        # Add DV01 line
        fig.add_trace(go.Scatter(
            x=historical_df['timestamp'],
            y=historical_df['dv01'],
            mode='lines',
            name='DV01',
            line=dict(color='#4CAF50', width=2),
            fill='tozeroy',
            fillcolor='rgba(76, 175, 80, 0.1)'
        ))
        
        # Add moving average (if enough data)
        if len(historical_df) >= 10:
            historical_df['dv01_ma'] = historical_df['dv01'].rolling(window=10).mean()
            fig.add_trace(go.Scatter(
                x=historical_df['timestamp'],
                y=historical_df['dv01_ma'],
                mode='lines',
                name='Moving Avg (10)',
                line=dict(color='#FF9800', width=2, dash='dash')
            ))
        
        fig.update_layout(
            title="Portfolio DV01 Over Time",
            xaxis_title="Time",
            yaxis_title="DV01 ($)",
            hovermode='x unified',
            template='plotly_dark',
            height=400,
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )
        
        return fig
    
    @staticmethod
    def create_dual_axis_chart(historical_df: pd.DataFrame) -> go.Figure:
        """
        Create chart with DV01 and NPV on dual axes.
        
        Args:
            historical_df: DataFrame with columns [timestamp, dv01, npv]
            
        Returns:
            Plotly figure
        """
        fig = go.Figure()
        
        # DV01 on primary axis
        fig.add_trace(go.Scatter(
            x=historical_df['timestamp'],
            y=historical_df['dv01'],
            name='DV01',
            yaxis='y',
            line=dict(color='#4CAF50', width=2)
        ))
        
        # NPV on secondary axis
        fig.add_trace(go.Scatter(
            x=historical_df['timestamp'],
            y=historical_df['npv'],
            name='NPV',
            yaxis='y2',
            line=dict(color='#2196F3', width=2)
        ))
        
        fig.update_layout(
            title="Portfolio Metrics Over Time",
            xaxis=dict(title="Time"),
            yaxis=dict(
                title="DV01 ($)",
                titlefont=dict(color='#4CAF50'),
                tickfont=dict(color='#4CAF50')
            ),
            yaxis2=dict(
                title="NPV ($)",
                titlefont=dict(color='#2196F3'),
                tickfont=dict(color='#2196F3'),
                overlaying='y',
                side='right'
            ),
            hovermode='x unified',
            template='plotly_dark',
            height=400
        )
        
        return fig
```

### Integration into main.py

```python
from components.charts import AdvancedCharts

# Add historical section
st.subheader("📈 Historical Risk Analysis")

start_date, end_date = filters_manager.render_date_selector()

historical_dv01 = fetcher.get_historical_dv01(start_date, end_date)

if not historical_dv01.empty:
    chart = AdvancedCharts.create_historical_dv01_chart(historical_dv01)
    st.plotly_chart(chart, use_container_width=True)
else:
    st.info("No historical data available for selected date range")
```

---

## 🎯 Feature 7: Concentration Risk

### Goal
Identify and visualize top risk contributors (largest DV01 positions).

### Implementation

**File:** `dashboard/app/components/charts.py` (ADD)

```python
@staticmethod
def create_concentration_chart(trades_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create bar chart showing top N risk contributors.
    
    Args:
        trades_df: Trade-level data
        top_n: Number of top trades to show
        
    Returns:
        Plotly figure
    """
    if trades_df.empty:
        fig = go.Figure()
        fig.add_annotation(
            text="No trade data available",
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            showarrow=False
        )
        return fig
    
    # Get top contributors by absolute DV01
    trades_df['DV01_Abs'] = trades_df['DV01'].abs()
    top_trades = trades_df.nlargest(top_n, 'DV01_Abs')
    
    # Calculate percentage of total
    total_dv01 = trades_df['DV01_Abs'].sum()
    top_trades['Percentage'] = (top_trades['DV01_Abs'] / total_dv01 * 100)
    
    # Create bar chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=top_trades['Instrument ID'],
        y=top_trades['DV01'],
        text=top_trades['Percentage'].apply(lambda x: f"{x:.1f}%"),
        textposition='outside',
        marker=dict(
            color=top_trades['DV01'],
            colorscale='RdYlGn',
            showscale=True,
            colorbar=dict(title="DV01 ($)")
        ),
        hovertemplate='<b>%{x}</b><br>DV01: $%{y:,.0f}<br>%{text} of total<extra></extra>'
    ))
    
    fig.update_layout(
        title=f"Top {top_n} Risk Contributors",
        xaxis_title="Instrument ID",
        yaxis_title="DV01 ($)",
        template='plotly_dark',
        height=400,
        showlegend=False
    )
    
    return fig

@staticmethod
def create_concentration_pie(trades_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create pie chart showing concentration risk.
    
    Args:
        trades_df: Trade-level data
        top_n: Number of top trades to show
        
    Returns:
        Plotly figure
    """
    if trades_df.empty:
        return go.Figure()
    
    trades_df['DV01_Abs'] = trades_df['DV01'].abs()
    top_trades = trades_df.nlargest(top_n, 'DV01_Abs')
    
    # Top N + "Others"
    top_sum = top_trades['DV01_Abs'].sum()
    others_sum = trades_df['DV01_Abs'].sum() - top_sum
    
    labels = list(top_trades['Instrument ID'][:5]) + ['Others']
    values = list(top_trades['DV01_Abs'][:5]) + [others_sum + top_trades['DV01_Abs'][5:].sum()]
    
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hole=0.3,
        marker=dict(colors=px.colors.qualitative.Set3)
    )])
    
    fig.update_layout(
        title="Risk Concentration Distribution",
        template='plotly_dark',
        height=400
    )
    
    return fig
```

### Integration into main.py

```python
# Add concentration section
st.subheader("🎯 Concentration Risk Analysis")

col1, col2 = st.columns(2)

with col1:
    concentration_chart = AdvancedCharts.create_concentration_chart(trades_df, top_n=10)
    st.plotly_chart(concentration_chart, use_container_width=True)

with col2:
    concentration_pie = AdvancedCharts.create_concentration_pie(trades_df, top_n=10)
    st.plotly_chart(concentration_pie, use_container_width=True)
```

---

## 🔥 Feature 8: Risk Heatmap

### Goal
Display 2D heatmap showing instrument vs. tenor sensitivity matrix.

### Implementation

**File:** `dashboard/app/components/charts.py` (ADD)

```python
@staticmethod
def create_krd_heatmap(trades_df: pd.DataFrame) -> go.Figure:
    """
    Create heatmap showing KRD by instrument and tenor.
    
    Args:
        trades_df: Trade-level data with KRD columns
        
    Returns:
        Plotly figure
    """
    if trades_df.empty:
        return go.Figure()
    
    # Prepare matrix data
    tenors = ['2Y', '5Y', '10Y', '30Y']
    krd_columns = ['KRD 2Y', 'KRD 5Y', 'KRD 10Y', 'KRD 30Y']
    
    # Get top 20 trades by total KRD
    trades_df['Total_KRD'] = trades_df[krd_columns].abs().sum(axis=1)
    top_trades = trades_df.nlargest(20, 'Total_KRD')
    
    # Build matrix
    z_data = []
    y_labels = []
    
    for idx, row in top_trades.iterrows():
        z_data.append([row[col] for col in krd_columns])
        y_labels.append(row['Instrument ID'][:12] + '...')
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=tenors,
        y=y_labels,
        colorscale='RdYlGn',
        zmid=0,
        colorbar=dict(title="KRD ($)"),
        hovertemplate='Instrument: %{y}<br>Tenor: %{x}<br>KRD: $%{z:,.0f}<extra></extra>'
    ))
    
    fig.update_layout(
        title="Key Rate Duration Heatmap (Top 20 Trades)",
        xaxis_title="Tenor",
        yaxis_title="Instrument",
        template='plotly_dark',
        height=600,
        yaxis=dict(tickmode='linear')
    )
    
    return fig

@staticmethod
def create_correlation_heatmap(historical_df: pd.DataFrame) -> go.Figure:
    """
    Create correlation heatmap between different risk metrics.
    
    Args:
        historical_df: Historical data with multiple metrics
        
    Returns:
        Plotly figure
    """
    if historical_df.empty or len(historical_df) < 10:
        return go.Figure()
    
    # Calculate correlation matrix
    metrics = ['dv01', 'npv', 'krd_2y', 'krd_5y', 'krd_10y', 'krd_30y']
    available_metrics = [m for m in metrics if m in historical_df.columns]
    
    if len(available_metrics) < 2:
        return go.Figure()
    
    corr_matrix = historical_df[available_metrics].corr()
    
    fig = go.Figure(data=go.Heatmap(
        z=corr_matrix.values,
        x=[m.upper() for m in corr_matrix.columns],
        y=[m.upper() for m in corr_matrix.index],
        colorscale='RdBu',
        zmid=0,
        zmin=-1,
        zmax=1,
        text=corr_matrix.values,
        texttemplate='%{text:.2f}',
        textfont={"size": 10},
        colorbar=dict(title="Correlation")
    ))
    
    fig.update_layout(
        title="Risk Metrics Correlation Matrix",
        template='plotly_dark',
        height=400
    )
    
    return fig
```

### Integration into main.py

```python
# Add heatmap section
st.subheader("🔥 Risk Heatmap Analysis")

tab1, tab2 = st.tabs(["KRD Heatmap", "Correlation Matrix"])

with tab1:
    krd_heatmap = AdvancedCharts.create_krd_heatmap(trades_df)
    st.plotly_chart(krd_heatmap, use_container_width=True)

with tab2:
    if not historical_dv01.empty:
        corr_heatmap = AdvancedCharts.create_correlation_heatmap(historical_dv01)
        st.plotly_chart(corr_heatmap, use_container_width=True)
    else:
        st.info("Correlation matrix requires historical data")
```

---

## 🧪 Testing Checklist

### Feature Testing

- [ ] **Dropdown Filters**
  - [ ] Currency filter works
  - [ ] Instrument type filter works
  - [ ] Maturity range slider works
  - [ ] Reset button clears filters
  - [ ] Filtered data matches criteria

- [ ] **Date Range Selector**
  - [ ] Quick select presets work
  - [ ] Custom date range works
  - [ ] Historical data loads correctly
  - [ ] Invalid date ranges handled

- [ ] **Risk Limit Alerts**
  - [ ] DV01 limit alert triggers
  - [ ] NPV limit alert triggers
  - [ ] Concentration alert triggers
  - [ ] Alert styling correct
  - [ ] Limits persist in session

- [ ] **Export to Excel**
  - [ ] Excel file downloads
  - [ ] All sheets present
  - [ ] Formatting applied
  - [ ] Data accurate
  - [ ] File opens in Excel

- [ ] **Dark/Light Theme**
  - [ ] Theme toggle works
  - [ ] Dark theme styles applied
  - [ ] Light theme styles applied
  - [ ] Theme persists during session

- [ ] **Historical Chart**
  - [ ] Chart renders correctly
  - [ ] Data points accurate
  - [ ] Moving average calculates
  - [ ] Hover tooltips work
  - [ ] Empty state handled

- [ ] **Concentration Risk**
  - [ ] Bar chart shows top 10
  - [ ] Percentages calculated correctly
  - [ ] Pie chart renders
  - [ ] Colors distinguish trades

- [ ] **Risk Heatmap**
  - [ ] Heatmap renders correctly
  - [ ] Color scale appropriate
  - [ ] Top 20 trades shown
  - [ ] Hover tooltips work
  - [ ] Correlation matrix calculates

---

## 🚀 Deployment Instructions

### Step 1: Update Dependencies

```bash
cd /Users/liuyuxuan/risk_monitor/dashboard
pip install -r requirements.txt
```

### Step 2: Create New Files

Create all files as specified in each feature section:
- `components/filters.py`
- `components/charts.py`
- `components/alerts.py`
- `components/themes.py`
- `utils/export.py`

### Step 3: Update main.py

Integrate all features into `main.py` as shown in each section.

### Step 4: Rebuild Docker

```bash
cd /Users/liuyuxuan/risk_monitor

# Rebuild dashboard
docker-compose build dashboard

# Restart
docker-compose up -d dashboard

# Check logs
docker-compose logs -f dashboard
```

### Step 5: Test Each Feature

Open http://localhost:8501 and test each feature systematically.

---

## 📊 Expected Outcome

After implementation, your dashboard will have:

✅ **Professional UI**
- Sidebar filters for data exploration
- Theme customization
- Clean, modern design

✅ **Advanced Analytics**
- Historical trend analysis
- Concentration risk identification
- Multi-dimensional heatmaps

✅ **Actionable Insights**
- Real-time limit alerts
- Risk distribution visualization
- Top contributors identification

✅ **Export Capabilities**
- Formatted Excel reports
- Historical data export
- Professional presentation

---

## 🎯 Success Metrics

| Metric | Target | Validation |
|--------|--------|------------|
| Feature Implementation | 8/8 complete | All features working |
| UI Response Time | < 1s | Page load < 1 second |
| Export File Size | < 5MB | Excel opens quickly |
| Chart Render Time | < 2s | Plotly charts load fast |
| Filter Performance | < 500ms | Data filters instantly |

---

## 📚 Additional Resources

**Plotly Documentation:** https://plotly.com/python/  
**Streamlit Components:** https://docs.streamlit.io/library/components  
**Excel Export:** https://xlsxwriter.readthedocs.io/  
**Pandas Filtering:** https://pandas.pydata.org/docs/user_guide/indexing.html

---

**Document Status:** ✅ Ready for Implementation  
**Estimated Completion:** 2-3 days  
**Priority:** High (significantly enhances demo value)  
**Next Steps:** Begin with Feature 1 (Dropdown Filters) and proceed sequentially
