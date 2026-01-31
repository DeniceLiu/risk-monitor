"""Tests for pricing and risk calculations."""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch

# Skip QuantLib tests if not installed
pytest.importorskip("QuantLib")

from app.pricing.curves import YieldCurveBuilder
from app.pricing.instruments import BondData, SwapData, BondPricer, SwapPricer
from app.pricing.risk import RiskCalculator, RiskMetrics


class TestYieldCurveBuilder:
    """Tests for yield curve building."""

    def test_update_rates(self):
        """Test updating rates."""
        builder = YieldCurveBuilder()

        rates = {
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
            "30Y": 0.0450,
        }

        builder.update_rates(rates, "2026-01-28")

        # Check quotes were updated
        assert builder.get_quote("2Y").value() == 0.0420
        assert builder.get_quote("5Y").value() == 0.0410

    def test_curve_built(self):
        """Test that curve is built after update."""
        builder = YieldCurveBuilder()

        rates = {
            "1M": 0.0525,
            "3M": 0.0520,
            "6M": 0.0510,
            "1Y": 0.0480,
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
            "30Y": 0.0450,
        }

        builder.update_rates(rates, "2026-01-28")

        assert builder.curve_handle is not None

    def test_discount_factor(self):
        """Test getting discount factors."""
        builder = YieldCurveBuilder()

        rates = {
            "1M": 0.0525,
            "3M": 0.0520,
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
        }

        builder.update_rates(rates, "2026-01-28")

        # Discount factor should be less than 1 for positive rates
        df_1y = builder.get_discount_factor(1.0)
        assert 0 < df_1y < 1

        # Longer maturities should have lower discount factors
        df_5y = builder.get_discount_factor(5.0)
        assert df_5y < df_1y


class TestBondPricer:
    """Tests for bond pricing."""

    @pytest.fixture
    def curve_builder(self):
        """Create a curve builder with sample rates."""
        builder = YieldCurveBuilder()
        rates = {
            "1M": 0.0525,
            "3M": 0.0520,
            "6M": 0.0510,
            "1Y": 0.0480,
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
            "30Y": 0.0450,
        }
        builder.update_rates(rates, "2026-01-28")
        return builder

    def test_price_bond(self, curve_builder):
        """Test pricing a simple bond."""
        bond = BondData(
            id="test-bond",
            isin="US912810TM25",
            notional=1000000.0,
            coupon_rate=0.0375,
            maturity_date=date(2028, 11, 15),
            issue_date=date(2023, 11, 15),
            payment_frequency="SEMI_ANNUAL",
            day_count_convention="ACT_ACT",
        )

        pricer = BondPricer(curve_builder.curve_handle)
        npv = pricer.price(bond)

        # NPV should be reasonable for a $1M bond
        assert 800000 < npv < 1200000


class TestSwapPricer:
    """Tests for swap pricing."""

    @pytest.fixture
    def curve_builder(self):
        """Create a curve builder with sample rates."""
        builder = YieldCurveBuilder()
        rates = {
            "1M": 0.0525,
            "3M": 0.0520,
            "6M": 0.0510,
            "1Y": 0.0480,
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
            "30Y": 0.0450,
        }
        builder.update_rates(rates, "2026-01-28")
        return builder

    def test_price_swap(self, curve_builder):
        """Test pricing a simple swap."""
        # Use future dates to avoid missing fixing issues
        swap = SwapData(
            id="test-swap",
            notional=10000000.0,
            fixed_rate=0.0410,
            tenor="5Y",
            trade_date=date(2026, 1, 28),
            maturity_date=date(2031, 1, 28),
            effective_date=date(2026, 1, 30),
            pay_receive="PAY",
            float_index="SOFR",
            payment_frequency="QUARTERLY",
        )

        pricer = SwapPricer(curve_builder.curve_handle, curve_builder.curve_handle)
        npv = pricer.price(swap)

        # At-market swap should have NPV close to zero
        # Allow for some deviation based on curve shape
        assert -1000000 < npv < 1000000


class TestRiskCalculator:
    """Tests for risk calculations."""

    @pytest.fixture
    def risk_setup(self):
        """Set up risk calculator with curve and bond."""
        builder = YieldCurveBuilder()
        rates = {
            "1M": 0.0525,
            "3M": 0.0520,
            "6M": 0.0510,
            "1Y": 0.0480,
            "2Y": 0.0420,
            "5Y": 0.0410,
            "10Y": 0.0420,
            "30Y": 0.0450,
        }
        builder.update_rates(rates, "2026-01-28")

        calculator = RiskCalculator(builder)

        bond = BondData(
            id="test-bond",
            isin="US912810TM25",
            notional=1000000.0,
            coupon_rate=0.0375,
            maturity_date=date(2028, 11, 15),
            issue_date=date(2023, 11, 15),
            payment_frequency="SEMI_ANNUAL",
            day_count_convention="ACT_ACT",
        )

        return calculator, bond

    def test_calculate_dv01(self, risk_setup):
        """Test DV01 calculation."""
        calculator, bond = risk_setup

        metrics = calculator.calculate(bond)

        # DV01 should be positive for a long bond position
        assert metrics.dv01 > 0

        # DV01 for a $1M bond should be in reasonable range
        # Roughly $100-500 per bp for a 2-3 year bond
        assert 50 < metrics.dv01 < 1000

    def test_calculate_krd(self, risk_setup):
        """Test KRD calculation."""
        calculator, bond = risk_setup

        metrics = calculator.calculate(bond)

        # Should have KRD for all key tenors
        assert "2Y" in metrics.krd
        assert "5Y" in metrics.krd
        assert "10Y" in metrics.krd
        assert "30Y" in metrics.krd

        # KRD values should be numeric
        for tenor, value in metrics.krd.items():
            assert isinstance(value, float)

        # At least one KRD should be non-zero for a bond
        assert any(abs(v) > 0 for v in metrics.krd.values())

    def test_risk_metrics_structure(self, risk_setup):
        """Test risk metrics structure."""
        calculator, bond = risk_setup

        metrics = calculator.calculate(bond)

        assert isinstance(metrics, RiskMetrics)
        assert metrics.instrument_id == "test-bond"
        assert isinstance(metrics.npv, float)
        assert isinstance(metrics.dv01, float)
        assert isinstance(metrics.krd, dict)
