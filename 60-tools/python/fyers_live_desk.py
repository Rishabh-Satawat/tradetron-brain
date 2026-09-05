# =============================================================================
# File: 60-tools/python/fyers_live_desk.py
# Description: Unified Self-Healing Fyers Live Option Chain & Greeks Desk
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
import sys
import threading
import time
import urllib.parse
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
from scipy.optimize import brentq
from scipy.stats import norm

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

if not os.path.exists(SECRETS_PATH):
  print(f"❌ Error: {SECRETS_PATH} not found.")
  exit(1)

load_dotenv(SECRETS_PATH)
APP_ID = os.getenv("FYERS_APP_ID", "UFCAZKDNZB-100").strip()
SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "").strip()
REDIRECT_URI = os.getenv(
    "FYERS_REDIRECT_URI", "http://127.0.0.1:5000/fyers/callback"
).strip()

captured_auth_code = None


# --- 1. OAuth Auto-Capture Server ---
class FyersCallbackHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    global captured_auth_code
    parsed_path = urllib.parse.urlparse(self.path)
    query_params = urllib.parse.parse_qs(parsed_path.query)

    if "auth_code" in query_params:
      captured_auth_code = query_params["auth_code"][0].strip()
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(b"""
                <html><body style="font-family:sans-serif; text-align:center; padding-top:50px; background:#0f172a; color:#fff;">
                    <h1 style="color:#22c55e;">&#10004; Authentication Successful!</h1>
                    <p>Token exchanged. You can close this tab now.</p>
                </body></html>
            """)
    else:
      self.send_response(400)
      self.end_headers()

  def log_message(self, format, *args):
    return


def login_and_get_fresh_token():
  global captured_auth_code
  captured_auth_code = None
  print("\n🔑 Token expired or missing. Initiating automatic Fyers login...")

  server = HTTPServer(("127.0.0.1", 5000), FyersCallbackHandler)
  threading.Thread(target=server.serve_forever, daemon=True).start()

  session = fyersModel.SessionModel(
      client_id=APP_ID,
      secret_key=SECRET_KEY,
      redirect_uri=REDIRECT_URI,
      response_type="code",
      grant_type="authorization_code",
  )
  auth_url = session.generate_authcode()
  print("🌐 Opening browser for authorization...")
  webbrowser.open(auth_url)

  timeout = 90
  start_time = time.time()
  while captured_auth_code is None:
    if time.time() - start_time > timeout:
      print("❌ Timeout waiting for browser login.")
      exit(1)
    time.sleep(0.5)

  session.set_token(captured_auth_code)
  response = session.generate_token()

  if response.get("s") == "ok":
    real_access_token = response.get("access_token")
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
      f.write(real_access_token)
    print(
        f"🎉 Fresh Access Token generated & saved ({real_access_token[:12]}...)!"
    )
    return real_access_token
  else:
    print(f"❌ Token exchange failed: {response}")
    exit(1)


# --- 2. Black-76 Greeks Engine ---
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


# --- 3. Option Chain Engine ---
def display_chain(fyers, symbol="NSE:NIFTY50-INDEX", strike_count=10):
  data = {"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  res = fyers.optionchain(data=data)

  if res.get("s") != "ok":
    print(f"❌ Error fetching {symbol}: {res.get('message')}")
    return False

  chain_data = res.get("data", {})
  options_list = chain_data.get("optionsChain", [])
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
  atm_strike = (
      min(all_strikes, key=lambda x: abs(x - spot_price))
      if all_strikes
      else spot_price
  )
  T_years = max(2.5 / 365.0, 0.002)

  total_call_oi, total_put_oi = 0, 0
  atm_straddle = 0.0

  print("\n" + "=" * 105)
  print(
      f"⚡ FYERS LIVE OPTION MATRIX: {symbol} | Spot: ₹{spot_price:,.2f} | Expiry:"
      f" {chain_data.get('expiry', 'Current')}"
  )
  print("=" * 105)
  print(
      f"{'Call OI':>10} | {'Call IV':>8} | {'Delta':>7} | {'Call LTP':>10} |"
      f" {'STRIKE':^8} | {'Put LTP':>10} | {'Delta':>7} | {'Put IV':>8} |"
      f" {'Put OI':>10}"
  )
  print("-" * 105)

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

    # Dual-Engine: Fyers Greek -> Fallback Black-76 (Fixed Keyword Args)
    c_iv_api = get_val(c, ["iv"], default=0.0)
    p_iv_api = get_val(p, ["iv"], default=0.0)

    c_iv = (
        c_iv_api / 100.0
        if c_iv_api > 0
        else solve_iv(
            c_price, spot_price, strike, T_years, r=0.0675, option_type="CE"
        )
    )
    p_iv = (
        p_iv_api / 100.0
        if p_iv_api > 0
        else solve_iv(
            p_price, spot_price, strike, T_years, r=0.0675, option_type="PE"
        )
    )

    c_g = (
        {"delta": get_val(c, ["delta"])}
        if c_iv_api > 0
        else calculate_greeks(
            spot_price, strike, T_years, 0.0675, c_iv, option_type="CE"
        )
    )
    p_g = (
        {"delta": get_val(p, ["delta"])}
        if p_iv_api > 0
        else calculate_greeks(
            spot_price, strike, T_years, 0.0675, p_iv, option_type="PE"
        )
    )

    if strike == atm_strike:
      atm_straddle = c_price + p_price

    is_atm = "➡️" if strike == atm_strike else "  "
    print(
        f"{c_oi:>10,d} | {c_iv * 100:>8.2f} | {c_g['delta']:>7.2f} |"
        f" {c_price:>10.2f} | {is_atm}{strike:^6.0f} | {p_price:>10.2f} |"
        f" {p_g['delta']:>7.2f} | {p_iv * 100:>8.2f} | {p_oi:>10,d}"
    )

  pcr = (total_put_oi / total_call_oi) if total_call_oi > 0 else 0.0
  print("-" * 105)
  print(
      f"📊 Total Call OI: {total_call_oi:,d} | Total Put OI: {total_put_oi:,d}"
      f" | PCR: {pcr:.2f}"
  )
  print(
      f"🪙 ATM Straddle : ₹{atm_straddle:.2f} (Expected Move:"
      f" ±{(atm_straddle / spot_price) * 100:.2f}%)"
  )
  print("=" * 105)
  return True


def main():
  print("=" * 70)
  print("⚡ TRADETRON BRAIN — FYERS LIVE MARKET DESK")
  print("=" * 70)

  # Check existing token
  token = None
  if os.path.exists(TOKEN_PATH):
    with open(TOKEN_PATH, "r", encoding="utf-8") as f:
      token = f.read().strip()

  fyers = None
  if token:
    fyers = fyersModel.FyersModel(
        client_id=APP_ID, is_async=False, token=token, log_path=""
    )
    prof = fyers.get_profile()
    if prof.get("s") != "ok":
      print("⚠️ Existing token rejected by Fyers. Generating fresh session...")
      fyers = None

  if fyers is None:
    fresh_token = login_and_get_fresh_token()
    fyers = fyersModel.FyersModel(
        client_id=APP_ID, is_async=False, token=fresh_token, log_path=""
    )

  prof = fyers.get_profile()
  print(
      f"👤 Connected: {prof.get('data', {}).get('name')} | Client ID:"
      f" {prof.get('data', {}).get('fy_id')}"
  )

  # Display live chains
  display_chain(fyers, "NSE:NIFTY50-INDEX", strike_count=10)
  display_chain(fyers, "BSE:SENSEX-INDEX", strike_count=10)


if __name__ == "__main__":
  main()