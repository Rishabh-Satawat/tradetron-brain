# =============================================================================
# File: 60-tools/python/fyers_option_chain.py
# Description: Live SENSEX & NIFTY Option Chain with Configurable Strike Depth
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
import sys
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

if not os.path.exists(SECRETS_PATH) or not os.path.exists(TOKEN_PATH):
  print("❌ Error: Missing credentials or access token. Run fyers_auth.py first.")
  exit(1)

load_dotenv(SECRETS_PATH)
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(TOKEN_PATH) as f:
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


def fetch_option_chain(symbol="NSE:NIFTY50-INDEX", strike_count=20):
  # Defensive safety check: if a list is passed, extract the item
  if isinstance(strike_count, list):
    strike_count = (
        strike_count
        if len(strike_count) > 1
        else (strike_count[0] if strike_count else 20)
    )

  # Handle "all" or specific integer strike count
  if str(strike_count).lower() in ("0", "all", ""):
    strikecount_param = ""
    display_depth = "ALL AVAILABLE"
  else:
    try:
      strikecount_param = int(strike_count)
      display_depth = f"±{strikecount_param}"
    except Exception:
      strikecount_param = 20
      display_depth = "±20"

  print("\n" + "=" * 105)
  print(f"⚡ FYERS v3 OPTION CHAIN (Depth: {display_depth} Strikes): {symbol}")
  print("=" * 105)

  data = {"symbol": symbol, "strikecount": strikecount_param, "timestamp": ""}
  res = fyers.optionchain(data=data)

  if res.get("s") != "ok":
    print(f"❌ Error fetching chain: {res.get('message')}")
    return

  chain_data = res.get("data", {})
  options_list = chain_data.get("optionsChain", [])

  if not options_list:
    print("❌ No options data returned.")
    return

  spot_price = float(chain_data.get("spotPrice", 0))
  calls = {}
  puts = {}

  for item in options_list:
    strike = item.get("strike_price")
    opt_type = item.get("option_type")

    if strike == -1:
      if spot_price == 0:
        spot_price = get_val(
            item, ["ltp", "prev_close_price", "close_price", "o"], default=0.0
        )
      continue

    if opt_type == "CE":
      calls[strike] = item
    elif opt_type == "PE":
      puts[strike] = item

  all_strikes = sorted(list(set(list(calls.keys()) + list(puts.keys()))))
  expiry = chain_data.get("expiry", "Current")

  print(
      f"📈 Underlying Spot : ₹{spot_price:,.2f} | Total Strikes Displayed:"
      f" {len(all_strikes)}"
  )
  print(f"📅 Active Expiry   : {expiry}")
  print("-" * 105)
  print(
      f"{'Call OI':>10} | {'Call IV':>8} | {'Delta':>7} | {'Call Price':>10} |"
      f" {'STRIKE':^8} | {'Put Price':>10} | {'Delta':>7} | {'Put IV':>8} |"
      f" {'Put OI':>10}"
  )
  print("-" * 105)

  total_call_oi = 0
  total_put_oi = 0

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

    c_iv = get_val(c, ["iv"], default=0.0)
    p_iv = get_val(p, ["iv"], default=0.0)

    c_delta = get_val(c, ["delta"], default=0.0)
    p_delta = get_val(p, ["delta"], default=0.0)

    is_atm = "➡️" if abs(strike - spot_price) < 30 else "  "

    print(
        f"{c_oi:>10,d} | {c_iv:>8.2f} | {c_delta:>7.2f} | {c_price:>10.2f} |"
        f" {is_atm}{strike:^6.0f} | {p_price:>10.2f} | {p_delta:>7.2f} |"
        f" {p_iv:>8.2f} | {p_oi:>10,d}"
    )

  pcr = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0.0
  print("-" * 105)
  print(
      f"📊 Total Call OI: {total_call_oi:,d} | Total Put OI: {total_put_oi:,d}"
      f" | Put-Call Ratio (PCR): {pcr:.2f}"
  )
  print("=" * 105)


if __name__ == "__main__":
  # Safely read command line argument if supplied
  user_depth = 20
  if len(sys.argv) > 1:
    user_depth = sys.argv

  fetch_option_chain("NSE:NIFTY50-INDEX", strike_count=user_depth)
  fetch_option_chain("BSE:SENSEX-INDEX", strike_count=user_depth)