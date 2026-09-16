# =============================================================================
# File: 60-tools/python/sync_to_supabase.py
# Description: Syncs Live Option Chains & Greeks (NIFTY & SENSEX) to Supabase Cloud
# Table: public.option_chain_snapshots (Schema Matched)
# Primary Data Feed: Dhan HQ v2 API (Scrip 13: NIFTY 50 | Scrip 51: BSE SENSEX)
# =============================================================================
import datetime
import math
import os
import sys
from dotenv import load_dotenv
import requests
from scipy.stats import norm
from supabase import Client, create_client

# 1. Load Credentials
for p in [
    r"C:\kite-agent\secrets\dhan.env",
    r"C:\kite-agent\brain\secrets\dhan.env",
]:
  if os.path.exists(p):
    load_dotenv(p)
    break

token = os.getenv("DHAN_ACCESS_TOKEN") or os.getenv("DHAN_TOKEN")
client_id = os.getenv("DHAN_CLIENT_ID", "1111831735")

# Load Supabase
supabase_env = r"C:\kite-agent\secrets\supabase.env"
if os.path.exists(supabase_env):
  load_dotenv(supabase_env)

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    or os.getenv("SUPABASE_KEY", "")
).strip()

if not SUPABASE_URL or not SUPABASE_KEY:
  print("❌ Error: SUPABASE_URL or SUPABASE_KEY missing in secrets/supabase.env")
  sys.exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

DHAN_HEADERS = {
    "access-token": token,
    "client-id": client_id,
    "Content-Type": "application/json",
}


def calculate_black76_greeks(spot, strike, t, r, iv, opt_type):
  """Computes Black-76 Greeks for European index options."""
  if t <= 0.0001 or iv <= 0.001:
    return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}

  try:
    d1 = (math.log(spot / strike) + 0.5 * (iv**2) * t) / (iv * math.sqrt(t))
    d2 = d1 - iv * math.sqrt(t)

    pdf_d1 = norm.pdf(d1)
    cdf_d1 = norm.cdf(d1)
    cdf_neg_d1 = norm.cdf(-d1)

    gamma = pdf_d1 / (spot * iv * math.sqrt(t))
    vega = (spot * math.sqrt(t) * pdf_d1) / 100.0

    if opt_type == "CE":
      delta = cdf_d1
      theta = (
          -(spot * pdf_d1 * iv) / (2 * math.sqrt(t))
          - r * strike * math.exp(-r * t) * norm.cdf(d2)
      ) / 365.0
    else:
      delta = -cdf_neg_d1
      theta = (
          -(spot * pdf_d1 * iv) / (2 * math.sqrt(t))
          + r * strike * math.exp(-r * t) * norm.cdf(-d2)
      ) / 365.0

    return {
        "delta": round(float(delta), 4),
        "gamma": round(float(gamma), 6),
        "theta": round(float(theta), 2),
        "vega": round(float(vega), 2),
    }
  except Exception:
    return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}


