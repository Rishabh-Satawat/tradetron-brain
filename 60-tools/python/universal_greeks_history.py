# =============================================================================
# File: 60-tools/python/universal_greeks_history.py
# Description: Smart Historical Greeks Engine (FINNIFTY, SENSEX, NIFTY, BANKNIFTY)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import argparse
import datetime
import os
import re
import sys
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

# 1. Load Secrets
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


# --- 2. Smart Symbol Resolver & Parser ---
def resolve_target_symbol(input_str, opt_type="CE"):
  """Resolves short keywords like 'SENSEX', 'FINNIFTY', 'NIFTY' into active Fyers contracts."""
  clean = input_str.upper().strip()

  spot_map = {
      "NIFTY": "NSE:NIFTY50-INDEX",
      "SENSEX": "BSE:SENSEX-INDEX",
      "FINNIFTY": "NSE:FINNIFTY-INDEX",
      "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
  }

  if clean in spot_map:
    spot_sym = spot_map[clean]
    print(
        f"🔍 Auto-detecting active ATM {clean} contract from live option"
        " chain..."
    )
    res = fyers.optionchain(
        data={"symbol": spot_sym, "strikecount": 2, "timestamp": ""}
    )
    if res.get("s") == "ok":
      chain = res.get("data", {})
      spot = float(chain.get("spotPrice", 0))
      opts = chain.get("optionsChain", [])
      valid_opts = [
          o for o in opts if o.get("strike_price") != -1 and o.get("symbol")
      ]
      target_opts = [
          o for o in valid_opts if o.get("option_type") == opt_type.upper()
      ]
      if not target_opts:
        target_opts = valid_opts
      if target_opts:
        atm_opt = min(
            target_opts, key=lambda x: abs(x.get("strike_price", 0) - spot)
        )
        resolved_sym = atm_opt.get("symbol")
        print(f"👉 Selected Active Contract: {resolved_sym}")
        return resolved_sym

  # If already a full symbol, return as is
  return input_str.strip()


def parse_option_symbol(symbol):
  clean = symbol.split(":")[-1].strip()

  spot_map = {
      "NIFTY": "NSE:NIFTY50-INDEX",
      "BANKNIFTY": "NSE:NIFTYBANK-INDEX",
      "FINNIFTY": "NSE:FINNIFTY-INDEX",
      "SENSEX": "BSE:SENSEX-INDEX",
  }

  underlying = "NIFTY"
  for u in ["BANKNIFTY", "FINNIFTY", "SENSEX", "NIFTY"]:
    if clean.startswith(u):
      underlying = u
      break

  spot_symbol = spot_map.get(underlying, "NSE:NIFTY50-INDEX")
  opt_type = "CE" if clean.endswith("CE") else "PE"

  # Weekly format: {UNDER}{YY}{M}{DD}{STRIKE}{CE/PE}
  m_weekly = re.match(
      r"^([A-Za-z]+)(\d{2})([1-9OND])(\d{2})(\d{4,5})(CE|PE)$", clean
  )
  if m_weekly:
    _, yy, m_code, dd, strike, _ = m_weekly.groups()
    month_map = {
        "1": 1,
        "2": 2,
        "3": 3,
        "4": 4,
        "5": 5,
        "6": 6,
        "7": 7,
        "8": 8,
        "9": 9,
        "O": 10,
        "N": 11,
        "D": 12,
    }
    month = month_map.get(m_code, 9)
    expiry_dt = datetime.datetime(
        2000 + int(yy),
        month,
        int(dd),
        15,
        30,
        tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
    )
    return underlying, spot_symbol, float(strike), opt_type, expiry_dt

  # Monthly format: {UNDER}{YY}{MMM}{STRIKE}{CE/PE}
  m_monthly = re.match(
      r"^([A-Za-z]+)(\d{2})([A-Za-z]{3})(\d{4,5})(CE|PE)$", clean
  )
  if m_monthly:
    _, yy, m_str, strike, _ = m_monthly.groups()
    expiry_dt = datetime.datetime(
        2000 + int(yy),
        9,
        29,
        15,
        30,
        tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
    )
    return underlying, spot_symbol, float(strike), opt_type, expiry_dt

  digits = re.findall(r"\d+", clean)
  strike_num = float(digits[-1]) if digits else 24000.0
  return (
      underlying,
      spot_symbol,
      strike_num,
      opt_type,
      datetime.datetime(
          2026,
          9,
          10,
          15,
          30,
          tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
      ),
  )


# --- 3. Black-76 Greeks & Numerical Solver ---
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


def get_candles(symbol, resolution, from_date, to_date):
  data = {
      "symbol": symbol,
      "resolution": str(resolution),
      "date_format": "1",
      "range_from": from_date,
      "range_to": to_date,
      "cont_flag": "1",
  }
  res = fyers.history(data=data)
  if res.get("s") != "ok":
    print(f"❌ Fyers Error for {symbol}: {res.get('message')}")
    return pd.DataFrame()

  df = pd.DataFrame(
      res.get("candles", []),
      columns=["epoch", "open", "high", "low", "close", "volume"],
  )
  if df.empty:
    return df
  df["datetime"] = (
      pd.to_datetime(df["epoch"], unit="s")
      .dt.tz_localize("UTC")
      .dt.tz_convert("Asia/Kolkata")
  )
  return df


