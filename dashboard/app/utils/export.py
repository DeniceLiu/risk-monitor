"""Excel export utilities."""

import pandas as pd
from io import BytesIO
from datetime import datetime
from typing import Dict, Any


class ExcelExporter:
    """Handles Excel export with formatting."""

    @staticmethod
    def create_portfolio_export(trades_df: pd.DataFrame, aggregates: Dict[str, Any]) -> BytesIO:
        """
        Create formatted Excel file with portfolio data.

        Args:
            trades_df: Trade-level data
            aggregates: Portfolio aggregates

        Returns:
            BytesIO: Excel file buffer
        """
        output = BytesIO()

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            workbook = writer.book

            # Define formats
            header_format = workbook.add_format(
                {"bold": True, "bg_color": "#4CAF50", "font_color": "white", "border": 1}
            )

            currency_format = workbook.add_format({"num_format": "$#,##0.00", "border": 1})

            # Sheet 1: Portfolio Summary
            summary_df = pd.DataFrame(
                {
                    "Metric": [
                        "Report Date",
                        "Total Instruments",
                        "Total NPV",
                        "Total DV01",
                        "Total KRD 2Y",
                        "Total KRD 5Y",
                        "Total KRD 10Y",
                        "Total KRD 30Y",
                    ],
                    "Value": [
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        aggregates.get("instrument_count", 0),
                        f"${aggregates.get('total_npv', 0):,.2f}",
                        f"${aggregates.get('total_dv01', 0):,.2f}",
                        f"${aggregates.get('krd_2y', 0):,.2f}",
                        f"${aggregates.get('krd_5y', 0):,.2f}",
                        f"${aggregates.get('krd_10y', 0):,.2f}",
                        f"${aggregates.get('krd_30y', 0):,.2f}",
                    ],
                }
            )

            summary_df.to_excel(writer, sheet_name="Summary", index=False)
            summary_sheet = writer.sheets["Summary"]
            summary_sheet.set_column("A:A", 20)
            summary_sheet.set_column("B:B", 25)

            # Apply header format
            for col_num, value in enumerate(summary_df.columns.values):
                summary_sheet.write(0, col_num, value, header_format)

            # Sheet 2: Trade Details
            if not trades_df.empty:
                # Create a copy for export (with numeric values, not formatted strings)
                export_df = trades_df.copy()
                export_df.to_excel(writer, sheet_name="Trade Details", index=False)
                trades_sheet = writer.sheets["Trade Details"]

                # Format columns
                for idx, col in enumerate(export_df.columns):
                    trades_sheet.write(0, idx, col, header_format)

                    if col in ["NPV", "DV01", "KRD 2Y", "KRD 5Y", "KRD 10Y", "KRD 30Y"]:
                        trades_sheet.set_column(idx, idx, 15, currency_format)
                    else:
                        trades_sheet.set_column(idx, idx, 15)

            # Sheet 3: Risk Breakdown
            if not trades_df.empty and "Type" in trades_df.columns:
                # By instrument type
                numeric_cols = ["NPV", "DV01"]
                available_cols = [c for c in numeric_cols if c in trades_df.columns]

                if available_cols:
                    type_breakdown = (
                        trades_df.groupby("Type")[available_cols].sum().reset_index()
                    )
                    type_breakdown.to_excel(
                        writer, sheet_name="Risk Breakdown", index=False, startrow=1
                    )

                    breakdown_sheet = writer.sheets["Risk Breakdown"]
                    breakdown_sheet.write(0, 0, "Risk by Instrument Type", header_format)

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

        with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
            historical_df.to_excel(writer, sheet_name="Historical Data", index=False)

            workbook = writer.book
            worksheet = writer.sheets["Historical Data"]

            # Add chart if we have data
            if len(historical_df) > 1:
                chart = workbook.add_chart({"type": "line"})
                chart.add_series(
                    {
                        "name": "DV01",
                        "categories": ["Historical Data", 1, 0, len(historical_df), 0],
                        "values": ["Historical Data", 1, 1, len(historical_df), 1],
                    }
                )
                chart.set_title({"name": "Portfolio DV01 Over Time"})
                chart.set_x_axis({"name": "Date"})
                chart.set_y_axis({"name": "DV01 ($)"})

                worksheet.insert_chart("D2", chart)

        output.seek(0)
        return output
