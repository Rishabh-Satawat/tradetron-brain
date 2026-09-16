# =============================================================================
# File: 60-tools/python/sensex_expiry_engine.py
# Description: BSE SENSEX 0-DTE Thursday Weekly Expiry Strategy & Execution Engine
# Underlying: BSE SENSEX (BFO) | Lot Size: 20 | Strike Step: 100 points
# Data Provider: Dhan HQ v2 API Native (Scrip ID: 51)
# =============================================================================
import datetime
import json
import os
import sys
from dotenv import load_dotenv
import requests

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

HEADERS = {
    "access-token": token,
    "client-id": client_id,
    "Content-Type": "application/json",
}


def run_sensex_expiry_engine():
  scrip_id = 51  # SENSEX
  lot_size = 20
  strike_step = 100
  wing_offset = 400  # 4 strike steps (400 points)

  print("=" * 95)
  print("⚡ BSE SENSEX 0-DTE THURSDAY WEEKLY EXPIRY ENGINE (STOCKERA QUANT)")
  print(f"⏰ Scan Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
  print("=" * 95)

  # A. Fetch Active Expiry Date for SENSEX
  active_expiry = None
  try:
    exp_res = requests.post(
        "https://api.dhan.co/v2/optionchain/expirylist",
        headers=HEADERS,
        json={"UnderlyingScrip": scrip_id, "UnderlyingSeg": "IDX_I"},
        timeout=5,
    )
    if exp_res.status_code == 200:
      exp_list = exp_res.json().get("data", [])
      if exp_list:
        active_expiry = exp_list[0]
  except Exception as e:
    print(f"⚠️ Expiry list fetch note: {e}")

  if not active_expiry:
    active_expiry = "2026-09-17"

  # B. Fetch Live Option Chain
  url = "https://api.dhan.co/v2/optionchain"
  oc_res = requests.post(
      url,
      headers=HEADERS,
      json={
          "UnderlyingScrip": scrip_id,
          "UnderlyingSeg": "IDX_I",
          "Expiry": active_expiry,
      },
      timeout=8,
  )

  spot = 75000.0
  oc = {}
  if oc_res.status_code == 200:
    data = oc_res.json().get("data", {})
    spot = float(data.get("last_price", 75000.0))
    oc = data.get("oc", {})
  else:
    # Fallback to marketfeed
    q_res = requests.post(
        "https://api.dhan.co/v2/marketfeed/ltp",
        headers=HEADERS,
        json={"BSE_IDX": [51]},
    )
    if q_res.status_code == 200:
      spot = float(
          q_res.json()
          .get("data", {})
          .get("BSE_IDX", {})
          .get("51", {})
          .get("last_price", 75000.0)
      )

  atm_strike = int(round(spot / strike_step) * strike_step)
  wing_ce_strike = atm_strike + wing_offset
  wing_pe_strike = atm_strike - wing_offset

  # Calculate Straddle & Wing costs
  atm_data = oc.get(f"{atm_strike:.6f}", oc.get(str(atm_strike), {}))
  c_atm = float(atm_data.get("ce", {}).get("last_price", 280.0))
  p_atm = float(atm_data.get("pe", {}).get("last_price", 270.0))
  straddle_cost = round(c_atm + p_atm, 2)

  wing_ce_data = oc.get(f"{wing_ce_strike:.6f}", {})
  wing_pe_data = oc.get(f"{wing_pe_strike:.6f}", {})
  wing_ce_price = float(wing_ce_data.get("ce", {}).get("last_price", 45.0))
  wing_pe_price = float(wing_pe_data.get("pe", {}).get("last_price", 40.0))

  net_credit_pts = straddle_cost - (wing_ce_price + wing_pe_price)
  max_profit_per_lot = round(net_credit_pts * lot_size, 2)
  max_loss_per_lot = round((wing_offset - net_credit_pts) * lot_size, 2)

  # Calculate PCR
  tot_c_oi = sum(int(v.get("ce", {}).get("oi", 0)) for v in oc.values())
  tot_p_oi = sum(int(v.get("pe", {}).get("oi", 0)) for v in oc.values())
  pcr = round(tot_p_oi / tot_c_oi, 2) if tot_c_oi > 0 else 1.0

  print("\n1. BSE SENSEX 0-DTE MARKET PROFILE:")
  print(f"   • SENSEX Spot Price      : ₹{spot:,.2f}")
  print(f"   • Dynamic ATM Strike     : {atm_strike:,.0f}")
  print(f"   • Active Expiry Date     : {active_expiry} (Thursday Cycle)")
  print(f"   • ATM Straddle Premium   : ₹{straddle_cost:.2f}")
  print(f"   • Market PCR (OI)        : {pcr:.2f}")

  print("\n2. SENSEX 0-DTE IRON FLY STRUCTURE (20 LOT SIZE):")
  print(
      f"   • Short Core Straddle    : SELL {atm_strike} CE @ ~₹{c_atm:.2f} +"
      f" SELL {atm_strike} PE @ ~₹{p_atm:.2f}"
  )
  print(
      f"   • Protective Wings (400p): BUY {wing_ce_strike} CE @ ~₹{wing_ce_price:.2f}"
      f" + BUY {wing_pe_strike} PE @ ~₹{wing_pe_price:.2f}"
  )
  print(f"   • Net Premium Collected  : ₹{net_credit_pts:.2f} points")
  print(f"   • Max Profit Potential   : ₹{max_profit_per_lot:,.2f} per lot (20 Qty)")
  print(f"   • Max Loss Capped At     : ₹{max_loss_per_lot:,.2f} per lot")
  print(f"   • Breakevens             : [{atm_strike - net_credit_pts:,.2f} to {atm_strike + net_credit_pts:,.2f}]")

  # C. Save Build Sheet
  out_dir = r"C:\kite-agent\brain\30-strategies"
  sheet_path = os.path.join(out_dir, "SENSEX_0DTE_EXPIRY_BUILD_SHEET.md")

  lines = [
      "# BSE SENSEX 0-DTE Weekly Expiry Iron Fly — Stockera Quant",
      (
          f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'
          ' IST')} for Thursday Expiry {active_expiry}"
      ),
      (
          f"# Underlying: BSE SENSEX (BFO) | Lot Size: {lot_size} | Strike"
          f" Step: {strike_step} pts"
      ),
      "",
      "## Strategy Configuration:",
      "- Strategy: SENSEX 0-DTE Iron Fly",
      "- Target Profit: +₹2,000 per lot",
      "- Stop Loss: -₹2,000 per lot",
      f"- Core ATM Strike: {atm_strike}",
      f"- Wings: {wing_ce_strike} CE / {wing_pe_strike} PE",
      "",
      "## Execution Order (Margin Relief Priority):",
      (
          f"1. BUY BFO SENSEX {wing_ce_strike} CE (Expiry: {active_expiry}) |"
          f" 1 Lot ({lot_size} Qty)"
      ),
      (
          f"2. BUY BFO SENSEX {wing_pe_strike} PE (Expiry: {active_expiry}) |"
          f" 1 Lot ({lot_size} Qty)"
      ),
      (
          f"3. SELL BFO SENSEX {atm_strike} CE (Expiry: {active_expiry}) | 1"
          f" Lot ({lot_size} Qty)"
      ),
      (
          f"4. SELL BFO SENSEX {atm_strike} PE (Expiry: {active_expiry}) | 1"
          f" Lot ({lot_size} Qty)"
      ),
  ]

  with open(sheet_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

  print("=" * 95)
  print(f"🎉 SENSEX BUILD SHEET SAVED: {sheet_path}")
  print("=" * 95)


if __name__ == "__main__":
  run_sensex_expiry_engine()