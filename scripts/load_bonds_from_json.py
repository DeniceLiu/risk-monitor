#!/usr/bin/env python3
"""
Load bonds from generated JSON file into Security Master API.

Usage:
    python scripts/load_bonds_from_json.py --input data/bonds_database.json --batch-size 50
"""

import asyncio
import argparse
import json
from pathlib import Path
from typing import Dict, List
import httpx
from tqdm import tqdm


async def load_bond_batch(client: httpx.AsyncClient, bonds: List[Dict], api_url: str) -> tuple:
    """Load a batch of bonds concurrently."""
    tasks = []
    
    for bond in bonds:
        payload = {
            "isin": bond["isin"],
            "notional": bond["notional"],
            "currency": "USD",
            "coupon_rate": bond["coupon_rate"],
            "maturity_date": bond["maturity_date"],
            "issue_date": bond["issue_date"],
            "payment_frequency": bond["payment_frequency"],
            "day_count_convention": bond.get("day_count_convention", "30_360"),
        }
        # Add portfolio_id if present
        if "portfolio_id" in bond:
            payload["portfolio_id"] = bond["portfolio_id"]

        task = client.post(
            f"{api_url}/api/v1/instruments/bonds",
            json=payload,
            timeout=30.0,
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    success = sum(1 for r in results if not isinstance(r, Exception) and r.status_code in [200, 201])
    failed = len(results) - success
    
    return success, failed


async def main():
    """Load bonds from JSON into API."""
    parser = argparse.ArgumentParser(description="Load bonds from JSON")
    parser.add_argument("--input", type=str, default="data/bonds_database.json", help="Input JSON file")
    parser.add_argument("--api-url", type=str, default="http://localhost:8000", help="Security Master API URL")
    parser.add_argument("--batch-size", type=int, default=50, help="Batch size for concurrent requests")
    parser.add_argument("--portfolio", type=str, default=None, help="Load only specific portfolio ID")
    args = parser.parse_args()
    
    print("=" * 80)
    print("LOADING BONDS INTO SECURITY MASTER")
    print("=" * 80)
    
    # Load JSON
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"❌ File not found: {input_path}")
        print("   Run fetch_finra_bonds.py first to generate the bond database")
        return
    
    with open(input_path, 'r') as f:
        data = json.load(f)
    
    print(f"\n📁 Loaded: {input_path}")
    print(f"📊 Generated: {data['generated_at']}")
    print(f"📈 Total bonds in file: {data['statistics']['total_bonds']:,}")
    
    # Check API connectivity
    print(f"\n🔗 Checking API at {args.api_url}...")
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{args.api_url}/health", timeout=5.0)
            if response.status_code != 200:
                print(f"❌ API not responding")
                return
        print("✅ API is available")
    except Exception as e:
        print(f"❌ Cannot connect to API: {e}")
        return
    
    # Collect bonds to load
    bonds_to_load = []
    if args.portfolio:
        # Load specific portfolio
        if args.portfolio in data['bonds']:
            bonds_to_load = data['bonds'][args.portfolio]
            portfolio_name = next(p['name'] for p in data['portfolios'] if p['id'] == args.portfolio)
            print(f"\n📂 Loading portfolio: {portfolio_name} ({len(bonds_to_load)} bonds)")
        else:
            print(f"❌ Portfolio '{args.portfolio}' not found")
            return
    else:
        # Load all portfolios
        for portfolio_id, bonds in data['bonds'].items():
            bonds_to_load.extend(bonds)
        print(f"\n📂 Loading all portfolios ({len(bonds_to_load)} bonds)")
    
    # Load in batches
    print(f"\n⚙️  Loading in batches of {args.batch_size}...")
    
    total_success = 0
    total_failed = 0
    
    async with httpx.AsyncClient() as client:
        # Process in batches
        batches = [bonds_to_load[i:i+args.batch_size] for i in range(0, len(bonds_to_load), args.batch_size)]
        
        with tqdm(total=len(bonds_to_load), desc="Loading bonds", unit="bonds") as pbar:
            for batch in batches:
                success, failed = await load_bond_batch(client, batch, args.api_url)
                total_success += success
                total_failed += failed
                pbar.update(len(batch))
    
    # Summary
    print(f"\n{'=' * 80}")
    print("LOAD SUMMARY")
    print("=" * 80)
    print(f"✅ Successfully loaded: {total_success:,} bonds")
    print(f"❌ Failed: {total_failed:,} bonds")
    print(f"📊 Success rate: {(total_success/(total_success+total_failed)*100):.1f}%")
    
    if args.portfolio:
        print(f"\n📂 Portfolio: {portfolio_name}")
    else:
        print(f"\n📂 Portfolio breakdown:")
        for portfolio in data['portfolios']:
            portfolio_bonds = data['bonds'][portfolio['id']]
            notional = sum(b['notional'] for b in portfolio_bonds)
            print(f"  • {portfolio['name']:35s}: {len(portfolio_bonds):4d} bonds, ${notional/1e6:,.0f}M")
    
    print(f"\n✅ Done! Bonds are now in the database.")
    print(f"   Restart risk workers to pick up new portfolio:")
    print(f"   docker-compose restart risk_worker")


if __name__ == "__main__":
    asyncio.run(main())