def sync_index_option_chain(symbol_name, scrip_id):
  print(f"\n🔄 Fetching {symbol_name} from Dhan and computing Greeks...")

  # Dynamic Expiry Lookup
  active_expiry = None
  try:
    exp_res = requests.post(
        "https://api.dhan.co/v2/optionchain/expirylist",
        headers=DHAN_HEADERS,
        json={"UnderlyingScrip": scrip_id, "UnderlyingSeg": "IDX_I"},
        timeout=6,
    )
    if exp_res.status_code == 200:
      exp_list = exp_res.json().get("data", [])
      if exp_list:
        active_expiry = exp_list[0]
  except Exception as e:
    print(f"⚠️ Expiry list fetch note: {e}")

  if not active_expiry:
    active_expiry = "2026-09-17" if scrip_id == 51 else "2026-09-22"

  # Option Chain Query
  oc_res = requests.post(
      "https://api.dhan.co/v2/optionchain",
      headers=DHAN_HEADERS,
      json={
          "UnderlyingScrip": scrip_id,
          "UnderlyingSeg": "IDX_I",
          "Expiry": active_expiry,
      },
      timeout=10,
  )

  if oc_res.status_code != 200:
    print(f"❌ Error fetching Dhan option chain: {oc_res.status_code}")
    return 0

  chain_data = oc_res.json().get("data", {})
  spot = float(chain_data.get("last_price", 0.0))
  oc = chain_data.get("oc", {})

  if spot <= 0 or not oc:
    print(f"⚠️ Empty option chain data received for {symbol_name}.")
    return 0

  # Days to expiry
  try:
    exp_dt = datetime.datetime.strptime(active_expiry, "%Y-%m-%d")
    days_to_exp = max(
        0.001, (exp_dt - datetime.datetime.now()).total_seconds() / 86400.0
    )
    t = days_to_exp / 365.0
  except Exception:
    t = 1.0 / 365.0

  r = 0.07  # RBI benchmark rate ~7%
  now_iso = datetime.datetime.now().isoformat()
  records = []

  for strike_str, leg in oc.items():
    strike = float(strike_str)

    # CE
    ce = leg.get("ce", {})
    if ce:
      ce_price = float(ce.get("last_price", 0.0))
      ce_iv = float(ce.get("iv", 0.0)) / 100.0 if ce.get("iv") else 0.13
      greeks_ce = calculate_black76_greeks(spot, strike, t, r, ce_iv, "CE")
      records.append({
          "underlying": symbol_name,
          "spot_price": spot,
          "strike_price": strike,
          "option_type": "CE",
          "ltp": ce_price,
          "oi": int(ce.get("oi", 0)),
          "volume": int(ce.get("volume", 0)),
          "iv": round(ce_iv * 100, 2),
          "delta": greeks_ce["delta"],
          "gamma": greeks_ce["gamma"],
          "theta": greeks_ce["theta"],
          "vega": greeks_ce["vega"],
          "created_at": now_iso,
      })

    # PE
    pe = leg.get("pe", {})
    if pe:
      pe_price = float(pe.get("last_price", 0.0))
      pe_iv = float(pe.get("iv", 0.0)) / 100.0 if pe.get("iv") else 0.13
      greeks_pe = calculate_black76_greeks(spot, strike, t, r, pe_iv, "PE")
      records.append({
          "underlying": symbol_name,
          "spot_price": spot,
          "strike_price": strike,
          "option_type": "PE",
          "ltp": pe_price,
          "oi": int(pe.get("oi", 0)),
          "volume": int(pe.get("volume", 0)),
          "iv": round(pe_iv * 100, 2),
          "delta": greeks_pe["delta"],
          "gamma": greeks_pe["gamma"],
          "theta": greeks_pe["theta"],
          "vega": greeks_pe["vega"],
          "created_at": now_iso,
      })

  # Batch Insert into Supabase (Chunks of 50)
  if records:
    try:
      for i in range(0, len(records), 50):
        chunk = records[i : i + 50]
        supabase.table("option_chain_snapshots").insert(chunk).execute()
      print(
          f"✅ Synced {len(records)} strike records with FULL GREEKS for"
          f" {symbol_name} to Supabase Cloud!"
      )
      return len(records)
    except Exception as e:
      print(f"❌ Supabase sync error: {e}")
      return 0
  return 0


def run_full_sync():
  print("=" * 75)
  print("☁️ DHAN HQ v2 ➔ SUPABASE OPTION CHAIN SYNC ENGINE (BLACK-76 GREEKS)")
  print(
      f"⏰ Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
  )
  print("=" * 75)

  # Sync NIFTY (13) & SENSEX (51)
  sync_index_option_chain("NSE:NIFTY50-INDEX", 13)
  sync_index_option_chain("BSE:SENSEX-INDEX", 51)

  print("\n" + "=" * 75)
  print("🎉 CLOUD GREEKS SYNCHRONIZATION COMPLETE!")
  print("=" * 75)


if __name__ == "__main__":
  run_full_sync()