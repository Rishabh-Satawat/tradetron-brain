# =============================================================================
# File: 60-tools/python/nifty_expiry_0dte_engine.py
# Description: NIFTY 50 0-DTE Tuesday Weekly Expiry Strategy & Execution Engine
# Tailored for: Tuesday Expiries (50-Point Strike Steps, 65 Lot Size)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import json
import os
import sys
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

# Load environment
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

if not os.path.exists(TOKEN_PATH):
  print(f"❌ Error: {TOKEN_PATH} missing. Run start_desk.ps1 first.")
  sys.exit(1)

with open(TOKEN_PATH) as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


def get_val(d, keys, default=0.0):
  for k in keys:
    v = d.get(k)
    if v is not None and v != "":
      return float(v)
  return default


def run_nifty_expiry_engine():
  symbol = "NSE:NIFTY50-INDEX"
  lot_size = 65
  strike_step = 50

  print("=" * 95)
  print("⚡ NIFTY 50 0-DTE WEEKLY EXPIRY EXECUTION ENGINE (TUESDAY CYCLE)")
  print(
      f"⏰ Scan Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}"
  )
  print("=" * 95)

  # 1. Fetch Verified NIFTY Spot Price
  spot = None
  q = fyers.quotes(data={"symbols": symbol})
  if q.get("s") == "ok":
    d = q.get("d", [])
    if d and isinstance(d, list):
      v = d[0].get("v", {})
      lp = v.get("lp") or v.get("prev_close_price") or v.get("cmd", {}).get("c")
      if lp and float(lp) > 0:
        spot = float(lp)

  # 2. Fetch NIFTY Option Chain
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": 15, "timestamp": ""}
  )
  if res.get("s") != "ok":
    print(f"❌ Error querying Fyers chain: {res.get('message')}")
    sys.exit(1)

  chain_data = res.get("data", {})
  options = chain_data.get("optionsChain", [])
  expiry = chain_data.get("expiry", "Current")

  if spot is None or spot <= 0:
    for item in options:
      if item.get("strike_price") == -1:
        lp = item.get("ltp") or item.get("close_price")
        if lp and float(lp) > 0:
          spot = float(lp)
          break

  if spot is None or spot <= 0:
    spot = 23635.10  # Fallback reference

  atm_strike = int(round(spot / strike_step) * strike_step)

  calls, puts = {}, {}
  for item in options:
    k = item.get("strike_price")
    if k == -1:
      continue
    if item.get("option_type") == "CE":
      calls[k] = item
    elif item.get("option_type") == "PE":
      puts[k] = item

  all_strikes = sorted(list(set(list(calls.keys()) + list(puts.keys()))))
  tot_call_oi, tot_put_oi = 0, 0

  for k in all_strikes:
    c = calls.get(k, {})
    p = puts.get(k, {})
    tot_call_oi += int(get_val(c, ["oi"], default=0))
    tot_put_oi += int(get_val(p, ["oi"], default=0))

  pcr = (tot_put_oi / tot_call_oi) if tot_call_oi > 0 else 1.0

  # ATM Straddle Cost
  c_atm = calls.get(atm_strike, {})
  p_atm = puts.get(atm_strike, {})
  c_price = get_val(
      c_atm, ["ltp", "prev_close_price", "close_price"], default=120.0
  )
  p_price = get_val(
      p_atm, ["ltp", "prev_close_price", "close_price"], default=110.0
  )
  straddle_cost = c_price + p_price
  expected_move_pct = (straddle_cost / spot) * 100.0 if spot > 0 else 0.0

  # 3. 0-DTE Iron Fly Structure (250-point wings = 5 strike steps)
  wing_offset_points = 250
  wing_ce_strike = atm_strike + wing_offset_points
  wing_pe_strike = atm_strike - wing_offset_points

  wing_ce_price = get_val(
      calls.get(wing_ce_strike, {}), ["ltp", "close_price"], default=15.0
  )
  wing_pe_price = get_val(
      puts.get(wing_pe_strike, {}), ["ltp", "close_price"], default=12.0
  )
  net_credit_pts = straddle_cost - (wing_ce_price + wing_pe_price)

  max_profit_per_lot = round(net_credit_pts * lot_size, 2)
  max_loss_per_lot = round((wing_offset_points - net_credit_pts) * lot_size, 2)

  target_pnl = 2500.0
  sl_pnl = -2500.0

  print(f"\n1. NIFTY 0-DTE EXPIRY MARKET PROFILE:")
  print(
      f"   • NIFTY 50 Spot Price    : ₹{spot:,.2f} (True ATM:"
      f" {atm_strike:,.0f})"
  )
  print(f"   • Active Expiry Cycle    : {expiry} (Tuesday Expiry)")
  print(
      f"   • ATM Straddle Premium   : ₹{straddle_cost:.2f} (Expected Move:"
      f" ±{expected_move_pct:.2f}%)"
  )
  print(
      f"   • Market PCR (OI)        : {pcr:.2f}"
      f" ({'Bullish Support' if pcr >= 1.0 else 'Call Writer Heavy'})"
  )

  print(f"\n2. NIFTY 0-DTE IRON FLY V6 STRUCTURE:")
  print(
      f"   • Short Straddle Core    : SELL {atm_strike} CE @ ~₹{c_price:.2f} +"
      f" SELL {atm_strike} PE @ ~₹{p_price:.2f}"
  )
  print(
      f"   • Protective Wings (250p): BUY {wing_ce_strike} CE @ ~₹{wing_ce_price:.2f}"
      f" + BUY {wing_pe_strike} PE @ ~₹{wing_pe_price:.2f}"
  )
  print(f"   • Net Premium Collected  : ₹{net_credit_pts:.2f} points per lot")
  print(
      f"   • Max Profit Potential   : ₹{max_profit_per_lot:,.2f} per lot (65"
      " Qty)"
  )
  print(
      f"   • Max Capital at Risk    : ₹{max_loss_per_lot:,.2f} per lot (Capped"
      " by Wings)"
  )
  print(
      f"   • Execution Strategy     : Target: +₹{target_pnl:,.0f} | Stop Loss:"
      f" -₹{abs(sl_pnl):,.0f}"
  )

  # 4. Save Clean Markdown Build Sheet
  out_dir = r"C:\kite-agent\brain\30-strategies"
  os.makedirs(out_dir, exist_ok=True)
  build_sheet_path = os.path.join(
      out_dir, "NIFTY_0DTE_EXPIRY_BUILD_SHEET.md"
  )

  lines = [
      "# NIFTY 50 0-DTE Weekly Expiry Iron Fly V6 — Tradetron Build Sheet",
      (
          f"# Generated on"
          f" {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')} for"
          " Tuesday Expiry"
      ),
      (
          f"# Underlying: NSE NIFTY 50 (NFO) | Lot Size: {lot_size} | Strike"
          f" Step: {strike_step} points"
      ),
      "",
      "## Strategy Profile:",
      "- Strategy Name: NIFTY 0-DTE Expiry Iron Fly V6",
      "- Target Profit: +₹2,500 * Multiplier",
      "- Stop Loss: -₹2,500 * Multiplier",
      "- Intraday Time Exit: 03:10 PM IST",
      f"- Dynamic ATM Anchor: {atm_strike}",
      (
          f"- Protective Wings: +250 pts ({wing_ce_strike} CE) / -250 pts"
          f" ({wing_pe_strike} PE)"
      ),
      "",
      "---",
      "",
      "## SET 1 — ENTRY CONDITION (0-DTE Tuesday Expiry Rangebound):",
      "```text",
      "( Positions Detail ( 'Entry' , 'All' , 'All' , 'NIFTY 50' ) == Number ("
      " '0' ) )",
      (
          "AND ( Days Difference (D2-D1) ( Current Week Expiry ( 'NIFTY 50' ,"
          " '0' ) , Today ( 'NSE' ) ) == Number ( '0' ) )"
      ),
      "AND ( Time ( 'NSE' ) >= Number ( '930' ) )",
      "AND ( Time ( 'NSE' ) <= Number ( '1400' ) )",
      (
          "AND ( Position ( ADX ( Symbol ( Instrument Name ( 'NFO,NIFTY"
          " 50,,,,,' ) ) , '15m' , 'All' , '14' ) , '-1' ) <= Number ( '25' )"
          " )"
      ),
      "```",
      "",
      "---",
      "",
      "## POSITION BUILDER (4 LEGS — MARGIN HEDGED SEQUENCE):",
      (
          "> Note: On entry, execute BUY wing legs (Leg 3 & 4) first to get"
          " SEBI margin relief before writing ATM legs!"
      ),
      "",
      (
          "| Leg # | Action | Exchange | Underlying | Expiry Selector | Strike"
          " Selection | Lots | Type | Order Type | Product |"
      ),
      (
          "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |"
          " :---: | :---: |"
      ),
      (
          f"| Leg 1 | SELL | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( 0"
          f" ) | 1 ({lot_size} Qty) | CE | Market | NRML |"
      ),
      (
          f"| Leg 2 | SELL | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( 0"
          f" ) | 1 ({lot_size} Qty) | PE | Market | NRML |"
      ),
      (
          f"| Leg 3 | BUY  | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( +5"
          f" ) | 1 ({lot_size} Qty) | CE | Market | NRML |"
      ),
      (
          f"| Leg 4 | BUY  | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( -5"
          f" ) | 1 ({lot_size} Qty) | PE | Market | NRML |"
      ),
      "",
      "---",
      "",
      "## SET 1 — UNIVERSAL EXIT CONDITIONS:",
      "```text",
      (
          "( PNL ( 'strategy_id' , 'run_counter' ) >= Number ( '2500' ) *"
          " Multiplier ( 'strategy_id' ) )"
      ),
      (
          "OR ( PNL ( 'strategy_id' , 'run_counter' ) <= Number ( '-2500' ) *"
          " Multiplier ( 'strategy_id' ) )"
      ),
      "OR ( Time ( 'NSE' ) >= Number ( '1510' ) )",
      "```",
      "",
      "---",
      "",
      "## ADVANCED SETTINGS:",
      "- Price Execution: Market Price",
      "- Execution Timeout: 60 Seconds",
      "- Exit At Market Price: YES",
      "- Exit Shorts First: YES",
      "- Check Conditions Every: Continuously",
      "- Reactivate on exit after: Never",
      "- Capital Required: ₹1,80,000",
      "- Strategy Visibility: Private",
      "",
  ]

  with open(build_sheet_path, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))

  print("\n" + "=" * 95)
  print("🎉 NIFTY 0-DTE BUILD SHEET EXPORTED SUCCESSFULLY!")
  print(f"📁 Path: {build_sheet_path}")
  print("=" * 95)


if __name__ == "__main__":
  run_nifty_expiry_engine()