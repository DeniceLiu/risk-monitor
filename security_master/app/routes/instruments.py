"""API routes for instrument CRUD operations."""

from typing import Optional
from uuid import UUID
import math

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Instrument, Bond, InterestRateSwap
from app.schemas import (
    BondCreate,
    BondResponse,
    SwapCreate,
    SwapResponse,
    InstrumentResponse,
    InstrumentListResponse,
)

router = APIRouter(prefix="/api/v1/instruments", tags=["instruments"])


# ============================================
# Helper Functions
# ============================================

def instrument_to_response(instrument: Instrument) -> InstrumentResponse:
    """Convert an Instrument model to a response schema."""
    data = {
        "id": instrument.id,
        "instrument_type": instrument.instrument_type,
        "notional": instrument.notional,
        "currency": instrument.currency,
        "created_at": instrument.created_at,
        "updated_at": instrument.updated_at,
    }

    if instrument.bond:
        data.update({
            "isin": instrument.bond.isin,
            "coupon_rate": instrument.bond.coupon_rate,
            "maturity_date": instrument.bond.maturity_date,
            "issue_date": instrument.bond.issue_date,
            "payment_frequency": instrument.bond.payment_frequency,
            "day_count_convention": instrument.bond.day_count_convention,
        })
    elif instrument.swap:
        data.update({
            "fixed_rate": instrument.swap.fixed_rate,
            "tenor": instrument.swap.tenor,
            "trade_date": instrument.swap.trade_date,
            "maturity_date": instrument.swap.maturity_date,
            "effective_date": instrument.swap.effective_date,
            "pay_receive": instrument.swap.pay_receive,
            "float_index": instrument.swap.float_index,
            "payment_frequency": instrument.swap.payment_frequency,
        })

    return InstrumentResponse(**data)


# ============================================
# Bond Endpoints
# ============================================

