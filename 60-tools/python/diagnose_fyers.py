# =============================================================================
# File: 60-tools/python/diagnose_fyers.py
# Description: 5-Second Diagnostic to Resolve Fyers Token Authorization
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

load_dotenv(SECRETS_PATH)
env_app_id = os.getenv("FYERS_APP_ID", "").strip()

if not os.path.exists(TOKEN_PATH):
  print(f"❌ Error: {TOKEN_PATH} not found.")
  exit(1)

with open(TOKEN_PATH) as f:
  token = f.read().strip()

print("=" * 70)
print(f"🔍 FYERS TOKEN DIAGNOSTIC PROBE")
print("=" * 70)
print(f"🔑 Token Length : {len(token)} chars")
print(f"🔑 Token Preview: {token[:12]}...{token[-10:]}")
print(f"📁 From Env ID  : '{env_app_id}'")
print("=" * 70)

# We test the 2 potential ID formats
candidate_ids = list(
    dict.fromkeys([env_app_id, "UFCAZKDNZB-100", "FAK62006-100"])
)

working_id = None
for cid in candidate_ids:
  if not cid:
    continue
  print(f"\n▶️ Testing with Client ID: '{cid}'...")
  fyers = fyersModel.FyersModel(
      client_id=cid, is_async=False, token=token, log_path=""
  )

  prof = fyers.get_profile()
  prof_status = prof.get("s")
  prof_msg = prof.get("message", "OK")
  print(f"   • Profile Endpoint: {prof_status} ({prof_msg})")

  chain = fyers.optionchain(
      data={"symbol": "NSE:NIFTY50-INDEX", "strikecount": 2, "timestamp": ""}
  )
  chain_status = chain.get("s")
  chain_msg = chain.get("message", "OK")
  print(f"   • Option Chain    : {chain_status} ({chain_msg})")

  if chain_status == "ok":
    working_id = cid
    spot = chain.get("data", {}).get("spotPrice", 0)
    print(f"   🎉 SUCCESS! Connected to Live NIFTY Spot: ₹{spot:,.2f}")
    break

print("\n" + "=" * 70)
if working_id:
  print(f"✅ WORKING CLIENT ID CONFIRMED: {working_id}")
  print(f"👉 Ensure FYERS_APP_ID={working_id} in C:\\kite-agent\\secrets\\fyers.env")
else:
  print("❌ Neither ID authenticated on the data API.")
  print("👉 Please check if 'Data' permission is enabled on myapi.fyers.in")
print("=" * 70)