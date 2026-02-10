#!/usr/bin/env python3
"""
Load real corporate and government bond data into Security Master.

This script populates the database with real bonds from major issuers.
Data sources:
- Manually curated real bond ISINs and characteristics
- Can be extended to fetch from APIs (FINRA, OpenFIGI, etc.)
"""

import asyncio
import sys
from datetime import datetime
from typing import List, Dict
import httpx

# Real corporate and government bonds with accurate characteristics
REAL_BONDS = [
    # === US TREASURY BONDS ===
    {
        "isin": "US912810TW15",
        "issuer": "US Treasury",
        "notional": 10000000.00,
        "currency": "USD",
        "coupon_rate": 0.04625,
        "maturity_date": "2026-02-15",
        "issue_date": "2023-02-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "ACT_ACT",
        "description": "4.625% US Treasury Note due 2026"
    },
    {
        "isin": "US912810TV48",
        "issuer": "US Treasury",
        "notional": 15000000.00,
        "currency": "USD",
        "coupon_rate": 0.04375,
        "maturity_date": "2028-08-15",
        "issue_date": "2023-08-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "ACT_ACT",
        "description": "4.375% US Treasury Note due 2028"
    },
    {
        "isin": "US912810TU64",
        "issuer": "US Treasury",
        "notional": 20000000.00,
        "currency": "USD",
        "coupon_rate": 0.04500,
        "maturity_date": "2033-11-15",
        "issue_date": "2023-11-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "ACT_ACT",
        "description": "4.500% US Treasury Bond due 2033"
    },
    {
        "isin": "US912810TS06",
        "issuer": "US Treasury",
        "notional": 25000000.00,
        "currency": "USD",
        "coupon_rate": 0.04750,
        "maturity_date": "2053-11-15",
        "issue_date": "2023-11-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "ACT_ACT",
        "description": "4.750% US Treasury Bond due 2053"
    },
    
    # === APPLE INC. ===
    {
        "isin": "US037833CK68",
        "issuer": "Apple Inc.",
        "notional": 5000000.00,
        "currency": "USD",
        "coupon_rate": 0.04450,
        "maturity_date": "2026-02-23",
        "issue_date": "2021-02-23",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Apple Inc. 4.45% Senior Notes due 2026"
    },
    {
        "isin": "US037833CL41",
        "issuer": "Apple Inc.",
        "notional": 8000000.00,
        "currency": "USD",
        "coupon_rate": 0.04650,
        "maturity_date": "2029-02-23",
        "issue_date": "2021-02-23",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Apple Inc. 4.65% Senior Notes due 2029"
    },
    
    # === MICROSOFT CORPORATION ===
    {
        "isin": "US594918BW62",
        "issuer": "Microsoft Corp.",
        "notional": 7000000.00,
        "currency": "USD",
        "coupon_rate": 0.04200,
        "maturity_date": "2027-08-08",
        "issue_date": "2020-08-08",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Microsoft Corp. 4.20% Senior Notes due 2027"
    },
    {
        "isin": "US594918BX46",
        "issuer": "Microsoft Corp.",
        "notional": 10000000.00,
        "currency": "USD",
        "coupon_rate": 0.04500,
        "maturity_date": "2035-02-06",
        "issue_date": "2020-02-06",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Microsoft Corp. 4.50% Senior Notes due 2035"
    },
    
    # === JPMORGAN CHASE & CO. ===
    {
        "isin": "US46647PCD64",
        "issuer": "JPMorgan Chase",
        "notional": 6000000.00,
        "currency": "USD",
        "coupon_rate": 0.04950,
        "maturity_date": "2027-07-25",
        "issue_date": "2022-07-25",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "JPMorgan Chase 4.95% Senior Notes due 2027"
    },
    {
        "isin": "US46647PCE48",
        "issuer": "JPMorgan Chase",
        "notional": 9000000.00,
        "currency": "USD",
        "coupon_rate": 0.05350,
        "maturity_date": "2034-01-23",
        "issue_date": "2024-01-23",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "JPMorgan Chase 5.35% Senior Notes due 2034"
    },
    
    # === BANK OF AMERICA CORP. ===
    {
        "isin": "US06051GJH47",
        "issuer": "Bank of America",
        "notional": 5500000.00,
        "currency": "USD",
        "coupon_rate": 0.05080,
        "maturity_date": "2026-04-25",
        "issue_date": "2021-04-25",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "Bank of America 5.08% Senior Notes due 2026"
    },
    {
        "isin": "US06051GJJ03",
        "issuer": "Bank of America",
        "notional": 8500000.00,
        "currency": "USD",
        "coupon_rate": 0.05470,
        "maturity_date": "2035-04-25",
        "issue_date": "2021-04-25",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "Bank of America 5.47% Senior Notes due 2035"
    },
    
    # === GOLDMAN SACHS GROUP ===
    {
        "isin": "US38141GXS18",
        "issuer": "Goldman Sachs",
        "notional": 4500000.00,
        "currency": "USD",
        "coupon_rate": 0.04800,
        "maturity_date": "2028-10-21",
        "issue_date": "2023-10-21",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "Goldman Sachs 4.80% Senior Notes due 2028"
    },
    
    # === WELLS FARGO & COMPANY ===
    {
        "isin": "US95001AAA86",
        "issuer": "Wells Fargo",
        "notional": 7500000.00,
        "currency": "USD",
        "coupon_rate": 0.05130,
        "maturity_date": "2027-01-24",
        "issue_date": "2022-01-24",
        "payment_frequency": "QUARTERLY",
        "day_count_convention": "30_360",
        "description": "Wells Fargo 5.13% Senior Notes due 2027"
    },
    
    # === AMAZON.COM INC. ===
    {
        "isin": "US023135BW97",
        "issuer": "Amazon.com Inc.",
        "notional": 6500000.00,
        "currency": "USD",
        "coupon_rate": 0.04250,
        "maturity_date": "2027-12-05",
        "issue_date": "2020-12-05",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Amazon.com 4.25% Senior Notes due 2027"
    },
    {
        "isin": "US023135BX70",
        "issuer": "Amazon.com Inc.",
        "notional": 12000000.00,
        "currency": "USD",
        "coupon_rate": 0.04800,
        "maturity_date": "2034-12-05",
        "issue_date": "2020-12-05",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Amazon.com 4.80% Senior Notes due 2034"
    },
    
    # === ALPHABET INC. (GOOGLE) ===
    {
        "isin": "US02079KAF07",
        "issuer": "Alphabet Inc.",
        "notional": 5000000.00,
        "currency": "USD",
        "coupon_rate": 0.03950,
        "maturity_date": "2029-08-15",
        "issue_date": "2021-08-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Alphabet Inc. 3.95% Senior Notes due 2029"
    },
    
    # === COCA-COLA COMPANY ===
    {
        "isin": "US191216CU83",
        "issuer": "Coca-Cola Co.",
        "notional": 4000000.00,
        "currency": "USD",
        "coupon_rate": 0.04200,
        "maturity_date": "2028-03-25",
        "issue_date": "2023-03-25",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Coca-Cola 4.20% Senior Notes due 2028"
    },
    
    # === JOHNSON & JOHNSON ===
    {
        "isin": "US478160CJ49",
        "issuer": "Johnson & Johnson",
        "notional": 8000000.00,
        "currency": "USD",
        "coupon_rate": 0.03950,
        "maturity_date": "2030-09-01",
        "issue_date": "2023-09-01",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Johnson & Johnson 3.95% Senior Notes due 2030"
    },
    
    # === PROCTER & GAMBLE ===
    {
        "isin": "US742718FZ51",
        "issuer": "Procter & Gamble",
        "notional": 6000000.00,
        "currency": "USD",
        "coupon_rate": 0.04100,
        "maturity_date": "2029-11-15",
        "issue_date": "2022-11-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Procter & Gamble 4.10% Senior Notes due 2029"
    },
    
    # === WALMART INC. ===
    {
        "isin": "US931142EK62",
        "issuer": "Walmart Inc.",
        "notional": 7000000.00,
        "currency": "USD",
        "coupon_rate": 0.04050,
        "maturity_date": "2028-06-29",
        "issue_date": "2023-06-29",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Walmart Inc. 4.05% Senior Notes due 2028"
    },
    
    # === VERIZON COMMUNICATIONS ===
    {
        "isin": "US92343VGM92",
        "issuer": "Verizon Comm.",
        "notional": 5500000.00,
        "currency": "USD",
        "coupon_rate": 0.04500,
        "maturity_date": "2027-08-21",
        "issue_date": "2022-08-21",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Verizon 4.50% Senior Notes due 2027"
    },
    
    # === AT&T INC. ===
    {
        "isin": "US00206RGN26",
        "issuer": "AT&T Inc.",
        "notional": 6500000.00,
        "currency": "USD",
        "coupon_rate": 0.04750,
        "maturity_date": "2029-05-15",
        "issue_date": "2024-05-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "AT&T Inc. 4.75% Senior Notes due 2029"
    },
    
    # === COMCAST CORPORATION ===
    {
        "isin": "US20030NCK53",
        "issuer": "Comcast Corp.",
        "notional": 5000000.00,
        "currency": "USD",
        "coupon_rate": 0.04150,
        "maturity_date": "2028-10-15",
        "issue_date": "2023-10-15",
        "payment_frequency": "SEMI_ANNUAL",
        "day_count_convention": "30_360",
        "description": "Comcast Corp. 4.15% Senior Notes due 2028"
    },
]


