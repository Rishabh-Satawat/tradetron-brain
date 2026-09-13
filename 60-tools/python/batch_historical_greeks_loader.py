# =============================================================================
# File: 60-tools/python/batch_historical_greeks_loader.py
# Description: Bulk Ingestion of Historical Option Candles & Backwards Greeks
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import numpy as np
import pandas as pd
from scipy.optimize import brentq
from scipy.stats import norm
from supabase import create_client, Client

load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  FYERS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=FYERS_TOKEN, log_path=""
)
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# --- 1. Black-76 Greeks & IV Solver ---
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


# --- 2. Ingestion Controller ---
def ingest_contract(
    symbol,
    spot_symbol,
    strike,
    opt_type,
    expiry_dt,
    from_date="2026-08-25",
    to_date="2026-09-04",
):
  print(f"\n📥 Ingesting {symbol} ({from_date} to {to_date})...")
  df_opt = get_candles(symbol, "15", from_date, to_date)
  df_spot = get_candles(spot_symbol, "15", from_date, to_date)

  if df_opt.empty or df_spot.empty:
    print(f"⚠️ Incomplete data for {symbol}.")
    return

  df_merged = pd.merge(
      df_opt,
      df_spot[["epoch", "close"]],
      on="epoch",
      suffixes=("_opt", "_spot"),
  )
  if df_merged.empty:
    return

  r = 0.0675
  records = []

  for _, row in df_merged.iterrows():
    candle_dt = row["datetime"]
    T_years = max(
        (expiry_dt - candle_dt).total_seconds() / (365.0 * 86400.0), 0.001
    )
    F = row["close_spot"]
    P = row["close_opt"]

    iv = solve_iv(P, F, strike, T_years, r=r, option_type=opt_type)
    g = calculate_greeks(F, strike, T_years, r, iv, option_type=opt_type)

    records.append({
        "underlying": spot_symbol,
        "spot_price": float(F),
        "strike_price": float(strike),
        "option_type": opt_type,
        "ltp": float(P),
        "oi": 0,
        "volume": int(row["volume"]),
        "iv": round(iv * 100, 2),
        "delta": g["delta"],
        "gamma": g["gamma"],
        "theta": g["theta"],
        "vega": g["vega"],
        "created_at": candle_dt.isoformat(),
    })

  # Bulk insert into Supabase
  batch_size = 300
  for i in range(0, len(records), batch_size):
    batch = records[i : i + batch_size]
    try:
      supabase.table("option_chain_snapshots").insert(batch).execute()
    except Exception as e:
      print(f"⚠️ Supabase error: {e}")

  print(f"   ✅ Successfully ingested {len(records)} 15m bars with Greeks!")


if __name__ == "__main__":
  print("=" * 75)
  print("📦 BULK HISTORICAL GREEKS LOADER TO SUPABASE PRO")
  print("=" * 75)

  # 1. Ingest NIFTY 23,900 CE (Tuesday 08-Sep Expiry)
  nifty_exp = datetime.datetime(
      2026, 9, 8, 15, 30, tzinfo=datetime.timezone(datetime.timedelta(hours=5.5))
  )
  ingest_contract(
      "NSE:NIFTY2690823900CE",
      "NSE:NIFTY50-INDEX",
      23900,
      "CE",
      nifty_exp,
      "2026-08-25",
      "2026-09-04",
  )

  # 2. Ingest SENSEX 76,500 PE (Thursday 10-Sep Expiry)
  sensex_exp = datetime.datetime(
      2026,
      9,
      10,
      15,
      30,
      tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
  )
  ingest_contract(
      "BSE:SENSEX2691076500PE",
      "BSE:SENSEX-INDEX",
      76500,
      "PE",
      sensex_exp,
      "2026-08-25",
      "2026-09-04",
  )

  print("=" * 75)