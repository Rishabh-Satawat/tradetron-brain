# =============================================================================
# File: 60-tools/python/oi_buildup_engine.py
# Description: 4-Quadrant Open Interest Dynamics & Strike Migration Engine
# Release: RELEASE 2 (Honest Institutional Order Flow Tracking)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import pandas as pd

load_dotenv(r"C:\kite-agent\secrets\fyers.env")
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


def classify_buildup(delta_price, delta_oi):
  """4-Quadrant Open Interest Dynamics Matrix."""
  if delta_oi > 0:
    return (
        "🟢 Long Buildup" if delta_price >= 0 else "🔴 Short Buildup"
    )
  elif delta_oi < 0:
    return (
        "🔵 Short Covering" if delta_price >= 0 else "🟡 Long Unwinding"
    )
  return "⚪ Neutral"


def get_val(d, keys, default=0.0):
  for k in keys:
    v = d.get(k)
    if v is not None and v != "":
      return float(v)
  return default


def analyze_oi_dynamics(symbol="NSE:NIFTY50-INDEX", strike_count=12):
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  )
  if res.get("s") != "ok":
    print(f"❌ Failed to fetch option chain: {res.get('message')}")
    return

  chain_data = res.get("data", {})
  spot = float(chain_data.get("spotPrice", 0))
  options_list = chain_data.get("optionsChain", [])
  expiry = chain_data.get("expiry", "Current")

  calls, puts = {}, {}
  for item in options_list:
    strike = item.get("strike_price")
    if strike == -1:
      if spot == 0:
        spot = get_val(
            item, ["ltp", "prev_close_price", "close_price"], default=0.0
        )
      continue
    if item.get("option_type") == "CE":
      calls[strike] = item
    elif item.get("option_type") == "PE":
      puts[strike] = item

  all_strikes = sorted(list(set(list(calls.keys()) + list(puts.keys()))))
  atm_strike = (
      min(all_strikes, key=lambda x: abs(x - spot)) if all_strikes else spot
  )

  call_centroid_num = 0.0
  call_centroid_den = 0.0
  put_centroid_num = 0.0
  put_centroid_den = 0.0

  total_call_oi = 0
  total_put_oi = 0
  parsed_rows = []

  for strike in all_strikes:
    c = calls.get(strike, {})
    p = puts.get(strike, {})

    c_price = get_val(
        c, ["ltp", "prev_close_price", "close_price"], default=0.0
    )
    p_price = get_val(
        p, ["ltp", "prev_close_price", "close_price"], default=0.0
    )
    c_prev = get_val(c, ["prev_close_price", "o"], default=c_price)
    p_prev = get_val(p, ["prev_close_price", "o"], default=p_price)

    c_oi = int(get_val(c, ["oi"], default=0))
    p_oi = int(get_val(p, ["oi"], default=0))
    c_oi_chg = int(get_val(c, ["oichange"], default=0))
    p_oi_chg = int(get_val(p, ["oichange"], default=0))

    total_call_oi += c_oi
    total_put_oi += p_oi

    # Price Changes
    c_dp = c_price - c_prev
    p_dp = p_price - p_prev

    # 4-Quadrant Buildup Classification
    c_regime = classify_buildup(c_dp, c_oi_chg)
    p_regime = classify_buildup(p_dp, p_oi_chg)

    # Activity-Weighted Resistance Centroid
    if abs(c_oi_chg) > 0:
      call_centroid_num += strike * abs(c_oi_chg)
      call_centroid_den += abs(c_oi_chg)
    if abs(p_oi_chg) > 0:
      put_centroid_num += strike * abs(p_oi_chg)
      put_centroid_den += abs(p_oi_chg)

    parsed_rows.append({
        "strike": strike,
        "c_oi": c_oi,
        "c_oichg": c_oi_chg,
        "c_regime": c_regime,
        "p_regime": p_regime,
        "p_oichg": p_oi_chg,
        "p_oi": p_oi,
    })

  # Centroids
  call_centroid = (
      call_centroid_num / call_centroid_den
      if call_centroid_den > 0
      else atm_strike
  )
  put_centroid = (
      put_centroid_num / put_centroid_den
      if put_centroid_den > 0
      else atm_strike
  )
  pcr = total_put_oi / total_call_oi if total_call_oi > 0 else 0.0

  now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
  print("=" * 110)
  print(
      f"📊 4-QUADRANT OPEN INTEREST & MIGRATION MATRIX: {symbol} | Spot:"
      f" ₹{spot:,.2f}"
  )
  print(f"📅 Active Expiry: {expiry} | Time: {now_str}")
  print("=" * 110)
  print(f"📌 Market PCR (OI)        : {pcr:.2f}")
  print(f"🛡️ Call Resistance Wall   : {call_centroid:,.0f} Strike Centroid")
  print(f"🏰 Put Support Floor       : {put_centroid:,.0f} Strike Centroid")
  print("-" * 110)
  print(
      f"{'Call OI':>10} | {'Call ΔOI':>9} | {'Call Regime':<18} | {'STRIKE':^8}"
      f" | {'Put Regime':<18} | {'Put ΔOI':>9} | {'Put OI':>10}"
  )
  print("-" * 110)

  for r in parsed_rows:
    is_atm = "➡️" if r["strike"] == atm_strike else "  "
    print(
        f"{r['c_oi']:>10,d} | {r['c_oichg']:>+9,d} | {r['c_regime']:<18} |"
        f" {is_atm}{r['strike']:^6.0f} | {r['p_regime']:<18} |"
        f" {r['p_oichg']:>+9,d} | {r['p_oi']:>10,d}"
    )
  print("=" * 110)


if __name__ == "__main__":
  analyze_oi_dynamics("NSE:NIFTY50-INDEX", 10)