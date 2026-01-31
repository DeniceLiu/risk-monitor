"""SQLAlchemy models for financial instruments."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Column,
    String,
    Numeric,
    Date,
    DateTime,
    ForeignKey,
    CheckConstraint,
    TypeDecorator,
    CHAR,
)
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class GUID(TypeDecorator):
    """Platform-independent GUID type.

    Uses PostgreSQL's UUID type, otherwise uses CHAR(36), storing as string.
    """

    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == "postgresql":
            return dialect.type_descriptor(PG_UUID(as_uuid=True))
        else:
            return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        elif dialect.name == "postgresql":
            return value
        else:
            return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        elif isinstance(value, uuid.UUID):
            return value
        else:
            return uuid.UUID(value)


class Instrument(Base):
    """Base instrument model."""

    __tablename__ = "instruments"

    id = Column(GUID(), primary_key=True, default=uuid.uuid4)
    instrument_type = Column(String(10), nullable=False)
    notional = Column(Numeric(18, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    bond = relationship("Bond", back_populates="instrument", uselist=False, cascade="all, delete-orphan")
    swap = relationship("InterestRateSwap", back_populates="instrument", uselist=False, cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("instrument_type IN ('BOND', 'SWAP')", name="valid_instrument_type"),
    )


class Bond(Base):
    """Bond instrument details."""

    __tablename__ = "bonds"

    instrument_id = Column(
        GUID(),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    isin = Column(String(12), unique=True, nullable=False)
    coupon_rate = Column(Numeric(8, 6), nullable=False)
    maturity_date = Column(Date, nullable=False)
    issue_date = Column(Date, nullable=True)
    payment_frequency = Column(String(20), nullable=False, default="SEMI_ANNUAL")
    day_count_convention = Column(String(20), nullable=False, default="ACT_ACT")

    # Relationship
    instrument = relationship("Instrument", back_populates="bond")

    __table_args__ = (
        CheckConstraint("coupon_rate >= 0 AND coupon_rate <= 1", name="valid_coupon"),
    )


class InterestRateSwap(Base):
    """Interest rate swap instrument details."""

    __tablename__ = "interest_rate_swaps"

    instrument_id = Column(
        GUID(),
        ForeignKey("instruments.id", ondelete="CASCADE"),
        primary_key=True,
    )
    fixed_rate = Column(Numeric(8, 6), nullable=False)
    tenor = Column(String(10), nullable=False)
    trade_date = Column(Date, nullable=False)
    maturity_date = Column(Date, nullable=False)
    effective_date = Column(Date, nullable=True)
    pay_receive = Column(String(10), nullable=False)
    float_index = Column(String(20), nullable=False, default="SOFR")
    payment_frequency = Column(String(20), nullable=False, default="QUARTERLY")

    # Relationship
    instrument = relationship("Instrument", back_populates="swap")

    __table_args__ = (
        CheckConstraint("pay_receive IN ('PAY', 'RECEIVE')", name="valid_pay_receive"),
        CheckConstraint("fixed_rate >= 0 AND fixed_rate <= 1", name="valid_swap_rate"),
    )
