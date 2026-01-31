"""Pydantic schemas for instrument validation."""

from datetime import date, datetime
from decimal import Decimal
from enum import Enum
from typing import Optional, List
from uuid import UUID

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class PayReceive(str, Enum):
    """Swap direction."""
    PAY = "PAY"
    RECEIVE = "RECEIVE"


class PaymentFrequency(str, Enum):
    """Payment frequency options."""
    ANNUAL = "ANNUAL"
    SEMI_ANNUAL = "SEMI_ANNUAL"
    QUARTERLY = "QUARTERLY"
    MONTHLY = "MONTHLY"


class DayCountConvention(str, Enum):
    """Day count convention options."""
    ACT_ACT = "ACT_ACT"
    ACT_360 = "ACT_360"
    ACT_365 = "ACT_365"
    THIRTY_360 = "30_360"


class FloatIndex(str, Enum):
    """Floating rate index options."""
    SOFR = "SOFR"
    LIBOR = "LIBOR"
    EURIBOR = "EURIBOR"


# ============================================
# Bond Schemas
# ============================================

class BondCreate(BaseModel):
    """Schema for creating a bond."""

    isin: str = Field(..., min_length=12, max_length=12, description="12-character ISIN")
    notional: Decimal = Field(..., gt=0, description="Face value of the bond")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    coupon_rate: Decimal = Field(..., ge=0, le=1, description="Coupon rate as decimal (e.g., 0.0375)")
    maturity_date: date = Field(..., description="Bond maturity date")
    issue_date: Optional[date] = Field(default=None, description="Bond issue date")
    payment_frequency: PaymentFrequency = Field(default=PaymentFrequency.SEMI_ANNUAL)
    day_count_convention: DayCountConvention = Field(default=DayCountConvention.ACT_ACT)

    @field_validator("isin")
    @classmethod
    def validate_isin(cls, v: str) -> str:
        """Validate ISIN format."""
        if not v.isalnum():
            raise ValueError("ISIN must be alphanumeric")
        return v.upper()

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate date relationships."""
        if self.issue_date and self.maturity_date <= self.issue_date:
            raise ValueError("Maturity date must be after issue date")
        return self


class BondResponse(BaseModel):
    """Schema for bond response."""

    id: UUID
    instrument_type: str = "BOND"
    isin: str
    notional: Decimal
    currency: str
    coupon_rate: Decimal
    maturity_date: date
    issue_date: Optional[date]
    payment_frequency: str
    day_count_convention: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Swap Schemas
# ============================================

class SwapCreate(BaseModel):
    """Schema for creating an interest rate swap."""

    notional: Decimal = Field(..., gt=0, description="Notional amount")
    currency: str = Field(default="USD", min_length=3, max_length=3)
    fixed_rate: Decimal = Field(..., ge=0, le=1, description="Fixed rate as decimal")
    tenor: str = Field(..., pattern=r"^\d+[YM]$", description="Tenor (e.g., '5Y', '18M')")
    trade_date: date = Field(..., description="Trade date")
    maturity_date: date = Field(..., description="Maturity date")
    effective_date: Optional[date] = Field(default=None, description="Effective date")
    pay_receive: PayReceive = Field(..., description="PAY or RECEIVE fixed")
    float_index: FloatIndex = Field(default=FloatIndex.SOFR)
    payment_frequency: PaymentFrequency = Field(default=PaymentFrequency.QUARTERLY)

    @model_validator(mode="after")
    def validate_dates(self):
        """Validate date relationships."""
        if self.maturity_date <= self.trade_date:
            raise ValueError("Maturity date must be after trade date")
        if self.effective_date and self.effective_date < self.trade_date:
            raise ValueError("Effective date cannot be before trade date")
        return self


class SwapResponse(BaseModel):
    """Schema for swap response."""

    id: UUID
    instrument_type: str = "SWAP"
    notional: Decimal
    currency: str
    fixed_rate: Decimal
    tenor: str
    trade_date: date
    maturity_date: date
    effective_date: Optional[date]
    pay_receive: str
    float_index: str
    payment_frequency: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Generic Instrument Schemas
# ============================================

class InstrumentResponse(BaseModel):
    """Generic instrument response (union of bond/swap)."""

    id: UUID
    instrument_type: str
    notional: Decimal
    currency: str
    created_at: datetime
    updated_at: datetime

    # Bond-specific (optional)
    isin: Optional[str] = None
    coupon_rate: Optional[Decimal] = None
    maturity_date: Optional[date] = None
    issue_date: Optional[date] = None
    payment_frequency: Optional[str] = None
    day_count_convention: Optional[str] = None

    # Swap-specific (optional)
    fixed_rate: Optional[Decimal] = None
    tenor: Optional[str] = None
    trade_date: Optional[date] = None
    effective_date: Optional[date] = None
    pay_receive: Optional[str] = None
    float_index: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InstrumentListResponse(BaseModel):
    """Paginated list of instruments."""

    items: List[InstrumentResponse]
    total: int
    page: int
    page_size: int
    pages: int
