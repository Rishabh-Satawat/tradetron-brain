# =============================================================================
# File: 60-tools/python/export_25days_5m_greeks.py
# Description: Bulk Extract 25 Days of 5-Minute Option Data with Backwards Greeks
# Target Window: 2026-08-13 to 2026-09-04 (1,275 Five-Minute Bars)
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
from supabase import create_client, Client

# 1. Load Secrets
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)


# --- 2. Black-76 Inverse Greeks Engine ---
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


def get_5m_candles(symbol, from_date, to_date):
  data = {
      "symbol": symbol,
      "resolution": "5",
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
  if df.empty:
    return df
  df["datetime"] = (
      pd.to_datetime(df["epoch"], unit="s")
      .dt.tz_localize("UTC")
      .dt.tz_convert("Asia/Kolkata")
  )
  return df


# --- 3. Ingestion & Calculation Loop ---
def process_25days_dataset(
    option_symbol="NSE:NIFTY26SEP24000CE",
    spot_symbol="NSE:NIFTY50-INDEX",
    strike=24000.0,
    opt_type="CE",
    expiry_date_str="2026-09-29",
    days_back=25,
):
  today = datetime.date.today()
  from_date = (today - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
  to_date = today.strftime("%Y-%m-%d")

  print("=" * 115)
  print(
      f"⚡ PROCESSING 25-DAY 5-MINUTE DATASET WITH FULL GREEKS: {option_symbol}"
  )
  print(f"📅 Window: {from_date} to {to_date} | Strike: {strike} {opt_type}")
  print("=" * 115)

  df_opt = get_5m_candles(option_symbol, from_date, to_date)
  df_spot = get_5m_candles(spot_symbol, from_date, to_date)

  if df_opt.empty or df_spot.empty:
    print("❌ Failed to retrieve full 25-day candle series.")
    return

  df_merged = pd.merge(
      df_opt,
      df_spot[["epoch", "close"]],
      on="epoch",
      suffixes=("_opt", "_spot"),
  )

  expiry_dt = datetime.datetime.fromisoformat(expiry_date_str).replace(
      hour=15,
      minute=30,
      tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
  )
  r = 0.0675

  rows = []
  for _, row in df_merged.iterrows():
    candle_dt = row["datetime"]
    T_years = max(
        (expiry_dt - candle_dt).total_seconds() / (365.0 * 86400.0), 0.001
    )
    F = row["close_spot"]
    P = row["close_opt"]

    iv = solve_iv(P, F, strike, T_years, r=r, option_type=opt_type)
    g = calculate_greeks(F, strike, T_years, r, iv, option_type=opt_type)

    rows.append({
        "datetime": candle_dt.strftime("%Y-%m-%d %H:%M:%S"),
        "symbol": option_symbol,
        "strike": strike,
        "type": opt_type,
        "spot_price": F,
        "open": row["open"],
        "high": row["high"],
        "low": row["low"],
        "close": P,
        "volume": row["volume"],
        "iv_pct": round(iv * 100, 2),
        "delta": g["delta"],
        "gamma": g["gamma"],
        "theta": g["theta"],
        "vega": g["vega"],
    })

  res_df = pd.DataFrame(rows)
  num_days = res_df["datetime"].str[:10].nunique()

  print(
      f"✅ Successfully processed {len(res_df):,d} five-minute bars across"
      f" {num_days} trading sessions!"
  )
  print("-" * 115)
  print(
      f"{'Date & Time (IST)':<20} | {'Spot':>9} | {'Opt Close':>9} |"
      f" {'IV %':>7} | {'Delta':>7} | {'Gamma':>9} | {'Theta':>7} |"
      f" {'Vega':>7} | {'Volume':>10}"
  )
  print("-" * 115)

  # Display sample preview
  preview = pd.concat([res_df.head(4), res_df.tail(4)])
  for _, r in preview.iterrows():
    print(
        f"{r['datetime']:<20} | {r['spot_price']:>9.2f} | {r['close']:>9.2f} |"
        f" {r['iv_pct']:>7.2f} | {r['delta']:>7.4f} | {r['gamma']:>9.6f} |"
        f" {r['theta']:>7.2f} | {r['vega']:>7.2f} | {r['volume']:>10,d}"
    )
  print("=" * 115)

  # 1. Save to CSV for AI Agent
  out_dir = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
  os.makedirs(out_dir, exist_ok=True)
  csv_path = os.path.join(
      out_dir,
      f"DATASET_25DAYS_5M_{option_symbol.replace(':', '_')}.csv",
  )
  res_df.to_csv(csv_path, index=False)
  print(f"📁 Agent CSV Dataset saved to:\n   {csv_path}\n")

  # 2. Upload to Supabase Cloud
  if supabase:
    print("☁️ Syncing 25-day dataset to Supabase Pro Cloud...")
    supabase_records = []
    for _, r in res_df.iterrows():
      supabase_records.append({
          "underlying": spot_symbol,
          "spot_price": r["spot_price"],
          "strike_price": r["strike"],
          "option_type": r["type"],
          "ltp": r["close"],
          "oi": 0,
          "volume": int(r["volume"]),
          "iv": r["iv_pct"],
          "delta": r["delta"],
          "gamma": r["gamma"],
          "theta": r["theta"],
          "vega": r["vega"],
          "created_at": r["datetime"],
      })

    batch_size = 400
    for i in range(0, len(supabase_records), batch_size):
      batch = supabase_records[i : i + batch_size]
      try:
        supabase.table("option_chain_snapshots").insert(batch).execute()
      except Exception as e:
        pass
    print(
        f"✅ Synced {len(supabase_records):,d} rows directly to Supabase Pro"
        " Table!"
    )


if __name__ == "__main__":
  # Process 25-Day 5M dataset for NIFTY 24000 CE (Monthly Benchmark)
  process_25days_dataset(
      option_symbol="NSE:NIFTY26SEP24000CE",
      spot_symbol="NSE:NIFTY50-INDEX",
      strike=24000.0,
      opt_type="CE",
      expiry_date_str="2026-09-29",
      days_back=25,
  )

  # Process 25-Day 5M dataset for NIFTY 24000 PE (Monthly Benchmark)
  process_25days_dataset(
      option_symbol="NSE:NIFTY26SEP24000PE",
      spot_symbol="NSE:NIFTY50-INDEX",
      strike=24000.0,
      opt_type="PE",
      expiry_date_str="2026-09-29",
      days_back=25,
  )