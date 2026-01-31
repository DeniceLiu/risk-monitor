"""Risk calculations using bump-and-reprice method."""

import logging
from dataclasses import dataclass
from typing import Dict, List, Optional, Union

from .curves import YieldCurveBuilder
from .instruments import BondData, SwapData, BondPricer, SwapPricer

logger = logging.getLogger(__name__)


@dataclass
class RiskMetrics:
    """Risk metrics for an instrument."""
    instrument_id: str
    npv: float
    dv01: float  # Dollar value of 1 basis point
    krd: Dict[str, float]  # Key rate durations by tenor


class RiskCalculator:
    """Calculates risk metrics using bump-and-reprice."""

    # Key rate tenors for KRD calculation
    KRD_TENORS = ["2Y", "5Y", "10Y", "30Y"]

    def __init__(self, curve_builder: YieldCurveBuilder, bump_size: float = 0.0001):
        """Initialize risk calculator.

        Args:
            curve_builder: Yield curve builder with mutable quotes
            bump_size: Size of rate bump in decimal (0.0001 = 1bp)
        """
        self.curve_builder = curve_builder
        self.bump_size = bump_size

    def calculate(
        self,
        instrument: Union[BondData, SwapData]
    ) -> RiskMetrics:
        """Calculate all risk metrics for an instrument.

        Args:
            instrument: Bond or Swap data

        Returns:
            RiskMetrics with NPV, DV01, and KRD
        """
        # Get base NPV
        base_npv = self._price_instrument(instrument)

        # Calculate DV01 (parallel shift)
        dv01 = self._calculate_dv01(instrument, base_npv)

        # Calculate KRD (key rate durations)
        krd = self._calculate_krd(instrument, base_npv)

        return RiskMetrics(
            instrument_id=instrument.id,
            npv=base_npv,
            dv01=dv01,
            krd=krd
        )

    def _price_instrument(self, instrument: Union[BondData, SwapData]) -> float:
        """Price an instrument using current curves."""
        curve = self.curve_builder.curve_handle
        if curve is None:
            raise ValueError("Yield curve not built")

        if isinstance(instrument, BondData):
            pricer = BondPricer(curve)
            return pricer.price(instrument)
        else:
            pricer = SwapPricer(curve, curve)  # Same curve for discount/forecast
            return pricer.price(instrument)

    def _calculate_dv01(
        self,
        instrument: Union[BondData, SwapData],
        base_npv: float
    ) -> float:
        """Calculate DV01 via parallel curve shift.

        DV01 = (NPV_down - NPV_up) / 2

        Uses central difference for better accuracy.
        """
        # Store original values
        original_values = {}
        for tenor in YieldCurveBuilder.TENORS:
            quote = self.curve_builder.get_quote(tenor)
            if quote is not None:
                original_values[tenor] = quote.value()

        try:
            # Bump up all tenors
            for tenor, orig_value in original_values.items():
                quote = self.curve_builder.get_quote(tenor)
                quote.setValue(orig_value + self.bump_size)

            npv_up = self._price_instrument(instrument)

            # Bump down all tenors
            for tenor, orig_value in original_values.items():
                quote = self.curve_builder.get_quote(tenor)
                quote.setValue(orig_value - self.bump_size)

            npv_down = self._price_instrument(instrument)

            # DV01 = (NPV_down - NPV_up) / 2
            # Positive DV01 means lose money when rates rise
            dv01 = (npv_down - npv_up) / 2

            return dv01

        finally:
            # Restore original values
            for tenor, orig_value in original_values.items():
                quote = self.curve_builder.get_quote(tenor)
                quote.setValue(orig_value)

    def _calculate_krd(
        self,
        instrument: Union[BondData, SwapData],
        base_npv: float
    ) -> Dict[str, float]:
        """Calculate Key Rate Durations.

        Bumps each key rate tenor individually to measure
        sensitivity to specific parts of the curve.
        """
        krd = {}

        for tenor in self.KRD_TENORS:
            quote = self.curve_builder.get_quote(tenor)
            if quote is None:
                krd[tenor] = 0.0
                continue

            original_value = quote.value()

            try:
                # Bump up
                quote.setValue(original_value + self.bump_size)
                npv_up = self._price_instrument(instrument)

                # Bump down
                quote.setValue(original_value - self.bump_size)
                npv_down = self._price_instrument(instrument)

                # KRD for this tenor
                krd[tenor] = (npv_down - npv_up) / 2

            finally:
                # Restore
                quote.setValue(original_value)

        return krd
