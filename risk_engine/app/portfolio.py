"""Portfolio loading from Security Master."""

import logging
from datetime import datetime
from typing import List, Union

import httpx

from app.pricing.instruments import BondData, SwapData

logger = logging.getLogger(__name__)


def parse_date(date_str: str) -> datetime:
    """Parse date string to datetime."""
    if not date_str:
        return None
    return datetime.strptime(date_str, "%Y-%m-%d").date()


def load_portfolio(security_master_url: str) -> List[Union[BondData, SwapData]]:
    """Load portfolio from Security Master API.

    Args:
        security_master_url: Base URL of Security Master service

    Returns:
        List of BondData and SwapData objects
    """
    instruments = []

    try:
        with httpx.Client(timeout=30.0) as client:
            # Fetch all instruments
            response = client.get(f"{security_master_url}/api/v1/instruments?page_size=100")
            response.raise_for_status()

            data = response.json()
            logger.info(f"Loaded {data['total']} instruments from Security Master")

            for item in data["items"]:
                try:
                    if item["instrument_type"] == "BOND":
                        bond = BondData(
                            id=item["id"],
                            isin=item["isin"],
                            notional=float(item["notional"]),
                            coupon_rate=float(item["coupon_rate"]),
                            maturity_date=parse_date(item["maturity_date"]),
                            issue_date=parse_date(item.get("issue_date")),
                            payment_frequency=item.get("payment_frequency", "SEMI_ANNUAL"),
                            day_count_convention=item.get("day_count_convention", "ACT_ACT"),
                        )
                        instruments.append(bond)

                    elif item["instrument_type"] == "SWAP":
                        swap = SwapData(
                            id=item["id"],
                            notional=float(item["notional"]),
                            fixed_rate=float(item["fixed_rate"]),
                            tenor=item["tenor"],
                            trade_date=parse_date(item["trade_date"]),
                            maturity_date=parse_date(item["maturity_date"]),
                            effective_date=parse_date(item.get("effective_date")),
                            pay_receive=item["pay_receive"],
                            float_index=item.get("float_index", "SOFR"),
                            payment_frequency=item.get("payment_frequency", "QUARTERLY"),
                        )
                        instruments.append(swap)

                except Exception as e:
                    logger.error(f"Failed to parse instrument {item.get('id')}: {e}")
                    continue

    except httpx.HTTPError as e:
        logger.error(f"Failed to load portfolio from Security Master: {e}")
        raise

    logger.info(f"Loaded {len(instruments)} instruments ({sum(1 for i in instruments if isinstance(i, BondData))} bonds, {sum(1 for i in instruments if isinstance(i, SwapData))} swaps)")
    return instruments
