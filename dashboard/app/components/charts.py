"""Advanced chart components using Plotly."""

import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import streamlit as st


class AdvancedCharts:
    """Creates advanced plotly charts."""

    @staticmethod
    def get_template() -> str:
        """Get plotly template based on current theme."""
        return "plotly_dark" if st.session_state.get("theme", "dark") == "dark" else "plotly_white"

    @staticmethod
    def create_historical_dv01_chart(historical_df: pd.DataFrame) -> go.Figure:
        """
        Create line chart showing DV01 over time.

        Args:
            historical_df: DataFrame with columns [timestamp, dv01]

        Returns:
            Plotly figure
        """
        template = AdvancedCharts.get_template()

        if historical_df.empty:
            # Empty chart placeholder
            fig = go.Figure()
            fig.add_annotation(
                text="No historical data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(template=template, height=400)
            return fig

        fig = go.Figure()

        # Add DV01 line
        fig.add_trace(
            go.Scatter(
                x=historical_df["timestamp"],
                y=historical_df["dv01"],
                mode="lines",
                name="DV01",
                line=dict(color="#4CAF50", width=2),
                fill="tozeroy",
                fillcolor="rgba(76, 175, 80, 0.1)",
            )
        )

        # Add moving average (if enough data)
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

        fig.update_layout(
            title="Portfolio DV01 Over Time",
            xaxis_title="Time",
            yaxis_title="DV01 ($)",
            hovermode="x unified",
            template=template,
            height=400,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )

        return fig

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
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trade data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(template=template, height=400)
            return fig

        # Get top contributors by absolute DV01
        df = trades_df.copy()
        df["DV01_Abs"] = df["DV01"].abs()
        top_trades = df.nlargest(top_n, "DV01_Abs")

        # Calculate percentage of total
        total_dv01 = df["DV01_Abs"].sum()
        if total_dv01 > 0:
            top_trades["Percentage"] = top_trades["DV01_Abs"] / total_dv01 * 100
        else:
            top_trades["Percentage"] = 0

        # Create bar chart
        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=top_trades["Instrument ID"],
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
            xaxis_title="Instrument ID",
            yaxis_title="DV01 ($)",
            template=template,
            height=400,
            showlegend=False,
        )

        return fig

    @staticmethod
    def create_concentration_pie(trades_df: pd.DataFrame, top_n: int = 5) -> go.Figure:
        """
        Create pie chart showing concentration risk.

        Args:
            trades_df: Trade-level data
            top_n: Number of top trades to show

        Returns:
            Plotly figure
        """
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.update_layout(template=template, height=400)
            return fig

        df = trades_df.copy()
        df["DV01_Abs"] = df["DV01"].abs()
        top_trades = df.nlargest(top_n, "DV01_Abs")

        # Top N + "Others"
        top_sum = top_trades["DV01_Abs"].sum()
        others_sum = df["DV01_Abs"].sum() - top_sum

        labels = list(top_trades["Instrument ID"]) + (["Others"] if others_sum > 0 else [])
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

    @staticmethod
    def create_krd_heatmap(trades_df: pd.DataFrame) -> go.Figure:
        """
        Create heatmap showing KRD by instrument and tenor.

        Args:
            trades_df: Trade-level data with KRD columns

        Returns:
            Plotly figure
        """
        template = AdvancedCharts.get_template()

        if trades_df.empty:
            fig = go.Figure()
            fig.add_annotation(
                text="No trade data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(template=template, height=500)
            return fig

        # Prepare matrix data
        tenors = ["2Y", "5Y", "10Y", "30Y"]
        krd_columns = ["KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]

        # Check if we have KRD columns
        available_krd = [col for col in krd_columns if col in trades_df.columns]
        if not available_krd:
            fig = go.Figure()
            fig.add_annotation(
                text="No KRD data available",
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                showarrow=False,
            )
            fig.update_layout(template=template, height=500)
            return fig

        df = trades_df.copy()

        # Get top 15 trades by total KRD
        df["Total_KRD"] = df[available_krd].abs().sum(axis=1)
        top_trades = df.nlargest(min(15, len(df)), "Total_KRD")

        # Build matrix
        z_data = []
        y_labels = []

        for _, row in top_trades.iterrows():
            z_data.append([row.get(col, 0) for col in krd_columns])
            inst_id = str(row["Instrument ID"])
            y_labels.append(inst_id[:12] + "..." if len(inst_id) > 12 else inst_id)

        # Create heatmap
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

        fig.update_layout(
            title="Key Rate Duration Heatmap (Top Trades)",
            xaxis_title="Tenor",
            yaxis_title="Instrument",
            template=template,
            height=500,
            yaxis=dict(tickmode="linear"),
        )

        return fig

    @staticmethod
    def create_dual_axis_chart(dv01_df: pd.DataFrame, npv_df: pd.DataFrame) -> go.Figure:
        """
        Create chart with DV01 and NPV on dual axes.

        Args:
            dv01_df: DataFrame with columns [timestamp, dv01]
            npv_df: DataFrame with columns [timestamp, npv]

        Returns:
            Plotly figure
        """
        template = AdvancedCharts.get_template()

        fig = go.Figure()

        if not dv01_df.empty:
            # DV01 on primary axis
            fig.add_trace(
                go.Scatter(
                    x=dv01_df["timestamp"],
                    y=dv01_df["dv01"],
                    name="DV01",
                    yaxis="y",
                    line=dict(color="#4CAF50", width=2),
                )
            )

        if not npv_df.empty:
            # NPV on secondary axis
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
            title="Portfolio Metrics Over Time",
            xaxis=dict(title="Time"),
            yaxis=dict(
                title="DV01 ($)", titlefont=dict(color="#4CAF50"), tickfont=dict(color="#4CAF50")
            ),
            yaxis2=dict(
                title="NPV ($)",
                titlefont=dict(color="#2196F3"),
                tickfont=dict(color="#2196F3"),
                overlaying="y",
                side="right",
            ),
            hovermode="x unified",
            template=template,
            height=400,
        )

        return fig