@router.post("/bonds", response_model=BondResponse, status_code=status.HTTP_201_CREATED)
def create_bond(bond_data: BondCreate, db: Session = Depends(get_db)) -> BondResponse:
    """Create a new bond instrument."""
    # Check for duplicate ISIN
    existing = db.query(Bond).filter(Bond.isin == bond_data.isin).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Bond with ISIN {bond_data.isin} already exists",
        )

    # Create parent instrument
    instrument = Instrument(
        instrument_type="BOND",
        notional=bond_data.notional,
        currency=bond_data.currency,
    )
    db.add(instrument)
    db.flush()  # Get the instrument ID

    # Create bond details
    bond = Bond(
        instrument_id=instrument.id,
        isin=bond_data.isin,
        coupon_rate=bond_data.coupon_rate,
        maturity_date=bond_data.maturity_date,
        issue_date=bond_data.issue_date,
        payment_frequency=bond_data.payment_frequency.value,
        day_count_convention=bond_data.day_count_convention.value,
    )
    db.add(bond)
    db.commit()
    db.refresh(instrument)

    return BondResponse(
        id=instrument.id,
        isin=bond.isin,
        notional=instrument.notional,
        currency=instrument.currency,
        coupon_rate=bond.coupon_rate,
        maturity_date=bond.maturity_date,
        issue_date=bond.issue_date,
        payment_frequency=bond.payment_frequency,
        day_count_convention=bond.day_count_convention,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


@router.get("/bonds/{bond_id}", response_model=BondResponse)
def get_bond(bond_id: UUID, db: Session = Depends(get_db)) -> BondResponse:
    """Get a bond by ID."""
    instrument = (
        db.query(Instrument)
        .filter(Instrument.id == bond_id, Instrument.instrument_type == "BOND")
        .first()
    )
    if not instrument or not instrument.bond:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Bond {bond_id} not found",
        )

    return BondResponse(
        id=instrument.id,
        isin=instrument.bond.isin,
        notional=instrument.notional,
        currency=instrument.currency,
        coupon_rate=instrument.bond.coupon_rate,
        maturity_date=instrument.bond.maturity_date,
        issue_date=instrument.bond.issue_date,
        payment_frequency=instrument.bond.payment_frequency,
        day_count_convention=instrument.bond.day_count_convention,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


# ============================================
# Swap Endpoints
# ============================================

@router.post("/swaps", response_model=SwapResponse, status_code=status.HTTP_201_CREATED)
def create_swap(swap_data: SwapCreate, db: Session = Depends(get_db)) -> SwapResponse:
    """Create a new interest rate swap."""
    # Create parent instrument
    instrument = Instrument(
        instrument_type="SWAP",
        notional=swap_data.notional,
        currency=swap_data.currency,
    )
    db.add(instrument)
    db.flush()

    # Create swap details
    swap = InterestRateSwap(
        instrument_id=instrument.id,
        fixed_rate=swap_data.fixed_rate,
        tenor=swap_data.tenor,
        trade_date=swap_data.trade_date,
        maturity_date=swap_data.maturity_date,
        effective_date=swap_data.effective_date,
        pay_receive=swap_data.pay_receive.value,
        float_index=swap_data.float_index.value,
        payment_frequency=swap_data.payment_frequency.value,
    )
    db.add(swap)
    db.commit()
    db.refresh(instrument)

    return SwapResponse(
        id=instrument.id,
        notional=instrument.notional,
        currency=instrument.currency,
        fixed_rate=swap.fixed_rate,
        tenor=swap.tenor,
        trade_date=swap.trade_date,
        maturity_date=swap.maturity_date,
        effective_date=swap.effective_date,
        pay_receive=swap.pay_receive,
        float_index=swap.float_index,
        payment_frequency=swap.payment_frequency,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


@router.get("/swaps/{swap_id}", response_model=SwapResponse)
def get_swap(swap_id: UUID, db: Session = Depends(get_db)) -> SwapResponse:
    """Get a swap by ID."""
    instrument = (
        db.query(Instrument)
        .filter(Instrument.id == swap_id, Instrument.instrument_type == "SWAP")
        .first()
    )
    if not instrument or not instrument.swap:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Swap {swap_id} not found",
        )

    return SwapResponse(
        id=instrument.id,
        notional=instrument.notional,
        currency=instrument.currency,
        fixed_rate=instrument.swap.fixed_rate,
        tenor=instrument.swap.tenor,
        trade_date=instrument.swap.trade_date,
        maturity_date=instrument.swap.maturity_date,
        effective_date=instrument.swap.effective_date,
        pay_receive=instrument.swap.pay_receive,
        float_index=instrument.swap.float_index,
        payment_frequency=instrument.swap.payment_frequency,
        created_at=instrument.created_at,
        updated_at=instrument.updated_at,
    )


# ============================================
# Generic Instrument Endpoints
# ============================================

@router.get("", response_model=InstrumentListResponse)
def list_instruments(
    page: int = Query(default=1, ge=1, description="Page number"),
    page_size: int = Query(default=50, ge=1, le=100, description="Items per page"),
    instrument_type: Optional[str] = Query(default=None, description="Filter by type (BOND/SWAP)"),
    db: Session = Depends(get_db),
) -> InstrumentListResponse:
    """List all instruments with pagination."""
    query = db.query(Instrument)

    if instrument_type:
        instrument_type = instrument_type.upper()
        if instrument_type not in ("BOND", "SWAP"):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="instrument_type must be BOND or SWAP",
            )
        query = query.filter(Instrument.instrument_type == instrument_type)

    total = query.count()
    pages = math.ceil(total / page_size) if total > 0 else 1

    instruments = (
        query
        .order_by(Instrument.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return InstrumentListResponse(
        items=[instrument_to_response(i) for i in instruments],
        total=total,
        page=page,
        page_size=page_size,
        pages=pages,
    )


@router.get("/{instrument_id}", response_model=InstrumentResponse)
def get_instrument(instrument_id: UUID, db: Session = Depends(get_db)) -> InstrumentResponse:
    """Get any instrument by ID."""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument {instrument_id} not found",
        )
    return instrument_to_response(instrument)


@router.delete("/{instrument_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_instrument(instrument_id: UUID, db: Session = Depends(get_db)) -> None:
    """Delete an instrument by ID."""
    instrument = db.query(Instrument).filter(Instrument.id == instrument_id).first()
    if not instrument:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Instrument {instrument_id} not found",
        )

    db.delete(instrument)
    db.commit()
