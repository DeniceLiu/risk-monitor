"""Advanced chart components using Plotly."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st

from utils.issuer_mapping import extract_issuer_name, shorten_label


def _issuer_label(row: pd.Series) -> str:
    """Derive a readable issuer label from a trade row."""
    isin = row.get("ISIN", "")
    if isin:
        return shorten_label(extract_issuer_name(isin))
    return shorten_label(str(row.get("Instrument ID", "Unknown")))


class AdvancedCharts:
    """Creates advanced plotly charts."""

    @staticmethod
    def get_template() -> str:
        """Get plotly template based on current theme."""
        return "plotly_dark" if st.session_state.get("theme", "dark") == "dark" else "plotly_white"

    # ------------------------------------------------------------------
    # Live mini sparkline (NEW for V2)
    # ------------------------------------------------------------------
    @staticmethod
    def create_mini_live_chart(historical_df: pd.DataFrame) -> go.Figure:
        """Create a compact sparkline-style chart for the live DV01 ticker."""
        template = AdvancedCharts.get_template()
        is_dark = template == "plotly_dark"

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=historical_df["timestamp"],
                y=historical_df["dv01"],
                mode="lines",
                line=dict(color="#00c853", width=2),
                hovertemplate="DV01: $%{y:,.0f}<br>%{x|%H:%M:%S}<extra></extra>",
            )
        )

        bg = "rgba(0,0,0,0)"
        grid_color = "rgba(255,255,255,0.08)" if is_dark else "rgba(0,0,0,0.06)"

        # Auto-fit y-axis around actual data
        dv01_min = historical_df["dv01"].min()
        dv01_max = historical_df["dv01"].max()
        margin = (dv01_max - dv01_min) * 0.1 if dv01_max != dv01_min else abs(dv01_max) * 0.05
        y_range = [dv01_min - margin, dv01_max + margin]

        fig.update_layout(
            height=130,
            margin=dict(l=0, r=0, t=0, b=0),
            xaxis=dict(showgrid=False, showticklabels=True, tickformat="%H:%M:%S"),
            yaxis=dict(showgrid=True, gridcolor=grid_color, tickformat="$,.0f", range=y_range),
            plot_bgcolor=bg,
            paper_bgcolor=bg,
            hovermode="x unified",
            template=template,
            showlegend=False,
        )
        return fig

    # ------------------------------------------------------------------
    # Yield Curve snapshot + time series (NEW)
    # ------------------------------------------------------------------
    @staticmethod
    def create_yield_curve_chart(rates: dict) -> go.Figure:
        """Create a yield curve chart from current rates snapshot."""
        template = AdvancedCharts.get_template()
        # Order tenors by maturity
        tenor_order = ["1M", "3M", "6M", "1Y", "2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        tenors = [t for t in tenor_order if t in rates]
        values = [rates[t] * 100 for t in tenors]  # convert to percent

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=tenors,
                y=values,
                mode="lines+markers",
                line=dict(color="#2196F3", width=3),
                marker=dict(size=8),
                hovertemplate="<b>%{x}</b><br>Rate: %{y:.3f}%<extra></extra>",
            )
        )
        fig.update_layout(
            title="USD Yield Curve (Current)",
            xaxis_title="Tenor",
            yaxis_title="Rate (%)",
            template=template,
            height=320,
            margin=dict(l=60, r=20, t=50, b=40),
            yaxis=dict(tickformat=".2f", automargin=True),
        )
        return fig

    @staticmethod
    def create_yield_curve_timeseries(history_df: pd.DataFrame) -> go.Figure:
        """Create time series of key yield curve tenors."""
        template = AdvancedCharts.get_template()

        if history_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="Collecting yield curve history...",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=320)
            return fig

        key_tenors = ["2Y", "5Y", "10Y", "30Y"]
        colors = {"2Y": "#26A69A", "5Y": "#42A5F5", "10Y": "#FFA726", "30Y": "#EF5350"}

        fig = go.Figure()
        for tenor in key_tenors:
            if tenor in history_df.columns:
                fig.add_trace(
                    go.Scatter(
                        x=history_df["timestamp"],
                        y=history_df[tenor] * 100,
                        mode="lines",
                        name=tenor,
                        line=dict(color=colors.get(tenor, "#999"), width=2),
                        hovertemplate=f"{tenor}: %{{y:.3f}}%<br>%{{x|%H:%M:%S}}<extra></extra>",
                    )
                )

        fig.update_layout(
            title="Yield Curve Rates Over Time",
            xaxis_title="Time",
            yaxis_title="Rate (%)",
            template=template,
            height=320,
            margin=dict(l=60, r=20, t=50, b=40),
            hovermode="x unified",
            yaxis=dict(tickformat=".3f", automargin=True),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig

    # ------------------------------------------------------------------
    # Historical DV01 — fixed scaling (no fill-to-zero, auto-fit y-axis)
    # ------------------------------------------------------------------
    @staticmethod
    def create_historical_dv01_chart(historical_df: pd.DataFrame) -> go.Figure:
        """Create line chart showing DV01 over time with auto-fit scaling."""
        template = AdvancedCharts.get_template()

        if historical_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No historical data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=400)
            return fig

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=historical_df["timestamp"],
                y=historical_df["dv01"],
                mode="lines",
                name="DV01",
                line=dict(color="#4CAF50", width=2),
                fill="tozeroy",
                fillcolor="rgba(76,175,80,0.10)",
            )
        )

        if len(historical_df) >= 10:
            historical_df = historical_df.copy()
            historical_df["dv01_ma"] = historical_df["dv01"].rolling(window=10).mean()
            fig.add_trace(
                go.Scatter(
                    x=historical_df["timestamp"],
                    y=historical_df["dv01_ma"],
                    mode="lines",
                    name="Moving Avg (10)",
                    line=dict(color="#FF9800", width=2, dash="dash"),
                )
            )

        # Auto-fit y-axis around actual data range with 10% padding
        dv01_min = historical_df["dv01"].min()
        dv01_max = historical_df["dv01"].max()
        spread = dv01_max - dv01_min
        margin = spread * 0.10 if spread > 0 else abs(dv01_max) * 0.10
        y_range = [dv01_min - margin, dv01_max + margin]

        fig.update_layout(
            title="Portfolio DV01 Over Time",
            xaxis_title="Time",
            yaxis_title="DV01 ($)",
            hovermode="x unified",
            template=template,
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            yaxis=dict(range=y_range, tickformat="$,.0f", automargin=True),
        )
        return fig

    # ------------------------------------------------------------------
    # Concentration bar — V2: issuer names on x-axis
    # ------------------------------------------------------------------
    @staticmethod
    def create_concentration_chart(trades_df: pd.DataFrame, top_n: int = 10) -> go.Figure:
        """Create bar chart showing top N risk contributors (by issuer name)."""
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trade data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=400)
            return fig

        df = trades_df.copy()
        df["DV01_Abs"] = df["DV01"].abs()
        top_trades = df.nlargest(top_n, "DV01_Abs").copy()

        total_dv01 = df["DV01_Abs"].sum()
        top_trades["Percentage"] = (
            top_trades["DV01_Abs"] / total_dv01 * 100 if total_dv01 > 0 else 0
        )

        # V2: readable issuer labels
        top_trades["Issuer"] = top_trades.apply(_issuer_label, axis=1)

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=top_trades["Issuer"],
                y=top_trades["DV01"],
                text=top_trades["Percentage"].apply(lambda x: f"{x:.1f}%"),
                textposition="outside",
                marker=dict(
                    color=top_trades["DV01"],
                    colorscale="RdYlGn",
                    showscale=True,
                    colorbar=dict(title="DV01 ($)"),
                ),
                hovertemplate="<b>%{x}</b><br>DV01: $%{y:,.0f}<br>%{text} of total<extra></extra>",
            )
        )

        fig.update_layout(
            title=f"Top {top_n} Risk Contributors",
            xaxis_title="Issuer",
            yaxis_title="DV01 ($)",
            template=template,
            height=400,
            showlegend=False,
            xaxis=dict(tickangle=-45, automargin=True),
            yaxis=dict(automargin=True),
            margin=dict(b=100),
        )
        return fig

    # ------------------------------------------------------------------
    # Concentration pie — V2: issuer names
    # ------------------------------------------------------------------
    @staticmethod
    def create_concentration_pie(trades_df: pd.DataFrame, top_n: int = 5) -> go.Figure:
        """Create pie chart showing concentration risk (by issuer name)."""
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.update_layout(template=template, height=400)
            return fig

        df = trades_df.copy()
        df["DV01_Abs"] = df["DV01"].abs()
        top_trades = df.nlargest(top_n, "DV01_Abs").copy()

        top_sum = top_trades["DV01_Abs"].sum()
        others_sum = df["DV01_Abs"].sum() - top_sum

        # V2: issuer labels
        top_trades["Issuer"] = top_trades.apply(_issuer_label, axis=1)

        labels = list(top_trades["Issuer"]) + (["Others"] if others_sum > 0 else [])
        values = list(top_trades["DV01_Abs"]) + ([others_sum] if others_sum > 0 else [])

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=labels,
                    values=values,
                    hole=0.3,
                    marker=dict(colors=px.colors.qualitative.Set3),
                )
            ]
        )
        fig.update_layout(title="Risk Concentration Distribution", template=template, height=400)
        return fig

    # ------------------------------------------------------------------
    # KRD Heatmap — V2: issuer names on y-axis
    # ------------------------------------------------------------------
    @staticmethod
    def create_krd_heatmap(trades_df: pd.DataFrame) -> go.Figure:
        """Create heatmap showing KRD by instrument and tenor (issuer names)."""
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trade data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=500)
            return fig

        tenors = ["2Y", "5Y", "10Y", "30Y"]
        krd_columns = ["KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]
        available_krd = [col for col in krd_columns if col in trades_df.columns]
        if not available_krd:
            fig = go.Figure()
            fig.add_annotation(
                text="No KRD data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=500)
            return fig

        df = trades_df.copy()
        df["Total_KRD"] = df[available_krd].abs().sum(axis=1)
        top_trades = df.nlargest(min(15, len(df)), "Total_KRD")

        z_data = []
        y_labels = []
        for _, row in top_trades.iterrows():
            z_data.append([row.get(col, 0) for col in krd_columns])
            # V2: issuer name instead of truncated ISIN
            y_labels.append(_issuer_label(row))

        fig = go.Figure(
            data=go.Heatmap(
                z=z_data,
                x=tenors,
                y=y_labels,
                colorscale="RdYlGn",
                zmid=0,
                colorbar=dict(title="KRD ($)"),
                hovertemplate="Instrument: %{y}<br>Tenor: %{x}<br>KRD: $%{z:,.0f}<extra></extra>",
            )
        )

        num_rows = len(y_labels)
        chart_height = max(400, 40 * num_rows + 120)

        fig.update_layout(
            title="Key Rate Duration Heatmap (Top Trades)",
            xaxis_title="Tenor",
            yaxis_title="Issuer",
            template=template,
            height=chart_height,
            yaxis=dict(tickmode="linear", automargin=True),
        )
        return fig

    # ------------------------------------------------------------------
    # Portfolio breakdown — V2: fixed scaling
    # ------------------------------------------------------------------
    @staticmethod
    def create_portfolio_breakdown_chart(trades_df: pd.DataFrame, metric: str = "DV01") -> go.Figure:
        """Create bar chart showing metric breakdown by portfolio with proper scaling."""
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trade data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=450)
            return fig

        df = trades_df.copy()
        group_col = "Portfolio ID" if "Portfolio ID" in df.columns else "Portfolio"

        if group_col not in df.columns:
            fig = go.Figure()
            fig.add_annotation(
                text="No portfolio data available",
                xref="paper", yref="paper", x=0.5, y=0.5, showarrow=False,
            )
            fig.update_layout(template=template, height=450)
            return fig

        df[group_col] = df[group_col].fillna("DEFAULT").replace("", "DEFAULT")

        if metric == "Count":
            portfolio_data = df.groupby(group_col).size().reset_index(name="Value")
            y_title = "Number of Instruments"
        elif metric == "Notional":
            portfolio_data = df.groupby(group_col)["Notional"].sum().reset_index(name="Value")
            y_title = "Notional ($)"
        elif metric == "NPV":
            portfolio_data = df.groupby(group_col)["NPV"].sum().reset_index(name="Value")
            y_title = "NPV ($)"
        else:
            portfolio_data = df.groupby(group_col)["DV01"].sum().reset_index(name="Value")
            y_title = "DV01 ($)"

        portfolio_data = portfolio_data.sort_values("Value", ascending=False)

        portfolio_names = {
            "CREDIT_IG": "IG Credit",
            "CREDIT_HY": "HY Credit",
            "GOVT_US": "US Govt",
            "TECH_SECTOR": "Tech Sector",
            "FINANCIAL_SECTOR": "Financials",
            "CONSUMER_DISCRETIONARY": "Consumer Disc.",
            "HEALTHCARE_PHARMA": "Healthcare",
            "ENERGY_UTILITIES": "Energy & Util.",
            "TELECOM_MEDIA": "Telecom",
            "EMERGING_MARKETS": "EM",
            "DEFAULT": "Unassigned",
        }

        portfolio_data["Display Name"] = portfolio_data[group_col].apply(
            lambda x: portfolio_names.get(x, x.replace("_", " ").title() if x else "Unassigned")
        )

        colors = px.colors.qualitative.Set2[: len(portfolio_data)]

        fig = go.Figure()
        fig.add_trace(
            go.Bar(
                x=portfolio_data["Display Name"],
                y=portfolio_data["Value"],
                marker=dict(color=colors),
                hovertemplate="<b>%{x}</b><br>" + y_title + ": %{y:,.0f}<extra></extra>",
            )
        )

        # V2: proper y-axis range with 20% padding
        max_val = portfolio_data["Value"].max()
        min_val = portfolio_data["Value"].min()
        y_range = [
            min_val * 1.2 if min_val < 0 else 0,
            max_val * 1.25 if max_val > 0 else 0,
        ]

        num_items = len(portfolio_data)
        chart_height = 450 if num_items <= 6 else 450 + (num_items - 6) * 25

        fig.update_layout(
            title=f"{metric} by Portfolio",
            xaxis_title="Portfolio",
            yaxis_title=y_title,
            template=template,
            height=chart_height,
            showlegend=False,
            xaxis=dict(tickangle=-45, automargin=True),
            yaxis=dict(range=y_range, tickformat="$,.0f", automargin=True),
            margin=dict(l=80, r=40, t=60, b=100),
        )
        return fig

    # ------------------------------------------------------------------
    # Portfolio pie chart
    # ------------------------------------------------------------------
    @staticmethod
    def create_portfolio_pie_chart(trades_df: pd.DataFrame, metric: str = "DV01") -> go.Figure:
        """Create pie chart showing portfolio allocation."""
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.update_layout(template=template, height=400)
            return fig

        df = trades_df.copy()
        group_col = "Portfolio ID" if "Portfolio ID" in df.columns else "Portfolio"

        if group_col not in df.columns:
            fig = go.Figure()
            fig.update_layout(template=template, height=400)
            return fig

        df[group_col] = df[group_col].fillna("DEFAULT").replace("", "DEFAULT")

        if metric == "Count":
            portfolio_data = df.groupby(group_col).size().reset_index(name="Value")
        elif metric == "Notional":
            portfolio_data = df.groupby(group_col)["Notional"].sum().reset_index(name="Value")
        elif metric == "NPV":
            portfolio_data = df.groupby(group_col)["NPV"].sum().abs().reset_index(name="Value")
        else:
            portfolio_data = df.groupby(group_col)["DV01"].sum().abs().reset_index(name="Value")

        portfolio_names = {
            "CREDIT_IG": "IG Credit",
            "CREDIT_HY": "HY Credit",
            "GOVT_US": "US Govt",
            "TECH_SECTOR": "Tech Sector",
            "FINANCIAL_SECTOR": "Financials",
            "CONSUMER_DISCRETIONARY": "Consumer Disc.",
            "HEALTHCARE_PHARMA": "Healthcare",
            "ENERGY_UTILITIES": "Energy & Util.",
            "TELECOM_MEDIA": "Telecom",
            "EMERGING_MARKETS": "EM",
            "DEFAULT": "Unassigned",
        }

        portfolio_data["Display Name"] = portfolio_data[group_col].apply(
            lambda x: portfolio_names.get(x, x.replace("_", " ").title() if x else "Unassigned")
        )

        fig = go.Figure(
            data=[
                go.Pie(
                    labels=portfolio_data["Display Name"],
                    values=portfolio_data["Value"],
                    hole=0.4,
                    marker=dict(colors=px.colors.qualitative.Set2),
                    textinfo="percent+label",
                    textposition="outside",
                )
            ]
        )

        fig.update_layout(
            title=f"Portfolio Allocation by {metric}",
            template=template,
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3),
        )
        return fig

    # ------------------------------------------------------------------
    # Portfolio comparison
    # ------------------------------------------------------------------
    @staticmethod
    def create_portfolio_comparison_chart(
        trades_df: pd.DataFrame, portfolios: list
    ) -> go.Figure:
        """Create grouped bar chart comparing multiple portfolios."""
        template = AdvancedCharts.get_template()

        if trades_df.empty or not portfolios:
            fig = go.Figure()
            fig.update_layout(template=template, height=400)
            return fig

        df = trades_df.copy()
        portfolio_ids = [p.id for p in portfolios[:6]]

        data = []
        for pid in portfolio_ids:
            pdata = df[df["Portfolio"] == pid]
            if not pdata.empty:
                data.append({
                    "Portfolio": pid.replace("_", " ").title(),
                    "NPV": pdata["NPV"].sum() / 1e6,
                    "DV01": pdata["DV01"].sum() / 1e3,
                    "Instruments": len(pdata),
                })

        if not data:
            fig = go.Figure()
            fig.add_annotation(text="No data for selected portfolios", x=0.5, y=0.5, showarrow=False)
            fig.update_layout(template=template, height=400)
            return fig

        compare_df = pd.DataFrame(data)

        fig = go.Figure()
        fig.add_trace(go.Bar(name="NPV ($M)", x=compare_df["Portfolio"], y=compare_df["NPV"]))
        fig.add_trace(go.Bar(name="DV01 ($K)", x=compare_df["Portfolio"], y=compare_df["DV01"]))
        fig.add_trace(go.Bar(name="Instruments", x=compare_df["Portfolio"], y=compare_df["Instruments"]))

        fig.update_layout(
            title="Portfolio Comparison",
            barmode="group",
            template=template,
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        return fig

    # ------------------------------------------------------------------
    # Dual-axis DV01 + NPV
    # ------------------------------------------------------------------
    @staticmethod
    def create_dual_axis_chart(dv01_df: pd.DataFrame, npv_df: pd.DataFrame) -> go.Figure:
        """Create chart with DV01 and NPV on dual axes."""
        template = AdvancedCharts.get_template()

        fig = go.Figure()

        if not dv01_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=dv01_df["timestamp"],
                    y=dv01_df["dv01"],
                    name="DV01",
                    yaxis="y",
                    line=dict(color="#4CAF50", width=2),
                    fill="tozeroy",
                    fillcolor="rgba(76,175,80,0.08)",
                )
            )

        if not npv_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=npv_df["timestamp"],
                    y=npv_df["npv"],
                    name="NPV",
                    yaxis="y2",
                    line=dict(color="#2196F3", width=2),
                )
            )

        fig.update_layout(
            title="DV01 & NPV Over Time",
            xaxis=dict(title="Time"),
            yaxis=dict(
                title="DV01 ($)",
                titlefont=dict(color="#4CAF50"),
                tickfont=dict(color="#4CAF50"),
                tickformat="$,.0f",
                automargin=True,
            ),
            yaxis2=dict(
                title="NPV ($)",
                titlefont=dict(color="#2196F3"),
                tickfont=dict(color="#2196F3"),
                tickformat="$,.0f",
                overlaying="y",
                side="right",
                automargin=True,
            ),
            hovermode="x unified",
            template=template,
            height=400,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        return fig
