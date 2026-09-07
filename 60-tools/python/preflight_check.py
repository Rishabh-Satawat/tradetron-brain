# =============================================================================
# File: 60-tools/python/preflight_check.py
# Description: Fail-Closed Pre-Flight Health Check (Redacted Logs & Error Codes)
# Status: RELEASE 0 CONTAINMENT PATCH (P0 Security & Governance)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import subprocess
import sys
from dotenv import load_dotenv

print("=" * 70)
print("⚡ QUANT DESK — FAIL-CLOSED PRE-FLIGHT AUDIT")
print("=" * 70)

all_systems_healthy = True

# --- 1. DHAN HQ v2 ---
print("\n[1/4] Auditing DhanHQ v2 Status...")
dhan_env = r"C:\kite-agent\secrets\dhan.env"
load_dotenv(dhan_env)
cid = os.getenv("DHAN_CLIENT_ID", "").strip()
tok = os.getenv("DHAN_ACCESS_TOKEN", "").strip()

dhan_ok = False
if cid and tok:
  try:
    import requests

    r = requests.get(
        "https://api.dhan.co/v2/profile",
        headers={"access-token": tok, "client-id": cid},
        timeout=5,
    )
    if r.status_code == 200:
      print("   ✅ DhanHQ v2: HEALTHY (Session Active)")
      dhan_ok = True
  except Exception:
    pass

if not dhan_ok:
  print("   ⚠️ DhanHQ session expired. Invoking auto-login...")
  res = subprocess.run(
      [
          sys.executable,
          r"C:\kite-agent\brain\60-tools\python\dhan_auto_login.py",
      ],
      capture_output=True,
      text=True,
  )
  if res.returncode == 0:
    print("   ✅ DhanHQ v2: RE-AUTHENTICATED & HEALTHY")
  else:
    print("   ❌ DhanHQ v2: AUTHENTICATION FAILED [BLOCKED]")
    all_systems_healthy = False


# --- 2. FYERS PRIME v3 ---
print("\n[2/4] Auditing Fyers Prime v3 Status...")
fyers_env = r"C:\kite-agent\secrets\fyers.env"
fyers_tok = r"C:\kite-agent\secrets\fyers_access_token.txt"
load_dotenv(fyers_env)
app_id = os.getenv("FYERS_APP_ID", "").strip()

fyers_ok = False
if os.path.exists(fyers_tok) and app_id:
  try:
    from fyers_apiv3 import fyersModel

    with open(fyers_tok) as f:
      t = f.read().strip()
    fyers = fyersModel.FyersModel(
        client_id=app_id, is_async=False, token=t, log_path=""
    )
    if fyers.get_profile().get("s") == "ok":
      print("   ✅ Fyers Prime: HEALTHY (Session Active)")
      fyers_ok = True
  except Exception:
    pass

if not fyers_ok:
  print("   ❌ Fyers Prime: SESSION EXPIRED [BLOCKED]")
  all_systems_healthy = False


# --- 3. ZERODHA KITE CONNECT ---
print("\n[3/4] Auditing Zerodha Kite Connect Status...")
kite_env = r"C:\kite-agent\.env"
kite_tok = r"C:\kite-agent\access_token.txt"
load_dotenv(kite_env)
api_key = os.getenv("KITE_API_KEY", "").strip()

kite_ok = False
if os.path.exists(kite_tok) and api_key:
  try:
    from kiteconnect import KiteConnect

    with open(kite_tok) as f:
      kt = f.read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(kt)
    if kite.profile().get("user_id"):
      print("   ✅ Zerodha Kite: HEALTHY (Session Active)")
      kite_ok = True
  except Exception:
    pass

if not kite_ok:
  print("   ❌ Zerodha Kite: SESSION EXPIRED [BLOCKED]")
  all_systems_healthy = False


# --- 4. SUPABASE PRO CLOUD DATABASE ---
print("\n[4/4] Auditing Supabase Pro Cloud Status...")
supa_env = r"C:\kite-agent\secrets\supabase.env"
load_dotenv(supa_env)
url = os.getenv("SUPABASE_URL", "").strip()
key = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
).strip()

supa_ok = False
if url and key:
  try:
    from supabase import create_client

    supa = create_client(url, key)
    supa.table("market_instruments").select("symbol").limit(1).execute()
    print("   ✅ Supabase Cloud: HEALTHY (Database Connected)")
    supa_ok = True
  except Exception:
    pass

if not supa_ok:
  print("   ❌ Supabase Cloud: CONNECTION FAILED [BLOCKED]")
  all_systems_healthy = False

print("\n" + "=" * 70)
if all_systems_healthy:
  print("🎉 DESK VERDICT: ALL SYSTEMS HEALTHY — PROCEED TO SESSION")
  print("=" * 70)
  sys.exit(0)
else:
  print("🚨 DESK VERDICT: PRE-FLIGHT FAILED — EXECUTION HALTED")
  print("=" * 70)
  sys.exit(1)  # Strictly FAIL-CLOSED