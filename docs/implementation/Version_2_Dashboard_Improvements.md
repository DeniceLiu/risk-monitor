# Version 2: Dashboard Improvements Based on User Feedback

**Deployed URL:** https://risk-monitor.ngrok.app  
**Current Version:** V1 (Static appearance, graphs first)  
**Target Version:** V2 (Real-time streaming, table-first, manager-focused)  
**Implementation Date:** TBD  

---

## 📋 **User Feedback Summary**

From initial deployment review, users requested:

1. **❌ Looks too static** → ✅ Add real-time streaming indicators
2. **❌ Graphs before data** → ✅ Show portfolio table first (manager workflow)
3. **❌ ISINs unreadable** → ✅ Use bond issuer names on charts
4. **❌ DV01 scale broken** → ✅ Fix chart scaling issues
5. **❌ Running icon unprofessional** → ✅ Change to financial chart icon

---

## 🎯 **Version 2 Objectives**

### **Primary Goal**
Transform dashboard from "static report view" to "live trading desk monitor"

### **User Persona**
Portfolio Manager who needs to:
- Quickly check their portfolio holdings (table view)
- See real-time risk changes (streaming indicators)
- Identify bonds by company name (not codes)
- Monitor multiple portfolios (dropdown switching)
- Export data for reports

---

## 🔧 **Implementation Plan**

## **Change 1: Add Real-Time Streaming Indicators**

### **Problem**
- Dashboard looks static, like a PDF report
- Users can't tell if data is live or stale
- No visual indication of updates happening

### **Solution**

#### **1.1 Live Status Badge**
```python
# Location: main.py, header section

# Current V1:
st.success(f"Status: {status}")

# New V2:
if "Live" in status:
    st.success(f"🟢 **LIVE STREAMING** | Updated {status}")
else:
    st.warning(f"🟡 **STALE DATA** | Last update {status}")
```

**Visual Result:**
```
Before: Status: Live
After:  🟢 LIVE STREAMING | Updated 2s ago
```

#### **1.2 Real-Time Clock**
```python
# Add to header row
with col3:
    current_time = datetime.now().strftime("%H:%M:%S")
    st.metric(
        "System Time", 
        current_time, 
        delta="Auto-refresh: 2s",
        delta_color="off"
    )
```

#### **1.3 Mini Live DV01 Ticker (Sparkline)**

Add a small streaming chart at the top showing last 5 minutes of DV01:

```python
# New component in main.py after Portfolio Summary

st.markdown("### 📈 Live DV01 Monitor (Last 5 Minutes)")

# Fetch recent history
historical_dv01_mini = fetcher.get_historical_dv01(
    datetime.now() - timedelta(minutes=5),
    datetime.now()
)

if not historical_dv01_mini.empty and len(historical_dv01_mini) > 5:
    # Create mini sparkline chart
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=historical_dv01_mini['timestamp'],
        y=historical_dv01_mini['dv01'],
        mode='lines',
        line=dict(color='#00ff00', width=2),
        fill='tozeroy',
        fillcolor='rgba(0,255,0,0.1)',
        name='DV01'
    ))
    
    fig.update_layout(
        height=120,  # Small height - sparkline style
        margin=dict(l=0, r=0, t=0, b=0),
        xaxis=dict(showgrid=False, showticklabels=False),
        yaxis=dict(showgrid=True, gridcolor='rgba(255,255,255,0.1)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        hovermode='x unified'
    ))
    
    st.plotly_chart(fig, use_container_width=True, key="live_ticker")
else:
    st.info("⏳ Building live history... (collecting 5+ minutes of data)")
```

**Visual Result:**
- Small chart showing DV01 trend
- Updates every 2 seconds (new point added)
- Gives "stock ticker" feel

#### **1.4 Pulsing Indicator During Updates**

Add CSS animation for live indicator:

