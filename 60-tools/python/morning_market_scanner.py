# =============================================================================
# File: 60-tools/python/morning_market_scanner.py
# Description: Pre-Market Opening Regime Scanner, PCR & GEX Analyzer
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd

load_dotenv(r"C:\kite-agent\secrets\fyers.env")
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


def get_val(d, keys, default=0.0):
  for k in keys:
    v = d.get(k)
    if v is not None and v != 0 and v != "":
      return float(v)
  return default


def scan_index(symbol="NSE:NIFTY50-INDEX", index_name="NIFTY 50"):
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": 12, "timestamp": ""}
  )
  if res.get("s") != "ok":
    print(f"❌ Failed to scan {index_name}: {res.get('message')}")
    return

  chain_data = res.get("data", {})
  spot = float(chain_data.get("spotPrice", 0))
  options = chain_data.get("optionsChain", [])
  expiry = chain_data.get("expiry", "Current")

  calls = {}
  puts = {}
  for item in options:
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

  tot_call_oi, tot_put_oi = 0, 0
  straddle_cost = 0.0

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

    tot_call_oi += c_oi
    tot_put_oi += p_oi

    if strike == atm_strike:
      straddle_cost = c_price + p_price

  pcr = (tot_put_oi / tot_call_oi) if tot_call_oi > 0 else 0.0
  expected_move_pct = (straddle_cost / spot) * 100 if spot > 0 else 0.0

  # Regime Recommendation Logic
  if pcr > 1.15:
    regime = "🟢 BULLISH BIAS (Put writers active — Watch S01 Bull Call Spread)"
  elif pcr < 0.80:
    regime = "🔴 BEARISH BIAS (Call writers dominant — Watch S06 Bear Put Spread)"
  else:
    regime = (
        "🟡 NEUTRAL / BALANCED (Rangebound expected — Monitor ADX threshold)"
    )

  print(f"\n⚡ {index_name} OPENING REGIME PROFILE")
  print(f"   • Live Spot Price : ₹{spot:,.2f} (ATM Strike: {atm_strike:,.0f})")
  print(f"   • Active Expiry   : {expiry}")
  print(
      f"   • ATM Straddle    : ₹{straddle_cost:.2f} (Implied Move:"
      f" ±{expected_move_pct:.2f}%)"
  )
  print(
      f"   • Market PCR (OI) : {pcr:.2f} (Call OI: {tot_call_oi:,d} | Put OI:"
      f" {tot_put_oi:,d})"
  )
  print(f"   • Desk Verdict    : {regime}")


def main():
  now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S IST")
  print("=" * 80)
  print(f"🌅 PRE-MARKET OPENING DESK SCANNER — {now_str}")
  print("=" * 80)

  scan_index("NSE:NIFTY50-INDEX", "NIFTY 50")
  scan_index("BSE:SENSEX-INDEX", "BSE SENSEX")
  scan_index("NSE:FINNIFTY-INDEX", "FINNIFTY")

  print("\n" + "=" * 80)
  print("📌 TRADETRON DESK: Awaiting 09:20 AM IST entry window.")
  print("=" * 80)


if __name__ == "__main__":
  main()