# =============================================================================
# File: 60-tools/python/fetch_hourly_greeks.py
# Description: Fetch 3rd Sep 2026 Hourly Candles & Compute Black-76 Greeks
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm

# Load secrets
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


# --- Black-76 Model & Greeks Solver ---
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


def get_hourly_candles(symbol, from_date="2026-09-03", to_date="2026-09-04"):
  data = {
      "symbol": symbol,
      "resolution": "60",
      "date_format": "1",
      "range_from": from_date,
      "range_to": to_date,
      "cont_flag": "1",
  }
  res = fyers.history(data=data)
  if res.get("s") != "ok":
    print(f"❌ Error fetching {symbol}: {res.get('message')}")
    return pd.DataFrame()

  df = pd.DataFrame(
      res.get("candles", []),
      columns=["epoch", "open", "high", "low", "close", "volume"],
  )
  df["datetime"] = (
      pd.to_datetime(df["epoch"], unit="s")
      .dt.tz_localize("UTC")
      .dt.tz_convert("Asia/Kolkata")
  )
  # Filter strictly for 2026-09-03
  df = df[df["datetime"].dt.strftime("%Y-%m-%d") == from_date].copy()
  return df


def main():
  target_date = "2026-09-03"
  option_symbol = (
      "NSE:NIFTY2690823900CE"  # 23,900 CE ATM Strike expiring 08-Sep-2026
  )
  spot_symbol = "NSE:NIFTY50-INDEX"
  strike = 23900.0
  opt_type = "CE"

  print("=" * 105)
  print(f"⚡ HISTORICAL HOURLY DATA & GREEKS MATRIX FOR {target_date}")
  print(f"📌 Option Strike : {option_symbol} (Strike: {strike:,.0f} {opt_type})")
  print(f"📌 Underlying    : {spot_symbol}")
  print("=" * 105)

  # Fetch option and spot hourly candles
  df_opt = get_hourly_candles(
      option_symbol, from_date=target_date, to_date="2026-09-04"
  )
  df_spot = get_hourly_candles(
      spot_symbol, from_date=target_date, to_date="2026-09-04"
  )

  if df_opt.empty or df_spot.empty:
    print("❌ Failed to retrieve hourly data.")
    return

  # Merge on epoch timestamp
  df_merged = pd.merge(
      df_opt,
      df_spot[["epoch", "close"]],
      on="epoch",
      suffixes=("_opt", "_spot"),
  )

  expiry_dt = datetime.datetime(
      2026, 9, 8, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=5.5))
  )
  r = 0.0675

  results = []
  for _, row in df_merged.iterrows():
    candle_dt = row["datetime"]
    T_years = max(
        (expiry_dt - candle_dt).total_seconds() / (365.0 * 86400.0), 0.001
    )
    F = row["close_spot"]
    P = row["close_opt"]

    # Solve IV & Greeks
    iv = solve_iv(P, F, strike, T_years, r=r, option_type=opt_type)
    greeks = calculate_greeks(F, strike, T_years, r, iv, option_type=opt_type)

    results.append({
        "time_ist": candle_dt.strftime("%H:%M:%S"),
        "spot_price": F,
        "opt_open": row["open"],
        "opt_high": row["high"],
        "opt_low": row["low"],
        "opt_close": P,
        "volume": row["volume"],
        "iv_pct": round(iv * 100, 2),
        "delta": greeks["delta"],
        "gamma": greeks["gamma"],
        "theta": greeks["theta"],
        "vega": greeks["vega"],
    })

  res_df = pd.DataFrame(results)

  # Print formatted table
  print(
      f"{'Time (IST)':<10} | {'Spot':>9} | {'Opt Close':>9} | {'IV %':>7} |"
      f" {'Delta':>7} | {'Gamma':>9} | {'Theta':>7} | {'Vega':>7} |"
      f" {'Volume':>10}"
  )
  print("-" * 105)
  for _, r in res_df.iterrows():
    print(
        f"{r['time_ist']:<10} | {r['spot_price']:>9.2f} | {r['opt_close']:>9.2f}"
        f" | {r['iv_pct']:>7.2f} | {r['delta']:>7.4f} | {r['gamma']:>9.6f} |"
        f" {r['theta']:>7.2f} | {r['vega']:>7.2f} | {r['volume']:>10,d}"
    )
  print("=" * 105)

  # Save to CSV
  out_path = rf"C:\kite-agent\brain\20-market-data\datasets\option_history\NIFTY_23900CE_hourly_{target_date}.csv"
  res_df.to_csv(out_path, index=False)
  print(f"📁 Full dataset saved to: {out_path}")


if __name__ == "__main__":
  main()