```python
# Add to themes.py or inject in main.py

st.markdown("""
<style>
    .live-pulse {
        display: inline-block;
        width: 10px;
        height: 10px;
        background-color: #00ff00;
        border-radius: 50%;
        animation: pulse 2s infinite;
    }
    
    @keyframes pulse {
        0% {
            box-shadow: 0 0 0 0 rgba(0, 255, 0, 0.7);
        }
        70% {
            box-shadow: 0 0 0 10px rgba(0, 255, 0, 0);
        }
        100% {
            box-shadow: 0 0 0 0 rgba(0, 255, 0, 0);
        }
    }
</style>

<div class="live-pulse"></div> <strong>LIVE</strong> - Updating every 2 seconds
""", unsafe_allow_html=True)
```

---

## **Change 2: Portfolio Table First, Then Visualizations**

### **Problem**
- Managers want to see holdings first, graphs second
- Current order: Metrics → Graphs → Table (backwards for workflow)
- Table is buried at bottom

### **Solution**

#### **2.1 New Page Structure**

```
NEW VERSION 2 LAYOUT:
┌─────────────────────────────────────────────────┐
│ Header: Logo | Portfolio Dropdown | 🟢 LIVE     │
├─────────────────────────────────────────────────┤
│ Portfolio Summary Metrics (4 cards)             │
├─────────────────────────────────────────────────┤
│ 📈 Live DV01 Ticker (sparkline)                 │
├─────────────────────────────────────────────────┤
│ 📋 PORTFOLIO HOLDINGS TABLE ⭐ MOVED UP         │
│ ┌─────────────────────────────────────────────┐ │
│ │ Issuer | Portfolio | Notional | NPV | DV01  │ │
│ │ Apple  | Tech Sect | $5M      | ... | ...   │ │
│ │ MSFT   | Tech Sect | $8M      | ... | ...   │ │
│ │ ...    | ...       | ...      | ... | ...   │ │
│ │ [150 rows, scrollable]                      │ │
│ └─────────────────────────────────────────────┘ │
│ [Download CSV Button]                           │
├─────────────────────────────────────────────────┤
│ 📊 Risk Analytics & Visualizations              │
│ ┌──────────────┬──────────────┐                 │
│ │ KRD Profile  │ Risk Dist.   │                 │
│ └──────────────┴──────────────┘                 │
│ ┌──────────────┬──────────────┐                 │
│ │ Concentration│ Heatmap      │                 │
│ └──────────────┴──────────────┘                 │
└─────────────────────────────────────────────────┘
```

#### **2.2 Implementation Code**

**File:** `dashboard/app/main.py`

```python
def render_dashboard():
    # ... existing setup ...
    
    # 1. HEADER (unchanged)
    render_header()
    
    # 2. PORTFOLIO SUMMARY METRICS (unchanged)
    render_summary_metrics(aggregates)
    
    # 3. LIVE TICKER (NEW)
    render_live_dv01_ticker(fetcher)
    
    # 4. ⭐ PORTFOLIO TABLE - MOVED HERE (was at bottom)
    st.divider()
    st.subheader("📋 Portfolio Holdings - Detailed View")
    render_portfolio_table(filtered_trades_df, active_filters)
    
    # 5. VISUALIZATIONS - MOVED DOWN (was near top)
    st.divider()
    st.subheader("📊 Risk Analytics & Visualizations")
    render_charts(filtered_trades_df, aggregates)
    
    # 6. HISTORICAL ANALYSIS (remains at bottom)
    render_historical_analysis(fetcher, start_date, end_date)
```

#### **2.3 Enhanced Portfolio Table**