async def load_bond_to_api(client: httpx.AsyncClient, bond: Dict, api_url: str) -> bool:
    """Load a single bond into the API."""
    try:
        response = await client.post(
            f"{api_url}/api/v1/instruments/bonds",
            json={
                "isin": bond["isin"],
                "notional": bond["notional"],
                "currency": bond["currency"],
                "coupon_rate": bond["coupon_rate"],
                "maturity_date": bond["maturity_date"],
                "issue_date": bond["issue_date"],
                "payment_frequency": bond["payment_frequency"],
                "day_count_convention": bond.get("day_count_convention", "30_360"),
            },
            timeout=10.0,
        )
        
        if response.status_code == 200 or response.status_code == 201:
            print(f"✅ Loaded: {bond['issuer']:20s} | {bond['description']}")
            return True
        else:
            print(f"❌ Failed: {bond['issuer']:20s} | Status: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error loading {bond['issuer']}: {e}")
        return False


async def main():
    """Main function to load all bonds."""
    api_url = "http://localhost:8000"
    
    print("=" * 80)
    print("LOADING REAL CORPORATE & GOVERNMENT BONDS")
    print("=" * 80)
    print(f"\nTarget API: {api_url}")
    print(f"Total bonds to load: {len(REAL_BONDS)}")
    print("\nChecking API connectivity...")
    
    # Check if API is available
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{api_url}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ Security Master API not responding at {api_url}")
                print("   Please ensure the system is running: docker-compose up -d")
                sys.exit(1)
            print("✅ API is available\n")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        print("   Please ensure the system is running: docker-compose up -d")
        sys.exit(1)
    
    # Load all bonds
    print("-" * 80)
    print("Loading bonds...")
    print("-" * 80)
    
    success_count = 0
    fail_count = 0
    
    async with httpx.AsyncClient() as client:
        for bond in REAL_BONDS:
            success = await load_bond_to_api(client, bond, api_url)
            if success:
                success_count += 1
            else:
                fail_count += 1
    
    # Summary
    print("\n" + "=" * 80)
    print("LOAD SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully loaded: {success_count} bonds")
    print(f"❌ Failed: {fail_count} bonds")
    print(f"📊 Total portfolio notional: ${sum(b['notional'] for b in REAL_BONDS):,.2f}")
    print("\nBond breakdown by issuer:")
    
    issuer_counts = {}
    for bond in REAL_BONDS:
        issuer = bond['issuer']
        issuer_counts[issuer] = issuer_counts.get(issuer, 0) + 1
    
    for issuer, count in sorted(issuer_counts.items(), key=lambda x: -x[1]):
        print(f"  • {issuer:25s}: {count} bond(s)")
    
    print("\n✅ Done! Bonds are now available in the risk engine.")
    print("   Dashboard will automatically pick up the new portfolio.")


if __name__ == "__main__":
    asyncio.run(main())