# --- 4. Main Execution Function ---
def run_universal_greeks(symbol_input, from_date, to_date=None, resolution="15"):
  # 1. Resolve to actual active symbol
  symbol = resolve_target_symbol(symbol_input)
  from_date_str = str(from_date).strip()
  resolution = str(resolution).strip()

  if (
      to_date is None
      or str(to_date).strip() == ""
      or str(to_date).strip().lower() == "none"
  ):
    d = datetime.date.fromisoformat(from_date_str)
    query_to_date = (d + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    is_single_day = True
  else:
    query_to_date = str(to_date).strip()
    is_single_day = False

  underlying, spot_symbol, strike, opt_type, expiry_dt = parse_option_symbol(
      symbol
  )

  print("=" * 115)
  print(f"⚡ UNIVERSAL GREEKS ENGINE | Resolution: {resolution}m")
  print(
      f"📌 Option Symbol : {symbol} (Strike: {strike:,.0f} {opt_type} |"
      f" Expiry: {expiry_dt.strftime('%Y-%m-%d')})"
  )
  print(f"📌 Spot Symbol   : {spot_symbol}")
  print(f"📅 Date Window   : {from_date_str} to {to_date or from_date_str}")
  print("=" * 115)

  df_opt = get_candles(symbol, resolution, from_date_str, query_to_date)
  df_spot = get_candles(spot_symbol, resolution, from_date_str, query_to_date)

  if df_opt.empty or df_spot.empty:
    print(
        "❌ No candle data returned. Ensure contract was actively trading on"
        f" {from_date_str}."
    )
    return

  if is_single_day:
    df_opt = df_opt[
        df_opt["datetime"].dt.strftime("%Y-%m-%d") == from_date_str
    ].copy()
    df_spot = df_spot[
        df_spot["datetime"].dt.strftime("%Y-%m-%d") == from_date_str
    ].copy()

  df_merged = pd.merge(
      df_opt,
      df_spot[["epoch", "close"]],
      on="epoch",
      suffixes=("_opt", "_spot"),
  )
  if df_merged.empty:
    print("❌ Timestamp alignment failed between option and spot.")
    return

  r = 0.0675
  results = []
  for _, row in df_merged.iterrows():
    candle_dt = row["datetime"]
    T_years = max(
        (expiry_dt - candle_dt).total_seconds() / (365.0 * 86400.0), 0.001
    )
    F = row["close_spot"]
    P = row["close_opt"]

    iv = solve_iv(P, F, strike, T_years, r=r, option_type=opt_type)
    g = calculate_greeks(F, strike, T_years, r, iv, option_type=opt_type)

    results.append({
        "datetime": candle_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "spot_price": F,
        "opt_open": row["open"],
        "opt_high": row["high"],
        "opt_low": row["low"],
        "opt_close": P,
        "volume": row["volume"],
        "iv_pct": round(iv * 100, 2),
        "delta": g["delta"],
        "gamma": g["gamma"],
        "theta": g["theta"],
        "vega": g["vega"],
    })

  res_df = pd.DataFrame(results)

  print(f"✅ Processed {len(res_df)} total {resolution}-minute candles!")
  print("-" * 115)
  print(
      f"{'Date & Time (IST)':<20} | {'Spot':>9} | {'Opt Close':>9} |"
      f" {'IV %':>7} | {'Delta':>7} | {'Gamma':>9} | {'Theta':>7} |"
      f" {'Vega':>7} | {'Volume':>10}"
  )
  print("-" * 115)

  preview = (
      pd.concat([res_df.head(4), res_df.tail(4)])
      if len(res_df) > 8
      else res_df
  )
  for _, r in preview.iterrows():
    print(
        f"{r['datetime']:<20} | {r['spot_price']:>9.2f} | {r['opt_close']:>9.2f}"
        f" | {r['iv_pct']:>7.2f} | {r['delta']:>7.4f} | {r['gamma']:>9.6f} |"
        f" {r['theta']:>7.2f} | {r['vega']:>7.2f} | {r['volume']:>10,d}"
    )
  print("=" * 115)

  out_dir = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
  os.makedirs(out_dir, exist_ok=True)
  clean_sym = symbol.replace(":", "_")
  filename = f"{clean_sym}_{resolution}m_{from_date_str}.csv"
  out_path = os.path.join(out_dir, filename)
  res_df.to_csv(out_path, index=False)
  print(f"📁 Dataset saved to:\n   {out_path}\n")


if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Universal Greeks History Engine")
  parser.add_argument("symbol", nargs="?", default="NIFTY")
  parser.add_argument("from_date", nargs="?", default="2026-09-03")
  parser.add_argument("resolution", nargs="?", default="15")
  parser.add_argument("to_date", nargs="?", default=None)

  args = parser.parse_args()

  run_universal_greeks(
      symbol_input=args.symbol,
      from_date=args.from_date,
      to_date=args.to_date,
      resolution=args.resolution,
  )