```python
def render_portfolio_table(trades_df, filters):
    """
    Render manager-focused portfolio table.
    
    Enhancements:
    - Issuer names (not ISINs)
    - Sortable columns
    - Download button
    - Summary row at top
    """
    if trades_df.empty:
        st.info("No positions in selected portfolio")
        return
    
    # Prepare display dataframe
    display_df = trades_df.copy()
    
    # Extract issuer from ISIN or use stored metadata
    if 'ISIN' in display_df.columns:
        display_df['Issuer'] = display_df['ISIN'].apply(extract_issuer_name)
    else:
        display_df['Issuer'] = "Corporate Bond"  # Fallback
    
    # Column order optimized for managers
    column_order = [
        'Issuer',           # Company name (readable)
        'Portfolio',        # Which strategy
        'Type',            # BOND/SWAP
        'Currency',        # USD/EUR/etc
        'Notional',        # Face value
        'Coupon',          # Interest rate (if available)
        'NPV',             # Market value
        'DV01',            # Interest rate risk
        'KRD 2Y',          # 2Y key rate risk
        'KRD 5Y',          # 5Y key rate risk
        'KRD 10Y',         # 10Y key rate risk
        'KRD 30Y'          # 30Y key rate risk
    ]
    
    # Filter to available columns
    display_columns = [col for col in column_order if col in display_df.columns]
    table_df = display_df[display_columns].copy()
    
    # Format currency columns
    currency_cols = ['Notional', 'NPV', 'DV01', 'KRD 2Y', 'KRD 5Y', 'KRD 10Y', 'KRD 30Y']
    for col in currency_cols:
        if col in table_df.columns:
            table_df[col] = table_df[col].apply(lambda x: f"${x:,.0f}")
    
    # Format coupon as percentage
    if 'Coupon' in table_df.columns:
        table_df['Coupon'] = table_df['Coupon'].apply(lambda x: f"{x*100:.3f}%")
    
    # Summary metrics above table
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("📊 Total Positions", f"{len(table_df):,}")
    
    with col2:
        total_notional = trades_df['Notional'].sum() if 'Notional' in trades_df.columns else 0
        st.metric("💵 Total Notional", f"${total_notional/1e9:.2f}B")
    
    with col3:
        total_npv = trades_df['NPV'].sum()
        st.metric("📈 Total NPV", f"${total_npv/1e6:.1f}M")
    
    with col4:
        total_dv01 = trades_df['DV01'].sum()
        st.metric("⚠️ Total DV01", f"${total_dv01/1e3:.0f}K")
    
    # Interactive data table with fixed height (scrollable)
    st.dataframe(
        table_df,
        use_container_width=True,
        hide_index=True,
        height=500,  # Fixed height = always visible, scrolls if needed
        column_config={
            "Issuer": st.column_config.TextColumn("Issuer", width="medium"),
            "DV01": st.column_config.TextColumn("DV01 ($)", help="Dollar value of 1bp move")
        }
    )
    
    # Export buttons
    col1, col2 = st.columns([1, 4])
    
    with col1:
        # CSV download
        csv = table_df.to_csv(index=False)
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"portfolio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    
    with col2:
        st.caption(f"Showing {len(table_df)} positions | Last updated: {datetime.now().strftime('%H:%M:%S')}")
```

---

## **Change 3: Use Issuer Names Instead of ISINs on Charts**

### **Problem**
- X-axis labels show ISINs like "US037833CK68"
- Unreadable for users
- Can't quickly identify which company

### **Solution**

#### **3.1 Create Issuer Mapping Function**

**File:** `dashboard/app/utils/issuer_mapping.py` (NEW FILE)

