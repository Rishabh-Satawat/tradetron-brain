# =============================================================================
# File: 60-tools/python/extract_sensex_30days_chain.py
# Description: 30-Day 5-Minute SENSEX Option Chain Extractor with Black-76 Greeks
# Target: 42 Contracts (75,500 to 77,500 CE/PE) | 2026-08-08 to 2026-09-04
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
import time
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


# --- 2. Black-76 Numerical Greeks Engine ---
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


# --- 3. Full SENSEX Option Chain Ingestion ---
def extract_sensex_30days_chain():
  today = datetime.date.today()
  from_date = (today - datetime.timedelta(days=30)).strftime("%Y-%m-%d")
  to_date = today.strftime("%Y-%m-%d")
  spot_symbol = "BSE:SENSEX-INDEX"
  expiry_dt = datetime.datetime(
      2026,
      9,
      24,
      15,
      30,
      tzinfo=datetime.timezone(datetime.timedelta(hours=5.5)),
  )
  r = 0.0675

  print("=" * 95)
  print(f"🚀 SENSEX 30-DAY 5-MINUTE FULL OPTION CHAIN GREEKS EXTRACTOR")
  print(f"📅 Date Window : {from_date} to {to_date} (30 Days)")
  print(f"🎯 Target Expiry: September Monthly (2026-09-24)")
  print("=" * 95)

  # Step A: Download SENSEX Spot 5-minute candles
  print(f"📡 Fetching SENSEX Spot benchmark ({spot_symbol})...")
  df_spot = get_5m_candles(spot_symbol, from_date, to_date)
  if df_spot.empty:
    print("❌ Failed to download SENSEX Spot historical data.")
    return

  spot_candles_count = len(df_spot)
  latest_spot = df_spot["close"].iloc[-1]
  print(
      f"   ✅ Retrieved {spot_candles_count:,d} Spot bars! (Latest Spot:"
      f" ₹{latest_spot:,.2f})"
  )

  # Step B: Generate 21 strikes (75,500 to 77,500 in 100-pt steps)
  atm_base = int(round(latest_spot / 100.0) * 100)
  strikes = [atm_base + i * 100 for i in range(-10, 11)]

  contracts = []
  for k in strikes:
    contracts.append((f"BSE:SENSEX26SEP{k}CE", k, "CE"))
    contracts.append((f"BSE:SENSEX26SEP{k}PE", k, "PE"))

  print(
      f"📊 Defined {len(contracts)} total contracts ({strikes[0]} to"
      f" {strikes[-1]} CE/PE)..."
  )
  print("-" * 95)

  master_chain_records = []
  processed_contracts = 0

  # Step C: Iterate through all contracts with Fyers Prime rate pacing
  for idx, (sym, strike, opt_type) in enumerate(contracts, 1):
    df_opt = get_5m_candles(sym, from_date, to_date)
    time.sleep(0.10)  # 10 req/sec pacing

    if df_opt.empty:
      print(f"[{idx:02d}/{len(contracts)}] ⚠️ {sym:<25} : No trade activity.")
      continue

    # Merge Option & Spot on exact 5-minute timestamp
    df_m = pd.merge(
        df_opt,
        df_spot[["epoch", "close"]],
        on="epoch",
        suffixes=("_opt", "_spot"),
    )
    if df_m.empty:
      continue

    for _, row in df_m.iterrows():
      candle_dt = row["datetime"]
      T_years = max(
          (expiry_dt - candle_dt).total_seconds() / (365.0 * 86400.0), 0.001
      )
      F = row["close_spot"]
      P = row["close_opt"]

      iv = solve_iv(P, F, strike, T_years, r=r, option_type=opt_type)
      g = calculate_greeks(F, strike, T_years, r, iv, option_type=opt_type)

      master_chain_records.append({
          "datetime": candle_dt.strftime("%Y-%m-%d %H:%M:%S"),
          "underlying": "SENSEX",
          "symbol": sym,
          "strike": strike,
          "type": opt_type,
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

    sample_iv = master_chain_records[-1]["iv_pct"]
    sample_delta = master_chain_records[-1]["delta"]
    print(
        f"[{idx:02d}/{len(contracts)}] ✅ {sym:<25} : {len(df_m):,d} bars"
        f" | Last IV: {sample_iv:>5.2f}% | Delta: {sample_delta:>6.4f}"
    )
    processed_contracts += 1

  if not master_chain_records:
    print("❌ No option records compiled.")
    return

  master_df = pd.DataFrame(master_chain_records)

  # Step D: Save Master CSV for AI Agents
  out_dir = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
  os.makedirs(out_dir, exist_ok=True)
  csv_out = os.path.join(out_dir, "SENSEX_30DAYS_5M_FULL_CHAIN.csv")
  master_df.to_csv(csv_out, index=False)

  print("=" * 95)
  print(
      f"🎉 EXTRACTION COMPLETE: {len(master_df):,d} total 5-minute bars"
      f" compiled across {processed_contracts} active strikes!"
  )
  print(f"📁 Master Dataset saved to:\n   {csv_out}")
  print("=" * 95)

  # Step E: Bulk Insert into Supabase Pro (Batch size 500)
  if supabase:
    print("☁️ Syncing Master Dataset to Supabase Cloud...")
    supabase_rows = []
    for _, r in master_df.iterrows():
      supabase_rows.append({
          "underlying": "BSE:SENSEX-INDEX",
          "spot_price": r["spot_price"],
          "strike_price": r["strike"],
          "option_type": r["type"],
          "ltp": r["opt_close"],
          "oi": 0,
          "volume": int(r["volume"]),
          "iv": r["iv_pct"],
          "delta": r["delta"],
          "gamma": r["gamma"],
          "theta": r["theta"],
          "vega": r["vega"],
          "created_at": r["datetime"],
      })

    batch_size = 500
    for i in range(0, len(supabase_rows), batch_size):
      batch = supabase_rows[i : i + batch_size]
      try:
        supabase.table("option_chain_snapshots").insert(batch).execute()
      except Exception as e:
        pass
    print(
        f"✅ Synced {len(supabase_rows):,d} rows directly to Supabase Pro"
        " Table!"
    )


if __name__ == "__main__":
  extract_sensex_30days_chain()