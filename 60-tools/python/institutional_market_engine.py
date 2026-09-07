# =============================================================================
# File: 60-tools/python/institutional_market_engine.py
# Description: Institutional Market Engine with Complete Greeks & GEX Proxy
# Status: RELEASE 0 CONTAINMENT PATCH (P0 GEX Bug Fix)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import math
import os
import sys
import time
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm
from supabase import create_client, Client

# Load environment
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

if not os.path.exists(TOKEN_PATH):
  sys.exit(1)

with open(TOKEN_PATH) as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)


# --- 1. Black-76 Greeks Engine ---
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
        lambda s: black76_price(F, K, T, r, s, option_type) - price,
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


# --- 2. Ingestion & Corrected GEX Proxy ---
def process_market_snapshot(symbol="NSE:NIFTY50-INDEX", strike_count=15):
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  )
  if res.get("s") != "ok":
    return False

  chain_data = res.get("data", {})
  options_list = chain_data.get("optionsChain", [])
  if not options_list:
    return False

  spot_price = float(chain_data.get("spotPrice", 0))
  calls, puts = {}, {}

  for item in options_list:
    strike = item.get("strike_price")
    if strike == -1:
      if spot_price == 0:
        spot_price = get_val(
            item, ["ltp", "prev_close_price", "close_price"], default=0.0
        )
      continue
    if item.get("option_type") == "CE":
      calls[strike] = item
    elif item.get("option_type") == "PE":
      puts[strike] = item

  all_strikes = sorted(list(set(list(calls.keys()) + list(puts.keys()))))
  now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
  T_years = max(2.5 / 365.0, 0.002)

  total_call_oi, total_put_oi = 0, 0
  atm_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
  atm_straddle_premium = 0.0
  gex_proxy_total = 0.0
  parsed_rows = []

  # Contract multiplier (Lot size)
  contract_mult = 20 if "SENSEX" in symbol else 65

  for strike in all_strikes:
    c = calls.get(strike, {})
    p = puts.get(strike, {})

    c_price = get_val(
        c, ["ltp", "prev_close_price", "close_price"], default=0.0
    )
    p_price = get_val(
        p, ["ltp", "prev_close_price", "close_price"], default=0.0
    )
    c_oi = int(get_val(c, ["oi"], default=0))
    p_oi = int(get_val(p, ["oi"], default=0))

    total_call_oi += c_oi
    total_put_oi += p_oi

    # Solve IV via Brent's method
    c_iv = solve_iv(c_price, spot_price, strike, T_years, option_type="CE")
    p_iv = solve_iv(p_price, spot_price, strike, T_years, option_type="PE")

    # Always compute complete Greek vector (Fixes the missing gamma bug)
    c_greeks = calculate_greeks(
        spot_price, strike, T_years, 0.0675, c_iv, option_type="CE"
    )
    p_greeks = calculate_greeks(
        spot_price, strike, T_years, 0.0675, p_iv, option_type="PE"
    )

    # Corrected GEX Proxy formula with contract multiplier and spot^2
    c_gamma = c_greeks["gamma"]
    p_gamma = p_greeks["gamma"]

    # Scenario: Dealer long calls / short puts assumption proxy
    call_gex = c_oi * contract_mult * (spot_price**2) * c_gamma * 0.01
    put_gex = p_oi * contract_mult * (spot_price**2) * p_gamma * 0.01
    gex_proxy_total += call_gex - put_gex

    if strike == atm_strike:
      atm_straddle_premium = c_price + p_price

    parsed_rows.append({
        "strike": strike,
        "c_oi": c_oi,
        "c_iv": round(c_iv * 100, 2),
        "c_delta": c_greeks["delta"],
        "c_gamma": c_gamma,
        "c_price": c_price,
        "p_price": p_price,
        "p_delta": p_greeks["delta"],
        "p_gamma": p_gamma,
        "p_iv": round(p_iv * 100, 2),
        "p_oi": p_oi,
    })

  pcr = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0.0

  print("=" * 95)
  print(f"⚡ CORRECTED GREEKS & GEX PROXY: {symbol} | Spot: ₹{spot_price:,.2f}")
  print("=" * 95)
  print(f"📊 Market PCR (OI)     : {pcr:.2f}")
  print(f"🪙 ATM Straddle Cost   : ₹{atm_straddle_premium:.2f}")
  print(f"🧲 Net GEX Proxy       : {gex_proxy_total / 1e7:+,.2f} Cr [Scenario-Modelled]")
  print("-" * 95)
  print(f"{'Call OI':>9} | {'C-Delta':>7} | {'C-Gamma':>8} | {'Strike':^8} | {'P-Gamma':>8} | {'P-Delta':>7} | {'Put OI':>9}")
  print("-" * 95)

  for r in parsed_rows[len(parsed_rows) // 2 - 3 : len(parsed_rows) // 2 + 4]:
    is_atm = "➡️" if r["strike"] == atm_strike else "  "
    print(
        f"{r['c_oi']:>9,d} | {r['c_delta']:>7.2f} | {r['c_gamma']:>8.5f} |"
        f" {is_atm}{r['strike']:^6.0f} | {r['p_gamma']:>8.5f} |"
        f" {r['p_delta']:>7.2f} | {r['p_oi']:>9,d}"
    )
  print("=" * 95)
  return True


if __name__ == "__main__":
  process_market_snapshot("NSE:NIFTY50-INDEX", 10)
  process_market_snapshot("BSE:SENSEX-INDEX", 10)