```python
"""
Map ISINs to issuer names for readable chart labels.
"""

# Known ISIN prefix to issuer mapping
ISIN_TO_ISSUER = {
    # Technology
    "US037833": "Apple Inc.",
    "US594918": "Microsoft Corp.",
    "US023135": "Amazon.com Inc.",
    "US02079K": "Alphabet Inc.",
    "US30303M": "Meta Platforms",
    "US68389X": "Oracle Corp.",
    "US17275R": "Cisco Systems",
    "US458140": "Intel Corp.",
    "US459200": "IBM Corp.",
    "US79466L": "Salesforce Inc.",
    
    # Financials
    "US46625H": "JPMorgan Chase",
    "US46647P": "JPMorgan Chase",
    "US060505": "Bank of America",
    "US06051G": "Bank of America",
    "US172967": "Citigroup Inc.",
    "US949746": "Wells Fargo",
    "US95001A": "Wells Fargo",
    "US38141G": "Goldman Sachs",
    "US617446": "Morgan Stanley",
    
    # Healthcare
    "US478160": "Johnson & Johnson",
    "US91324P": "UnitedHealth Group",
    "US717081": "Pfizer Inc.",
    "US002824": "Abbott Labs",
    "US58933Y": "Merck & Co.",
    
    # Consumer
    "US742718": "Procter & Gamble",
    "US191216": "Coca-Cola Co.",
    "US713448": "PepsiCo Inc.",
    "US931142": "Walmart Inc.",
    "US437076": "Home Depot",
    
    # Energy
    "US30231G": "Exxon Mobil",
    "US166764": "Chevron Corp.",
    
    # Telecom
    "US92343V": "Verizon",
    "US00206R": "AT&T Inc.",
    
    # Government
    "US912810": "US Treasury",
}

def extract_issuer_name(isin: str) -> str:
    """
    Extract readable issuer name from ISIN code.
    
    Args:
        isin: ISIN code (e.g., "US037833CK68")
        
    Returns:
        str: Issuer name (e.g., "Apple Inc.")
    """
    if not isin or len(isin) < 8:
        return "Unknown"
    
    # Try full 8-character prefix match
    prefix_8 = isin[:8]
    if prefix_8 in ISIN_TO_ISSUER:
        return ISIN_TO_ISSUER[prefix_8]
    
    # Try 6-character prefix (some mappings use shorter)
    prefix_6 = isin[:6]
    if prefix_6 in ISIN_TO_ISSUER:
        return ISIN_TO_ISSUER[prefix_6]
    
    # Fallback: Return first 6 chars as identifier
    return f"Bond-{isin[:6]}"


def shorten_issuer_name(full_name: str, max_length: int = 15) -> str:
    """
    Shorten issuer name for chart labels.
    
    Examples:
        "Johnson & Johnson" → "J&J"
        "Bank of America Corp." → "Bank of America"
        "Procter & Gamble" → "P&G"
    """
    # Known abbreviations
    abbreviations = {
        "Johnson & Johnson": "J&J",
        "Procter & Gamble": "P&G",
        "Goldman Sachs Group": "Goldman Sachs",
        "JPMorgan Chase & Co.": "JPMorgan",
        "Bank of America Corp.": "BofA",
        "Microsoft Corp.": "Microsoft",
        "Amazon.com Inc.": "Amazon",
        "Alphabet Inc.": "Google",
        "Meta Platforms Inc.": "Meta",
    }
    
    if full_name in abbreviations:
        return abbreviations[full_name]
    
    # Remove common suffixes
    name = full_name.replace(" Inc.", "").replace(" Corp.", "").replace(" Co.", "")
    
    # If still too long, truncate
    if len(name) > max_length:
        return name[:max_length-2] + ".."
    
    return name
```

#### **3.2 Update Charts to Use Issuer Names**

**File:** `dashboard/app/components/charts.py`

