# =============================================================================
# File: 60-tools/python/institutional_market_engine.py
# Description: Institutional Dual-Engine Option Matrix, Greeks, GEX & DOM
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

# 1. Load Secrets
FYERS_ENV = r"C:\kite-agent\secrets\fyers.env"
SUPABASE_ENV = r"C:\kite-agent\secrets\supabase.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"
DATASET_DIR = r"C:\kite-agent\brain\20-market-data\datasets\snapshots"

os.makedirs(DATASET_DIR, exist_ok=True)
load_dotenv(FYERS_ENV)
load_dotenv(SUPABASE_ENV)

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()

if not os.path.exists(TOKEN_PATH):
  print("❌ Error: fyers_access_token.txt missing. Run fyers_auth.py first.")
  exit(1)

with open(TOKEN_PATH) as f:
  ACCESS_TOKEN = f.read().strip()

# Initialize API Clients
fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)


# --- 2. Local Black-76 Numerical Greeks Engine (Fallback) ---
def black76_price(F, K, T, r, sigma, option_type="CE"):
  if T <= 0 or sigma <= 0:
    return max(0.0, F - K) if option_type == "CE" else max(0.0, K - F)
  d1 = (np.log(F / K) + (0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  d2 = d1 - sigma * np.sqrt(T)
  df = np.exp(-r * T)
  if option_type == "CE":
    return df * (F * norm.cdf(d1) - K * norm.cdf(d2))
  else:
    return df * (K * norm.cdf(-d2) - F * norm.cdf(-d1))


def solve_iv(price, F, K, T, r=0.0675, option_type="CE"):
  if T <= 0.001 or price <= 0:
    return 0.15
  df = np.exp(-r * T)
  intrinsic = max(0.0, F - K) if option_type == "CE" else max(0.0, K - F)
  if price < df * intrinsic:
    return 0.10

  def objective(sigma):
    return black76_price(F, K, T, r, sigma, option_type) - price

  try:
    return brentq(objective, 0.01, 3.00, xtol=1e-4)
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


# --- 3. Institutional Matrix & Order Flow Engine ---
def process_market_snapshot(symbol="NSE:NIFTY50-INDEX", strike_count=15):
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  )
  if res.get("s") != "ok":
    print(f"❌ Fyers API Error for {symbol}: {res.get('message')}")
    return None

  chain_data = res.get("data", {})
  options_list = chain_data.get("optionsChain", [])
  if not options_list:
    return None

  # 1. Parse Spot Price
  spot_price = float(chain_data.get("spotPrice", 0))
  calls = {}
  puts = {}

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
  now_iso = datetime.datetime.now().isoformat()
  T_years = max(2.5 / 365.0, 0.002)

  total_call_oi = 0
  total_put_oi = 0
  total_call_vol = 0
  total_put_vol = 0
  atm_strike = min(all_strikes, key=lambda x: abs(x - spot_price))
  atm_straddle_premium = 0.0
  gex_total = 0.0

  parsed_rows = []
  supabase_rows = []

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
    c_vol = int(get_val(c, ["volume"], default=0))
    p_vol = int(get_val(p, ["volume"], default=0))

    total_call_oi += c_oi
    total_put_oi += p_oi
    total_call_vol += c_vol
    total_put_vol += p_vol

    # Dual-Engine Greeks: Check Fyers first; fallback to Black-76
    c_iv_api = get_val(c, ["iv"], default=0.0)
    p_iv_api = get_val(p, ["iv"], default=0.0)

    c_iv = (
        c_iv_api / 100.0
        if c_iv_api > 0
        else solve_iv(c_price, spot_price, strike, T_years, option_type="CE")
    )
    p_iv = (
        p_iv_api / 100.0
        if p_iv_api > 0
        else solve_iv(p_price, spot_price, strike, T_years, option_type="PE")
    )

    c_greeks = (
        {"delta": get_val(c, ["delta"]), "theta": get_val(c, ["theta"])}
        if c_iv_api > 0
        else calculate_greeks(
            spot_price, strike, T_years, 0.0675, c_iv, option_type="CE"
        )
    )
    p_greeks = (
        {"delta": get_val(p, ["delta"]), "theta": get_val(p, ["theta"])}
        if p_iv_api > 0
        else calculate_greeks(
            spot_price, strike, T_years, 0.0675, p_iv, option_type="PE"
        )
    )

    # Net Gamma Exposure (GEX) Calculation
    gamma_val = c_greeks.get("gamma", 0.0)
    gex_strike = (c_oi * gamma_val * spot_price * 100) - (
        p_oi * gamma_val * spot_price * 100
    )
    gex_total += gex_strike

    if strike == atm_strike:
      atm_straddle_premium = c_price + p_price

    parsed_rows.append({
        "strike": strike,
        "c_oi": c_oi,
        "c_iv": round(c_iv * 100, 2),
        "c_delta": c_greeks.get("delta", 0),
        "c_price": c_price,
        "p_price": p_price,
        "p_delta": p_greeks.get("delta", 0),
        "p_iv": round(p_iv * 100, 2),
        "p_oi": p_oi,
    })

    # Prepare Supabase payloads for both CE and PE
    supabase_rows.append({
        "underlying": symbol,
        "spot_price": spot_price,
        "strike_price": float(strike),
        "option_type": "CE",
        "ltp": c_price,
        "oi": c_oi,
        "volume": c_vol,
        "iv": round(c_iv * 100, 2),
        "delta": c_greeks.get("delta", 0),
        "theta": c_greeks.get("theta", 0),
    })
    supabase_rows.append({
        "underlying": symbol,
        "spot_price": spot_price,
        "strike_price": float(strike),
        "option_type": "PE",
        "ltp": p_price,
        "oi": p_oi,
        "volume": p_vol,
        "iv": round(p_iv * 100, 2),
        "delta": p_greeks.get("delta", 0),
        "theta": p_greeks.get("theta", 0),
    })

  # Compute Key Desk Statistics
  pcr_oi = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0.0
  pcr_vol = (total_put_vol / total_call_vol) if total_call_vol > 0 else 0.0
  implied_move_pct = (
      (atm_straddle_premium / spot_price) * 100 if spot_price > 0 else 0.0
  )

  # Max Pain Calculation (Strike where payout is minimum)
  pain_per_strike = {}
  for target_k in all_strikes:
    total_loss = 0.0
    for row in parsed_rows:
      k = row["strike"]
      # Call writer loss if spot finishes at target_k
      if target_k > k:
        total_loss += (target_k - k) * row["c_oi"]
      # Put writer loss if spot finishes at target_k
      if target_k < k:
        total_loss += (k - target_k) * row["p_oi"]
    pain_per_strike[target_k] = total_loss
  max_pain_strike = min(pain_per_strike, key=pain_per_strike.get)

  # --- Print Formatted Console Matrix ---
  print("\n" + "=" * 110)
  print(
      f"⚡ INSTITUTIONAL MATRIX: {symbol} | Spot: ₹{spot_price:,.2f} | Time:"
      f" {now_iso[11:19]}"
  )
  print("=" * 110)
  print(
      f"📊 PCR (OI)       : {pcr_oi:.2f} {'(Bullish)' if pcr_oi > 1.1 else '(Bearish)' if pcr_oi < 0.8 else '(Neutral)'}"
  )
  print(f"🎯 Max Pain Strike: {max_pain_strike:,.0f}")
  print(
      f"🪙 ATM Straddle   : ₹{atm_straddle_premium:.2f} (Implied Expiry Move:"
      f" ±{implied_move_pct:.2f}%)"
  )
  print(
      f"🧲 Net Dealer GEX : {gex_total / 1e7:,.2f} Cr"
      f" {'(Vol Dampening / Range)' if gex_total > 0 else '(Vol Accelerating / Breakout)'}"
  )
  print("-" * 110)
  print(
      f"{'Call OI':>10} | {'Call IV':>8} | {'Delta':>7} | {'Call Price':>10} |"
      f" {'STRIKE':^8} | {'Put Price':>10} | {'Delta':>7} | {'Put IV':>8} |"
      f" {'Put OI':>10}"
  )
  print("-" * 110)

  for r in parsed_rows:
    is_atm = "➡️" if r["strike"] == atm_strike else "  "
    print(
        f"{r['c_oi']:>10,d} | {r['c_iv']:>8.2f} | {r['c_delta']:>7.2f} |"
        f" {r['c_price']:>10.2f} | {is_atm}{r['strike']:^6.0f} |"
        f" {r['p_price']:>10.2f} | {r['p_delta']:>7.2f} | {r['p_iv']:>8.2f} |"
        f" {r['p_oi']:>10,d}"
    )
  print("=" * 110)

  # Save to Parquet
  today_str = datetime.date.today().strftime("%Y%m%d")
  sym_clean = symbol.replace(":", "_").replace("-", "_")
  parquet_path = os.path.join(
      DATASET_DIR, f"{sym_clean}_quant_matrix_{today_str}.parquet"
  )
  df = pd.DataFrame(supabase_rows)
  if os.path.exists(parquet_path):
    existing_df = pd.read_parquet(parquet_path)
    df = pd.concat([existing_df, df], ignore_index=True)
  df.to_parquet(parquet_path, index=False)

  # Upload to Supabase Cloud
  if supabase:
    try:
      supabase.table("option_chain_snapshots").insert(supabase_rows).execute()
      print(f"☁️ Synced {len(supabase_rows)} records to Supabase Cloud.")
    except Exception as e:
      print(f"⚠️ Supabase upload skipped: {e}")

  return True


def run_continuous_loop(interval_sec=60):
  print(f"\n🚀 STARTING 1-MINUTE QUANTITATIVE SNAPSHOTTER LOOP (Ctrl+C to stop)")
  while True:
    try:
      process_market_snapshot("NSE:NIFTY50-INDEX", strike_count=10)
      process_market_snapshot("BSE:SENSEX-INDEX", strike_count=10)
      print(
          f"\n⏳ Sleeping for {interval_sec} seconds until next snapshot..."
      )
      time.sleep(interval_sec)
    except KeyboardInterrupt:
      print("\n🛑 Stopped snapshotter loop.")
      break
    except Exception as e:
      print(f"⚠️ Error during cycle: {e}")
      time.sleep(10)


if __name__ == "__main__":
  # Run a single snapshot pass, or run with argument 'loop' for continuous capture
  if len(sys.argv) > 1 and sys.argv.lower() == "loop":
    run_continuous_loop(interval_sec=60)
  else:
    process_market_snapshot("NSE:NIFTY50-INDEX", strike_count=10)
    process_market_snapshot("BSE:SENSEX-INDEX", strike_count=10)