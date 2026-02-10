"""API routes for portfolio operations."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel

from app.db import get_db
from app.models import Instrument


router = APIRouter(prefix="/api/v1/portfolios", tags=["portfolios"])


class PortfolioResponse(BaseModel):
    """Portfolio summary response."""
    id: str
    name: str
    description: str
    strategy_type: str
    bond_count: int
    total_notional: float

    class Config:
        from_attributes = True


class PortfolioDetailResponse(PortfolioResponse):
    """Detailed portfolio response with additional metrics."""
    avg_coupon: Optional[float] = None
    instruments: List[int] = []


# Portfolio name mapping
PORTFOLIO_NAMES = {
    "CREDIT_IG": ("Investment Grade Credit", "High-quality corporate bonds, BBB- and above", "CREDIT"),
    "CREDIT_HY": ("High Yield Credit", "Below investment grade corporate bonds", "CREDIT"),
    "GOVT_US": ("US Government", "US Treasury notes and bonds", "GOVERNMENT"),
    "TECH_SECTOR": ("Technology Sector", "Concentrated tech company debt", "SECTOR"),
    "FINANCIAL_SECTOR": ("Financial Institutions", "Bank and insurance company bonds", "SECTOR"),
    "CONSUMER_DISCRETIONARY": ("Consumer Discretionary", "Retail, automotive, leisure", "SECTOR"),
    "HEALTHCARE_PHARMA": ("Healthcare & Pharma", "Healthcare providers and pharmaceutical companies", "SECTOR"),
    "ENERGY_UTILITIES": ("Energy & Utilities", "Power generation, oil & gas", "SECTOR"),
    "TELECOM_MEDIA": ("Telecom & Media", "Telecommunications and media companies", "SECTOR"),
    "EMERGING_MARKETS": ("Emerging Markets Corporate", "EM corporate bonds (USD denominated)", "EMERGING_MARKETS"),
}


@router.get("", response_model=List[PortfolioResponse])
def list_portfolios(db: Session = Depends(get_db)) -> List[PortfolioResponse]:
    """
    List all portfolios with summary statistics.

    Returns aggregated data for each portfolio_id found in instruments.
    """
    # Query to get portfolio stats
    portfolio_stats = (
        db.query(
            Instrument.portfolio_id,
            func.count(Instrument.id).label("bond_count"),
            func.sum(Instrument.notional).label("total_notional"),
        )
        .filter(Instrument.portfolio_id.isnot(None))
        .filter(Instrument.portfolio_id != "")
        .group_by(Instrument.portfolio_id)
        .all()
    )

    portfolios = []
    for stat in portfolio_stats:
        portfolio_id = stat.portfolio_id
        name_info = PORTFOLIO_NAMES.get(
            portfolio_id,
            (portfolio_id.replace("_", " ").title(), "", "UNKNOWN")
        )

        portfolios.append(PortfolioResponse(
            id=portfolio_id,
            name=name_info[0],
            description=name_info[1],
            strategy_type=name_info[2],
            bond_count=stat.bond_count or 0,
            total_notional=float(stat.total_notional or 0),
        ))

    # Sort by bond count descending
    portfolios.sort(key=lambda p: p.bond_count, reverse=True)

    return portfolios


@router.get("/{portfolio_id}", response_model=PortfolioDetailResponse)
def get_portfolio(portfolio_id: str, db: Session = Depends(get_db)) -> PortfolioDetailResponse:
    """
    Get detailed information for a specific portfolio.
    """
    # Get instruments in this portfolio
    instruments = (
        db.query(Instrument)
        .filter(Instrument.portfolio_id == portfolio_id)
        .all()
    )

    if not instruments:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")

    # Calculate statistics
    total_notional = sum(float(i.notional) for i in instruments)
    bond_count = len(instruments)
    instrument_ids = [i.id for i in instruments]

    # Calculate average coupon (for bonds only)
    coupons = []
    for inst in instruments:
        if inst.bond and inst.bond.coupon_rate:
            coupons.append(float(inst.bond.coupon_rate))
    avg_coupon = sum(coupons) / len(coupons) if coupons else None

    # Get name info
    name_info = PORTFOLIO_NAMES.get(
        portfolio_id,
        (portfolio_id.replace("_", " ").title(), "", "UNKNOWN")
    )

    return PortfolioDetailResponse(
        id=portfolio_id,
        name=name_info[0],
        description=name_info[1],
        strategy_type=name_info[2],
        bond_count=bond_count,
        total_notional=total_notional,
        avg_coupon=avg_coupon,
        instruments=instrument_ids,
    )


@router.get("/{portfolio_id}/summary")
def get_portfolio_summary(portfolio_id: str, db: Session = Depends(get_db)):
    """
    Get summary statistics for a portfolio.
    """
    from sqlalchemy import func as sqlfunc
    from app.models import Bond

    # Get basic stats
    stats = (
        db.query(
            sqlfunc.count(Instrument.id).label("count"),
            sqlfunc.sum(Instrument.notional).label("total_notional"),
        )
        .filter(Instrument.portfolio_id == portfolio_id)
        .first()
    )

    if not stats or not stats.count:
        raise HTTPException(status_code=404, detail=f"Portfolio '{portfolio_id}' not found")

    # Get average coupon
    avg_coupon = (
        db.query(sqlfunc.avg(Bond.coupon_rate))
        .join(Instrument)
        .filter(Instrument.portfolio_id == portfolio_id)
        .scalar()
    )

    name_info = PORTFOLIO_NAMES.get(
        portfolio_id,
        (portfolio_id.replace("_", " ").title(), "", "UNKNOWN")
    )

    return {
        "portfolio_id": portfolio_id,
        "name": name_info[0],
        "description": name_info[1],
        "strategy_type": name_info[2],
        "bond_count": stats.count,
        "total_notional": float(stats.total_notional or 0),
        "avg_coupon": float(avg_coupon) if avg_coupon else None,
    }