```python
# Import new utility
from utils.issuer_mapping import extract_issuer_name, shorten_issuer_name

# Update concentration chart
@staticmethod
def create_concentration_chart(trades_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
    """
    Create bar chart showing top N risk contributors.
    
    V2 Change: Use issuer names on X-axis instead of ISINs.
    """
    # ... existing code ...
    
    # V1 code (OLD):
    # x=top_trades['Instrument ID'],
    
    # V2 code (NEW):
    # Extract issuer names for X-axis
    if 'ISIN' in top_trades.columns:
        top_trades['Issuer Display'] = top_trades['ISIN'].apply(
            lambda x: shorten_issuer_name(extract_issuer_name(x))
        )
    elif 'Full ID' in top_trades.columns:
        top_trades['Issuer Display'] = top_trades['Full ID'].apply(
            lambda x: shorten_issuer_name(extract_issuer_name(x))
        )
    else:
        top_trades['Issuer Display'] = top_trades['Instrument ID']
    
    fig.add_trace(go.Bar(
        x=top_trades['Issuer Display'],  # Changed from Instrument ID
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
        xaxis_title="Issuer",  # Changed from "Instrument ID"
        yaxis_title="DV01 ($)",
        template='plotly_dark',
        height=400,
        showlegend=False,
        xaxis=dict(tickangle=-45)  # Angle for readability
    )
    
    return fig


# Update risk heatmap similarly
@staticmethod
def create_krd_heatmap(trades_df: pd.DataFrame) -> go.Figure:
    """
    Create heatmap showing KRD by instrument and tenor.
    
    V2 Change: Use issuer names on Y-axis.
    """
    # ... existing code ...
    
    # Build Y-axis labels with issuer names
    y_labels = []
    for idx, row in top_trades.iterrows():
        if 'ISIN' in row:
            issuer = shorten_issuer_name(extract_issuer_name(row['ISIN']), max_length=20)
        else:
            issuer = row['Instrument ID'][:15]
        y_labels.append(issuer)
    
    # Create heatmap
    fig = go.Figure(data=go.Heatmap(
        z=z_data,
        x=tenors,
        y=y_labels,  # Now shows issuer names
        # ... rest of config ...
    ))
    
    return fig
```

---

## **Change 4: Fix DV01 Graph Scale Issues**

### **Problem**
- Portfolio breakdown DV01 chart doesn't fit properly
- Bars cut off or compressed
- Scale not appropriate for data range

### **Solution**

#### **4.1 Dynamic Scale Adjustment**

```python
@staticmethod
def create_portfolio_breakdown_chart(trades_df: pd.DataFrame, metric: str = "DV01") -> go.Figure:
    """
    Create bar chart with proper scaling.
    
    V2 Changes:
    - Auto-adjust Y-axis range
    - Add padding above tallest bar
    - Format tick labels
    """
    # ... existing data preparation ...
    
    # Calculate appropriate Y-axis range
    max_value = portfolio_data['Value'].max()
    min_value = portfolio_data['Value'].min()
    
    # Add 20% padding
    y_range = [
        min_value * 0.8 if min_value < 0 else 0,
        max_value * 1.2
    ]
    
    fig.add_trace(go.Bar(
        x=portfolio_data["Display Name"],
        y=portfolio_data["Value"],
        marker=dict(color=colors),
        hovertemplate="<b>%{x}</b><br>" + y_title + ": %{y:,.0f}<extra></extra>",
    ))
    
    fig.update_layout(
        title=f"{metric} by Portfolio",
        xaxis_title="Portfolio",
        yaxis_title=y_title,
        template=template,
        height=450,  # Increased from 400
        showlegend=False,
        xaxis=dict(
            tickangle=-45,  # Angle labels
            automargin=True  # Auto-adjust margins
        ),
        yaxis=dict(
            range=y_range,  # Set calculated range
            tickformat="$,.0f",  # Format as currency
            automargin=True
        ),
        margin=dict(l=80, r=40, t=60, b=100)  # More space for labels
    ))
    
    return fig
```

#### **4.2 Responsive Height Based on Data**

```python
# Adjust chart height based on number of items
def get_chart_height(num_items: int, min_height: int = 400) -> int:
    """
    Calculate appropriate chart height based on number of data points.
    
    Prevents squishing when many items.
    """
    if num_items <= 5:
        return min_height
    elif num_items <= 10:
        return 500
    else:
        # 30px per item beyond 10
        return 500 + (num_items - 10) * 30

# Use in chart creation
height = get_chart_height(len(portfolio_data))
fig.update_layout(height=height)
```

