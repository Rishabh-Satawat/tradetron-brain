# =============================================================================
# File: 60-tools/python/live_portfolio_risk_sentinel.py
# Description: Real-Time Demat Position Greeks, OI Threat Detector & Hedging Alert
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import json
import os
import sys
import time
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
from kiteconnect import KiteConnect

# 1. Load Secrets
load_dotenv(r"C:\kite-agent\.env")
load_dotenv(r"C:\kite-agent\secrets\fyers.env")

KITE_KEY = os.getenv("KITE_API_KEY", "").strip()
FYERS_APP = os.getenv("FYERS_APP_ID", "").strip()

KITE_TOK_PATH = r"C:\kite-agent\access_token.txt"
FYERS_TOK_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"
DIRECTIVE_PATH = r"C:\kite-agent\brain\70-ops\status\regime_directive.json"

if not os.path.exists(KITE_TOK_PATH) or not os.path.exists(FYERS_TOK_PATH):
  print("❌ Error: Broker tokens missing. Run start_desk.ps1 first.")
  sys.exit(1)

with open(KITE_TOK_PATH) as f:
  kite_token = f.read().strip()
with open(FYERS_TOK_PATH) as f:
  fyers_token = f.read().strip()

kite = KiteConnect(api_key=KITE_KEY)
kite.set_access_token(kite_token)
fyers = fyersModel.FyersModel(
    client_id=FYERS_APP, is_async=False, token=fyers_token, log_path=""
)


def get_live_demat_positions():
  """Fetches active non-zero derivative positions from Zerodha Kite."""
  try:
    pos_data = kite.positions()
    net_positions = pos_data.get("net", [])
    active = [p for p in net_positions if p.get("quantity", 0) != 0]
    return active
  except Exception as e:
    print(f"⚠️ Error fetching Kite positions: {e}")
    return []


def analyze_portfolio_risk():
  print("=" * 85)
  print("🛡️ QUANT DESK — REAL-TIME DEMAT POSITION RISK & HEDGING SENTINEL")
  print(f"⏰ Scan Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
  print("=" * 85)

  # 1. Inspect Active Demat Positions
  positions = get_live_demat_positions()

  if not positions:
    print("ℹ️ Zero open positions in Zerodha Demat account. Desk is in CASH.")
    print("=" * 85)
    return

  total_m2m = sum(p.get("m2m", 0.0) for p in positions)
  total_pnl = sum(p.get("pnl", 0.0) for p in positions)

  print(f"📊 Active Open Positions: {len(positions)} legs")
  print(
      f"💰 Real-Time M2M P&L    : ₹{total_m2m:+,.2f} (Unrealized: ₹{total_pnl:+,.2f})"
  )
  print("-" * 85)
  print(
      f"{'Instrument':<28} | {'Qty':>5} | {'Avg Price':>9} | {'LTP':>8} |"
      f" {'Current P&L':>11}"
  )
  print("-" * 85)

  net_delta_exposure = 0.0
  is_long_biased = False
  is_short_biased = False

  for p in positions:
    tradingsymbol = p.get("tradingsymbol", "Unknown")
    qty = p.get("quantity", 0)
    avg_price = float(p.get("average_price", 0.0))
    ltp = float(p.get("last_price", 0.0))
    pnl = float(p.get("pnl", 0.0))

    if "CE" in tradingsymbol:
      net_delta_exposure += 0.50 * qty
    elif "PE" in tradingsymbol:
      net_delta_exposure -= 0.50 * qty
    elif "FUT" in tradingsymbol:
      net_delta_exposure += 1.0 * qty

    print(
        f"{tradingsymbol:<28} | {qty:>5} | {avg_price:>9.2f} | {ltp:>8.2f} |"
        f" ₹{pnl:>+10,.2f}"
    )

  print("-" * 85)
  print(f"📐 Approximate Net Position Delta: {net_delta_exposure:+.1f} shares")

  if net_delta_exposure > 20:
    is_long_biased = True
    print("📈 Portfolio Stance: NET LONG (Profits on rallies, loses on drops)")
  elif net_delta_exposure < -20:
    is_short_biased = True
    print("📉 Portfolio Stance: NET SHORT (Profits on drops, loses on rallies)")
  else:
    print("⚖️ Portfolio Stance: DELTA NEUTRAL (Protected Spread / Iron Fly)")

  # 2. Read Market Regime Threats from Fyers Directive
  if os.path.exists(DIRECTIVE_PATH):
    with open(DIRECTIVE_PATH, "r", encoding="utf-8") as f:
      reg = json.load(f)

    spot = float(reg.get("spot_price", 0))
    pcr = float(reg.get("pcr", 1.0))
    dominant_buildup = reg.get("dominant_buildup", "Neutral")
    call_wall = float(reg.get("call_wall", 0))
    put_floor = float(reg.get("put_floor", 0))

    print("\n🔍 MARKET STRUCTURE & THREAT RADAR:")
    print(
        f"   • Current SENSEX Spot : ₹{spot:,.2f} | Market PCR: {pcr:.2f}"
        f" ({dominant_buildup})"
    )
    print(
        f"   • Key Structural Walls: Support @ ₹{put_floor:,.0f} | Resistance @"
        f" ₹{call_wall:,.0f}"
    )

    # 3. Automated Risk & Hedging Alarm Dispatcher
    print("\n" + "=" * 85)
    print("🚨 SENTINEL THREAT ASSESSMENT & HEDGING DIRECTIVE")
    print("=" * 85)

    threat_detected = False

    # THREAT A: Holding Long position while market develops Short Buildup
    if is_long_biased and (pcr < 0.85 or dominant_buildup == "Short Buildup"):
      threat_detected = True
      print("⚠️ CRITICAL RISK WARNING: Bearish OI buildup against your LONG position!")
      print(
          f"   • Cause: Heavy Call writing observed; PCR collapsed to {pcr:.2f}."
      )
      print(
          f"   • Stop-Loss Level: ₹{put_floor:,.0f} (If broken, expect aggressive long liquidation)."
      )
      print(
          f"   • RECOMMENDED HEDGE: Buy ATM Put option or scale out of 50% long quantity immediately."
      )

    # THREAT B: Holding Short position while Put writers accumulate
    elif is_short_biased and (pcr > 1.25 or dominant_buildup == "Long Buildup"):
      threat_detected = True
      print("⚠️ CRITICAL RISK WARNING: Bullish OI buildup against your SHORT position!")
      print(
          f"   • Cause: Aggressive Put writing floor forming; PCR elevated at {pcr:.2f}."
      )
      print(
          f"   • Stop-Loss Level: ₹{call_wall:,.0f} (Breakout zone above call writers)."
      )
      print(
          f"   • RECOMMENDED HEDGE: Buy ATM Call option or tighten stop to cost."
      )

    # THREAT C: Approaching structural support floor
    if is_long_biased and spot < put_floor:
      threat_detected = True
      print(
          f"🚨 EMERGENCY ALERT: SENSEX spot (₹{spot:,.2f}) has breached Put"
          f" Support Floor (₹{put_floor:,.0f})!"
      )
      print(
          "   • ACTION REQUIRED: Institutional put writers are unwinding."
          " Execute emergency hedge or exit position."
      )

    if not threat_detected:
      print(
          "✅ All clear. Market regime and open position delta are in harmony."
      )
      print("   • No hedging required at this time. Maintain active trailing stop.")

    print("=" * 85)


if __name__ == "__main__":
  analyze_portfolio_risk()