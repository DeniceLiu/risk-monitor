"""Yield curve building with QuantLib.

Implements dual-curve framework:
- OIS curve for discounting
- SOFR curve for forecasting (same as OIS post-LIBOR transition)
"""

import logging
from datetime import date
from typing import Dict, Optional

import QuantLib as ql

logger = logging.getLogger(__name__)


class YieldCurveBuilder:
    """Builds and maintains QuantLib yield curves from market data.

    Uses mutable Quote objects so curves auto-recalibrate when rates change.
    """

    # Standard tenors we support
    TENORS = {
        "1M": ql.Period(1, ql.Months),
        "3M": ql.Period(3, ql.Months),
        "6M": ql.Period(6, ql.Months),
        "1Y": ql.Period(1, ql.Years),
        "2Y": ql.Period(2, ql.Years),
        "3Y": ql.Period(3, ql.Years),
        "5Y": ql.Period(5, ql.Years),
        "7Y": ql.Period(7, ql.Years),
        "10Y": ql.Period(10, ql.Years),
        "20Y": ql.Period(20, ql.Years),
        "30Y": ql.Period(30, ql.Years),
    }

    def __init__(self):
        """Initialize the curve builder."""
        self._quotes: Dict[str, ql.SimpleQuote] = {}
        self._curve: Optional[ql.YieldTermStructureHandle] = None
        self._curve_date: Optional[date] = None

        # Initialize quotes with zero values
        for tenor in self.TENORS:
            self._quotes[tenor] = ql.SimpleQuote(0.0)

    def update_rates(self, rates: Dict[str, float], curve_date: str) -> None:
        """Update quote values from market data.

        Args:
            rates: Dict mapping tenor strings to rate values
            curve_date: Date string in YYYY-MM-DD format
        """
        for tenor, rate in rates.items():
            if tenor in self._quotes:
                self._quotes[tenor].setValue(rate)

        # Parse and set evaluation date
        year, month, day = map(int, curve_date.split("-"))
        eval_date = ql.Date(day, month, year)
        ql.Settings.instance().evaluationDate = eval_date
        self._curve_date = date(year, month, day)

        # Build curve if not already built
        if self._curve is None:
            self._build_curve(eval_date)

        logger.debug(f"Updated rates for {curve_date}: {len(rates)} tenors")

    def _build_curve(self, eval_date: ql.Date) -> None:
        """Build the yield curve using swap rate helpers."""
        calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)
        settlement_days = 2

        # Create rate helpers from quotes
        helpers = []

        # Use deposit rates for short end (up to 1Y)
        short_tenors = ["1M", "3M", "6M", "1Y"]
        for tenor in short_tenors:
            if tenor in self._quotes:
                helper = ql.DepositRateHelper(
                    ql.QuoteHandle(self._quotes[tenor]),
                    self.TENORS[tenor],
                    settlement_days,
                    calendar,
                    ql.ModifiedFollowing,
                    True,  # end of month
                    ql.Actual360()
                )
                helpers.append(helper)

        # Use swap rates for long end (2Y+)
        long_tenors = ["2Y", "3Y", "5Y", "7Y", "10Y", "20Y", "30Y"]
        sofr_index = ql.Sofr()

        for tenor in long_tenors:
            if tenor in self._quotes:
                helper = ql.OISRateHelper(
                    settlement_days,
                    self.TENORS[tenor],
                    ql.QuoteHandle(self._quotes[tenor]),
                    sofr_index
                )
                helpers.append(helper)

        if not helpers:
            logger.warning("No rate helpers available, curve not built")
            return

        # Bootstrap the curve
        curve = ql.PiecewiseLogCubicDiscount(
            eval_date,
            helpers,
            ql.Actual365Fixed()
        )
        curve.enableExtrapolation()

        self._curve = ql.YieldTermStructureHandle(curve)
        logger.info(f"Built yield curve with {len(helpers)} instruments")

    @property
    def curve_handle(self) -> Optional[ql.YieldTermStructureHandle]:
        """Get the yield curve handle for pricing."""
        return self._curve

    @property
    def discount_curve(self) -> Optional[ql.YieldTermStructureHandle]:
        """Get the discount curve (same as forecasting for SOFR)."""
        return self._curve

    @property
    def forecast_curve(self) -> Optional[ql.YieldTermStructureHandle]:
        """Get the forecast curve."""
        return self._curve

    def get_quote(self, tenor: str) -> Optional[ql.SimpleQuote]:
        """Get the quote object for a tenor (for bumping)."""
        return self._quotes.get(tenor)

    def get_discount_factor(self, years: float) -> float:
        """Get discount factor for a given number of years."""
        if self._curve is None:
            return 1.0
        return self._curve.discount(years)

    def get_zero_rate(self, years: float) -> float:
        """Get zero rate for a given number of years."""
        if self._curve is None:
            return 0.0
        return self._curve.zeroRate(
            years, ql.Compounded, ql.Annual
        ).rate()