---

## **Change 5: Change Running Icon to Financial Icon**

### **Problem**
- Current icon (🏃) looks like sports website
- Need professional financial appearance

### **Solution**

#### **5.1 Update Page Config**

**File:** `dashboard/app/main.py`

```python
# Current V1:
st.set_page_config(
    page_title="Risk Monitor",
    page_icon="📊",  # or whatever V1 uses
    layout="wide",
    initial_sidebar_state="expanded",
)

# New V2:
st.set_page_config(
    page_title="Fixed Income Risk Monitor",
    page_icon="💹",  # Upward trending chart - professional financial icon
    layout="wide",
    initial_sidebar_state="expanded",
)
```

**Icon Options (choose one):**
- 💹 Chart with upward trend (recommended)
- 📈 Line chart trending up
- 💼 Briefcase (business/finance)
- 💰 Money bag (finance)
- 🏦 Bank building (financial institution)
- 📊 Bar chart (analytics)

---

## 📦 **Additional Enhancements for V2**

### **Bonus Feature 1: Quick Portfolio Switcher**

Add prominent dropdown at top:

```python
# Make portfolio selector more visible
st.markdown("### Select Portfolio")
selected_portfolio = st.selectbox(
    "Manager / Desk",
    options=["All Portfolios"] + [p.name for p in portfolios],
    key="portfolio_selector_main",
    help="Switch between different portfolio managers or trading desks"
)
```

### **Bonus Feature 2: Key Metrics Delta**

Show change from last update:

```python
# Track previous values
if 'prev_dv01' not in st.session_state:
    st.session_state.prev_dv01 = aggregates.total_dv01

# Calculate delta
dv01_delta = aggregates.total_dv01 - st.session_state.prev_dv01

st.metric(
    "Total DV01",
    format_currency(aggregates.total_dv01),
    delta=f"${dv01_delta:+,.0f} vs prev",
    delta_color="inverse"
)

# Update for next cycle
st.session_state.prev_dv01 = aggregates.total_dv01
```

### **Bonus Feature 3: Export with Timestamp**

```python
# Add timestamp to exports
csv = table_df.to_csv(index=False)
filename = f"portfolio_{selected_portfolio}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

st.download_button(
    label="📥 Download Portfolio CSV",
    data=csv,
    file_name=filename,
    mime="text/csv",
    help=f"Export {len(table_df)} positions to Excel/CSV"
)
```

---

## 🧪 **Testing Checklist for V2**

Before deploying to https://risk-monitor.ngrok.app:

### **Real-Time Elements**
- [ ] Live badge shows "🟢 LIVE STREAMING"
- [ ] Status updates every 2 seconds
- [ ] Mini DV01 chart adds new points
- [ ] Pulsing indicator animates smoothly
- [ ] System time clock ticks

