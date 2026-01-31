"""Instrument pricing with QuantLib."""

import logging
from dataclasses import dataclass
from datetime import date
from decimal import Decimal
from typing import Optional

import QuantLib as ql

logger = logging.getLogger(__name__)


@dataclass
class BondData:
    """Bond instrument data."""
    id: str
    isin: str
    notional: float
    coupon_rate: float
    maturity_date: date
    issue_date: Optional[date]
    payment_frequency: str
    day_count_convention: str


@dataclass
class SwapData:
    """Swap instrument data."""
    id: str
    notional: float
    fixed_rate: float
    tenor: str
    trade_date: date
    maturity_date: date
    effective_date: Optional[date]
    pay_receive: str  # PAY or RECEIVE
    float_index: str
    payment_frequency: str


def parse_frequency(freq_str: str) -> int:
    """Convert frequency string to QuantLib frequency."""
    freq_map = {
        "ANNUAL": ql.Annual,
        "SEMI_ANNUAL": ql.Semiannual,
        "QUARTERLY": ql.Quarterly,
        "MONTHLY": ql.Monthly,
    }
    return freq_map.get(freq_str, ql.Semiannual)


def parse_day_count(dc_str: str):
    """Convert day count string to QuantLib day counter."""
    dc_map = {
        "ACT_ACT": ql.ActualActual(ql.ActualActual.Bond),
        "ACT_360": ql.Actual360(),
        "ACT_365": ql.Actual365Fixed(),
        "30_360": ql.Thirty360(ql.Thirty360.BondBasis),
    }
    return dc_map.get(dc_str, ql.ActualActual(ql.ActualActual.Bond))


def to_ql_date(d: date):
    """Convert Python date to QuantLib date."""
    return ql.Date(d.day, d.month, d.year)


class BondPricer:
    """Prices fixed-rate bonds using QuantLib."""

    def __init__(self, discount_curve: ql.YieldTermStructureHandle):
        """Initialize with discount curve."""
        self.discount_curve = discount_curve
        self.calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)

    def price(self, bond: BondData) -> float:
        """Calculate bond NPV.

        Args:
            bond: Bond instrument data

        Returns:
            Net present value in currency units
        """
        try:
            # Set up bond schedule
            maturity = to_ql_date(bond.maturity_date)
            issue = to_ql_date(bond.issue_date) if bond.issue_date else maturity - ql.Period(5, ql.Years)

            frequency = parse_frequency(bond.payment_frequency)
            day_count = parse_day_count(bond.day_count_convention)

            schedule = ql.Schedule(
                issue,
                maturity,
                ql.Period(frequency),
                self.calendar,
                ql.Unadjusted,
                ql.Unadjusted,
                ql.DateGeneration.Backward,
                False
            )

            # Create fixed rate bond
            ql_bond = ql.FixedRateBond(
                2,  # settlement days
                bond.notional,
                schedule,
                [bond.coupon_rate],
                day_count
            )

            # Set up pricing engine
            engine = ql.DiscountingBondEngine(self.discount_curve)
            ql_bond.setPricingEngine(engine)

            return ql_bond.NPV()

        except Exception as e:
            logger.error(f"Error pricing bond {bond.id}: {e}")
            raise


class SwapPricer:
    """Prices interest rate swaps using QuantLib."""

    def __init__(
        self,
        discount_curve: ql.YieldTermStructureHandle,
        forecast_curve: ql.YieldTermStructureHandle
    ):
        """Initialize with discount and forecast curves."""
        self.discount_curve = discount_curve
        self.forecast_curve = forecast_curve
        self.calendar = ql.UnitedStates(ql.UnitedStates.GovernmentBond)

    def price(self, swap: SwapData) -> float:
        """Calculate swap NPV.

        Args:
            swap: Swap instrument data

        Returns:
            Net present value in currency units
        """
        try:
            # Determine swap type
            swap_type = ql.Swap.Payer if swap.pay_receive == "PAY" else ql.Swap.Receiver

            # Set dates
            effective = to_ql_date(swap.effective_date) if swap.effective_date else to_ql_date(swap.trade_date) + 2
            maturity = to_ql_date(swap.maturity_date)

            # Create SOFR index linked to forecast curve
            sofr_index = ql.Sofr(self.forecast_curve)

            # Fixed leg parameters
            fixed_frequency = parse_frequency(swap.payment_frequency)
            fixed_day_count = ql.Actual360()

            # Create vanilla swap
            fixed_schedule = ql.Schedule(
                effective,
                maturity,
                ql.Period(fixed_frequency),
                self.calendar,
                ql.ModifiedFollowing,
                ql.ModifiedFollowing,
                ql.DateGeneration.Forward,
                False
            )

            float_schedule = ql.Schedule(
                effective,
                maturity,
                ql.Period(ql.Quarterly),  # SOFR typically quarterly
                self.calendar,
                ql.ModifiedFollowing,
                ql.ModifiedFollowing,
                ql.DateGeneration.Forward,
                False
            )

            # Create the swap
            ql_swap = ql.VanillaSwap(
                swap_type,
                swap.notional,
                fixed_schedule,
                swap.fixed_rate,
                fixed_day_count,
                float_schedule,
                sofr_index,
                0.0,  # spread
                ql.Actual360()
            )

            # Set up pricing engine
            engine = ql.DiscountingSwapEngine(self.discount_curve)
            ql_swap.setPricingEngine(engine)

            return ql_swap.NPV()

        except Exception as e:
            logger.error(f"Error pricing swap {swap.id}: {e}")
            raise
