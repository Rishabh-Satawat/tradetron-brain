# =============================================================================
# File: 60-tools/python/sync_to_supabase.py
# Description: Streams Fyers Option Chain with Local Black-76 Greeks to Supabase
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import math
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm
from supabase import create_client, Client

# 1. Load Secrets
load_dotenv(r"C:\kite-agent\secrets\supabase.env")
load_dotenv(r"C:\kite-agent\secrets\fyers.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
  print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in secrets/supabase.env")
  exit(1)

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  FYERS_TOKEN = f.read().strip()

# Initialize API Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=FYERS_TOKEN, log_path=""
)


# --- 2. Black-76 Mathematical Greeks Engine ---
def black76_price(F, K, T, r, sigma, option_type="CE"):
  if T <= 0 or sigma <= 0:
    return max(0.0, F - K) if option_type == "CE" else max(0.0, K - F)
  d1 = (np.log(F / K) + (0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  d2 = d1 - sigma * np.sqrt(T)
  df = np.exp(-r * T)
  return (
      df * (F * norm.cdf(d1) - K * norm.cdf(d2))
      if option_type == "CE"
      else df * (K * norm.cdf(-d2) - F * norm.cdf(-d1))
  )


def solve_iv(price, F, K, T, r=0.0675, option_type="CE"):
  if T <= 0.001 or price <= 0:
    return 0.15
  df = np.exp(-r * T)
  intrinsic = max(0.0, F - K) if option_type == "CE" else max(0.0, K - F)
  if price < df * intrinsic:
    return 0.10
  try:
    return brentq(
        lambda s: black76_price(F, K, T, r, s, option_type=option_type) - price,
        0.01,
        3.00,
        xtol=1e-4,
    )
  except Exception:
    return 0.15


def calculate_greeks(F, K, T, r, sigma, option_type="CE"):
  if T <= 0 or sigma <= 0:
    return {"delta": 0.0, "gamma": 0.0, "theta": 0.0, "vega": 0.0}
  d1 = (np.log(F / K) + (0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  d2 = d1 - sigma * np.sqrt(T)
  df = np.exp(-r * T)

  gamma = (df * norm.pdf(d1)) / (F * sigma * np.sqrt(T))
  vega = (F * df * norm.pdf(d1) * np.sqrt(T)) / 100.0

  if option_type == "CE":
    delta = df * norm.cdf(d1)
    theta = (
        -(F * df * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        - r * K * df * norm.cdf(d2)
        + r * F * df * norm.cdf(d1)
    ) / 365.0
  else:
    delta = -df * norm.cdf(-d1)
    theta = (
        -(F * df * norm.pdf(d1) * sigma) / (2 * np.sqrt(T))
        + r * K * df * norm.cdf(-d2)
        - r * F * df * norm.cdf(-d1)
    ) / 365.0

  return {
      "delta": round(float(delta), 4),
      "gamma": round(float(gamma), 6),
      "theta": round(float(theta), 2),
      "vega": round(float(vega), 2),
  }


def get_val(d, keys, default=0.0):
  for k in keys:
    v = d.get(k)
    if v is not None and v != 0 and v != "":
      return float(v)
  return default


# --- 3. Sync Option Chain with Real Greeks ---
def sync_chain_to_cloud(symbol="NSE:NIFTY50-INDEX", strike_count=15):
  print(f"\n🔄 Fetching {symbol} from Fyers and computing Greeks...")
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  )

  if res.get("s") != "ok":
    print(f"❌ Fyers Error for {symbol}: {res.get('message')}")
    return

  chain_data = res.get("data", {})
  spot_price = float(chain_data.get("spotPrice", 0))
  options_list = chain_data.get("optionsChain", [])

  # Time to expiry: ~2.5 days for weekly contracts
  T_years = max(2.5 / 365.0, 0.002)
  r = 0.0675

  records_to_insert = []
  for item in options_list:
    strike = item.get("strike_price")
    if strike == -1:
      if spot_price == 0:
        spot_price = get_val(
            item, ["ltp", "prev_close_price", "close_price"], default=0.0
        )
      continue

    opt_type = item.get("option_type")
    ltp = get_val(
        item, ["ltp", "prev_close_price", "close_price"], default=0.0
    )

    # If Fyers sends 0 for IV, our mathematical solver derives it
    broker_iv = get_val(item, ["iv"], default=0.0)
    if broker_iv > 0:
      solved_iv = broker_iv / 100.0 if broker_iv > 1.0 else broker_iv
    else:
      solved_iv = solve_iv(
          ltp, spot_price, float(strike), T_years, r=r, option_type=opt_type
      )

    greeks = calculate_greeks(
        spot_price,
        float(strike),
        T_years,
        r=r,
        sigma=solved_iv,
        option_type=opt_type,
    )

    records_to_insert.append({
        "underlying": symbol,
        "spot_price": spot_price,
        "strike_price": float(strike),
        "option_type": opt_type,
        "ltp": ltp,
        "oi": int(get_val(item, ["oi"], default=0)),
        "volume": int(get_val(item, ["volume"], default=0)),
        "iv": round(solved_iv * 100, 2),
        "delta": greeks["delta"],
        "gamma": greeks["gamma"],
        "theta": greeks["theta"],
        "vega": greeks["vega"],
    })

  if records_to_insert:
    supabase.table("option_chain_snapshots").insert(records_to_insert).execute()
    print(
        f"✅ Synced {len(records_to_insert)} strike records with FULL GREEKS"
        f" for {symbol} to Supabase Cloud!"
    )


if __name__ == "__main__":
  print("=" * 70)
  print("☁️ SUPABASE OPTION CHAIN SYNC ENGINE (BLACK-76 GREEKS)")
  print("=" * 70)
  sync_chain_to_cloud("NSE:NIFTY50-INDEX", strike_count=15)
  sync_chain_to_cloud("BSE:SENSEX-INDEX", strike_count=15)
  print("=" * 70)