### **Table Functionality**
- [ ] Table appears BEFORE visualizations
- [ ] Sortable by clicking column headers
- [ ] Scrollable (500px height, doesn't push content down)
- [ ] Shows issuer names clearly
- [ ] Metrics above table show correct totals
- [ ] CSV download works with timestamp
- [ ] Filters apply to table correctly

### **Issuer Names**
- [ ] Concentration chart X-axis shows company names
- [ ] Heatmap Y-axis shows company names
- [ ] Risk distribution shows companies not ISINs
- [ ] Hover tooltips show full details
- [ ] Names are readable (not cut off)

### **Chart Scaling**
- [ ] Portfolio breakdown DV01 bars fit within view
- [ ] Y-axis has appropriate range
- [ ] Labels not overlapping
- [ ] Responsive to window resize
- [ ] All values visible

### **UI Polish**
- [ ] Icon changed to 💹 or financial alternative
- [ ] Dark theme consistent throughout
- [ ] No layout shifts on refresh
- [ ] Loading states show appropriately
- [ ] Mobile responsive (if applicable)

---

## 🚀 **Deployment Plan**

### **Step 1: Create V2 Branch**
```bash
cd /Users/liuyuxuan/risk_monitor
git checkout -b version-2-improvements
```

### **Step 2: Implement Changes**
Work through each change sequentially:
1. Update icon (5 minutes)
2. Add real-time indicators (30 minutes)
3. Move table before graphs (15 minutes)
4. Add issuer mapping (45 minutes)
5. Fix chart scales (30 minutes)

### **Step 3: Test Locally**
```bash
docker-compose restart dashboard
# Open http://localhost:8501
# Test all checklist items
```

### **Step 4: Deploy to ngrok**
```bash
# Update ngrok deployment
# Test at https://risk-monitor.ngrok.app
```

### **Step 5: Collect Feedback**
- Show to manager
- Get user feedback
- Iterate if needed

---

## 📊 **Before & After Comparison**

### **V1 (Current)**
```
❌ Static appearance
❌ Graphs first, table buried
❌ ISINs on charts (unreadable)
❌ DV01 chart scale issues
❌ Running person icon
✅ Basic functionality works
```

### **V2 (Target)**
```
✅ Live streaming indicators
✅ Table first (manager workflow)
✅ Company names on charts
✅ Proper chart scaling
✅ Professional financial icon
✅ Enhanced user experience
```

---

## 💬 **User Quotes (Expected)**

**V1 Feedback:**
> "Looks like a static PDF report. Can't tell if it's updating."
> "Why do I have to scroll down to see my bonds?"
> "What does US037833CK68 mean? I just want to see 'Apple'."

**V2 Target:**
> "I can see it's live! The green indicator is great."
> "Perfect - I see my holdings first, then the analytics."
> "Much easier to read with company names. Thanks!"

---

## 📚 **Files to Modify**

### **Modified Files:**
1. `dashboard/app/main.py` - Layout reordering, streaming indicators
2. `dashboard/app/components/charts.py` - Issuer names, scaling fixes
3. `dashboard/app/components/themes.py` - Add pulse animation CSS

### **New Files:**
4. `dashboard/app/utils/issuer_mapping.py` - ISIN → Issuer name mapping

### **Configuration:**
5. Update `st.set_page_config()` icon parameter

---

## ⏱️ **Estimated Implementation Time**

| Task | Time | Difficulty |
|------|------|------------|
| Change icon | 5 min | Easy |
| Add live indicators | 30 min | Medium |
| Reorder layout | 15 min | Easy |
| Create issuer mapping | 45 min | Medium |
| Update all charts | 30 min | Medium |
| Fix scaling issues | 30 min | Medium |
| Testing & polish | 60 min | Medium |
| **TOTAL** | **~3.5 hours** | **Medium** |

---

## ✅ **Success Metrics**

V2 is successful if:

1. ✅ Users immediately see "LIVE" status
2. ✅ Portfolio table is first thing they scroll to
3. ✅ No questions about "what is US037833CK68?"
4. ✅ Charts display properly without scrolling sideways
5. ✅ Professional appearance suitable for client demos

---

## 📝 **Implementation Notes**

- Keep V1 in main branch (stable)
- Implement V2 in feature branch
- Test thoroughly before merging
- Can rollback to V1 if issues
- Document any breaking changes

---

## 🎯 **Next Steps**

1. Review this document with team
2. Prioritize which changes are must-have vs. nice-to-have
3. Create implementation branch
4. Start with icon change (quick win)
5. Implement table reordering (high impact)
6. Add issuer names (readability)
7. Polish with streaming indicators
8. Deploy and gather feedback

---

**Document Version:** 1.0  
**Created:** 2026-02-02  
**Status:** Ready for Implementation  
**Target Completion:** TBD

---

Ready to build Version 2! 🚀
