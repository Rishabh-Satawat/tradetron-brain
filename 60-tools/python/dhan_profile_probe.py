#!/usr/bin/env python3
"""
Dhan Profile Probe — Read-only verification of Dhan account access.

Checks:
- API authentication (access token validity)
- Account profile (client ID, account type)
- Data API subscription status (dataPlan: Active/Inactive)

Hard constraints (from AGENTS.md E5-E8):
- READ ONLY: no order placement, no GTT, no kill switch
- NO SECRET LEAKAGE: never print full access token
- FAIL CLOSED: exit on any auth error

Usage:
    python dhan_profile_probe.py

Environment:
    DHAN_CLIENT_ID      Client ID (e.g., "1111831735")
    DHAN_ACCESS_TOKEN   Live access token (never commit)

Exit codes:
    0 = success (dataPlan Active)
    1 = auth failed
    2 = dataPlan Inactive (subscription required)
    3 = network error
"""

import os
import sys
from dhanhq import dhanhq

def main():
    # Load credentials from environment (never hardcode)
    client_id = os.getenv("DHAN_CLIENT_ID")
    access_token = os.getenv("DHAN_ACCESS_TOKEN")
    
    if not client_id or not access_token:
        print("❌ ERROR: Missing DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN environment variables")
        print("Set them in PowerShell:")
        print('  $env:DHAN_CLIENT_ID = "1111831735"')
        print('  $env:DHAN_ACCESS_TOKEN = "YOUR_TOKEN_HERE"')
        sys.exit(1)
    
    try:
        # Initialize Dhan client
        dhan = dhanhq(client_id, access_token)
        
        # Fetch profile (read-only call)
        print("🔍 Fetching Dhan account profile...")
        profile = dhan.get_profile()
        
        if not profile or "data" not in profile:
            print("❌ ERROR: Invalid profile response")
            sys.exit(1)
        
        data = profile["data"]
        
        # Print key fields (mask sensitive data)
        print(f"\n✅ Account Profile Retrieved:")
        print(f"   Client ID:     {data.get('clientId', 'N/A')}")
        print(f"   Account Type:  {data.get('accountType', 'N/A')}")
        print(f"   Data Plan:     {data.get('dataPlan', 'N/A')}")
        print(f"   Trading Plan:  {data.get('tradingPlan', 'N/A')}")
        
        # Check data plan status
        data_plan = data.get('dataPlan', '').lower()
        if data_plan != 'active':
            print(f"\n⚠️  WARNING: Data API subscription NOT active")
            print(f"   Current status: {data.get('dataPlan', 'Unknown')}")
            print(f"   Subscribe at: https://dhanhq.co/api-documentation")
            print(f"   Cost: ₹499/month (required for option chain & Greeks)")
            sys.exit(2)
        
        print(f"\n✅ SUCCESS: Data API subscription is Active")
        print(f"   Token prefix: {access_token[:8]}... (valid)")
        sys.exit(0)
        
    except Exception as e:
        print(f"❌ ERROR: {type(e).__name__}: {e}")
        sys.exit(3)

if __name__ == "__main__":
    main()
