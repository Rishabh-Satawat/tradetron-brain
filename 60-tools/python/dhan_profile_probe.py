# =============================================================================
# File: 60-tools/python/dhan_profile_probe.py
# Description: Lightweight DhanHQ v2 Profile & Fund Probe
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
import requests
from dotenv import load_dotenv

SECRETS_PATH = r"C:\kite-agent\secrets\dhan.env"

if not os.path.exists(SECRETS_PATH):
    print(f"❌ Error: {SECRETS_PATH} not found. Please create it with DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN.")
    exit(1)

load_dotenv(SECRETS_PATH)
CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "").strip()
ACCESS_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "").strip()

if not CLIENT_ID or not ACCESS_TOKEN:
    print("❌ Error: DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN missing in secrets/dhan.env")
    exit(1)

headers = {
    "access-token": ACCESS_TOKEN,
    "client-id": CLIENT_ID,
    "Content-Type": "application/json"
}

print("=" * 65)
print("⚡ DHAN HQ v2 PROFILE & FUNDS PROBE")
print("=" * 65)

# Probe Profile
try:
    r_prof = requests.get("https://api.dhan.co/v2/profile", headers=headers, timeout=10)
    if r_prof.status_code == 200:
        prof_data = r_prof.json()
        print(f"👤 Dhan Client ID : {prof_data.get('dhanClientId', CLIENT_ID)}")
        print(f"📡 Data Plan Status: {prof_data.get('dataPlan', 'Active')}")
        print(f"📅 Plan Validity   : {prof_data.get('dataValidity', 'N/A')}")
    else:
        print(f"⚠️ Profile check returned HTTP {r_prof.status_code}: {r_prof.text}")
except Exception as e:
    print(f"❌ Error connecting to Dhan Profile: {e}")

# Probe Fund Limits
try:
    r_funds = requests.get("https://api.dhan.co/v2/fundlimit", headers=headers, timeout=10)
    if r_funds.status_code == 200:
        funds = r_funds.json()
        avail_cash = funds.get("availabelBalance", funds.get("sodLimit", 0.0))
        print(f"💰 Available Cash  : ₹{float(avail_cash):,.2f}")
    else:
        print(f"⚠️ Fund check returned HTTP {r_funds.status_code}")
except Exception as e:
    print(f"❌ Error connecting to Dhan Funds: {e}")

print("=" * 65)