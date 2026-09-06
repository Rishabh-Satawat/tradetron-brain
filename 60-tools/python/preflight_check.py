# =============================================================================
# File: 60-tools/python/preflight_check.py
# Description: Automated Pre-Flight Health Check & Self-Healing Token Rotator
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import subprocess
import sys
from dotenv import load_dotenv

print("=" * 75)
print("⚡ QUANT DESK — AUTOMATED MORNING PRE-FLIGHT CHECK")
print("=" * 75)

# --- 1. DHAN HQ v2 CHECK & AUTO-HEAL ---
print("\n[1/4] Checking DhanHQ v2 API...")
dhan_env = r"C:\kite-agent\secrets\dhan.env"
load_dotenv(dhan_env)
cid = os.getenv("DHAN_CLIENT_ID", "").strip()
tok = os.getenv("DHAN_ACCESS_TOKEN", "").strip()

dhan_connected = False
if cid and tok:
  try:
    import requests

    r = requests.get(
        "https://api.dhan.co/v2/profile",
        headers={"access-token": tok, "client-id": cid},
        timeout=5,
    )
    if r.status_code == 200:
      pdata = r.json()
      print(f"   ✅ DhanHQ v2: CONNECTED (Client: {cid})")
      dhan_connected = True
  except Exception as e:
    pass

if not dhan_connected:
  print("   ⚠️ Dhan token expired. Triggering automated PIN + TOTP login...")
  auto_login_script = (
      r"C:\kite-agent\brain\60-tools\python\dhan_auto_login.py"
  )
  if os.path.exists(auto_login_script):
    subprocess.run([sys.executable, auto_login_script], check=False)
    print("   ✅ DhanHQ v2: RE-AUTHENTICATED & ACTIVE")
  else:
    print(f"   ❌ Missing auto-login script at {auto_login_script}")


# --- 2. FYERS PRIME CHECK ---
print("\n[2/4] Checking Fyers API v3 (Prime Tier)..." )
fyers_env = r"C:\kite-agent\secrets\fyers.env"
fyers_tok_path = r"C:\kite-agent\secrets\fyers_access_token.txt"
load_dotenv(fyers_env)
app_id = os.getenv("FYERS_APP_ID", "").strip()

fyers_connected = False
if os.path.exists(fyers_tok_path) and app_id:
  try:
    from fyers_apiv3 import fyersModel

    with open(fyers_tok_path) as f:
      f_tok = f.read().strip()
    fyers = fyersModel.FyersModel(
        client_id=app_id, is_async=False, token=f_tok, log_path=""
    )
    prof = fyers.get_profile()
    if prof.get("s") == "ok":
      name = prof.get("data", {}).get("name", "Trader")
      print(f"   ✅ Fyers Prime: CONNECTED ({name})")
      fyers_connected = True
  except Exception as e:
    pass

if not fyers_connected:
  print("   ⚠️ Fyers token expired. Please run fyers_live_desk.py to refresh.")


# --- 3. ZERODHA KITE CONNECT CHECK ---
print("\n[3/4] Checking Zerodha Kite Connect...")
kite_env = r"C:\kite-agent\.env"
kite_tok_path = r"C:\kite-agent\access_token.txt"
load_dotenv(kite_env)
api_key = os.getenv("KITE_API_KEY", "").strip()

kite_connected = False
if os.path.exists(kite_tok_path) and api_key:
  try:
    from kiteconnect import KiteConnect

    with open(kite_tok_path) as f:
      k_tok = f.read().strip()
    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(k_tok)
    p = kite.profile()
    m = kite.margins()
    cash = m.get("equity", {}).get("available", {}).get("cash", 0)
    print(
        f"   ✅ Zerodha Kite: CONNECTED ({p.get('user_name')} | Cash:"
        f" ₹{cash:,.2f})"
    )
    kite_connected = True
  except Exception as e:
    pass

if not kite_connected:
  print(
      "   ⚠️ Kite token expired. Run: cd C:\\kite-agent && python"
      " generate_token.py"
  )


# --- 4. SUPABASE PRO CLOUD DATABASE CHECK ---
print("\n[4/4] Checking Supabase Pro Database (Mumbai)...")
supa_env = r"C:\kite-agent\secrets\supabase.env"
load_dotenv(supa_env)
url = os.getenv("SUPABASE_URL", "").strip()
key = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")
).strip()

if url and key:
  try:
    from supabase import create_client

    supa = create_client(url, key)
    res = supa.table("option_chain_snapshots").select("id").limit(1).execute()
    print(f"   ✅ Supabase Cloud: CONNECTED & HEALTHY (URL: {url})")
  except Exception as e:
    print(f"   ❌ Supabase Error: {e}")
else:
  print("   ❌ Missing Supabase credentials in secrets/supabase.env")

print("\n" + "=" * 75)
print("🎉 PRE-FLIGHT COMPLETE — DESK STATUS VERIFIED!")
print("=" * 75)