# =============================================================================
# File: 60-tools/python/build_dynamic_rolled_atm_series.py
# Description: Compiles Continuous Dynamically-Rolled ATM Series for SENSEX
# Resolves: Manus AI feedback on fixed strike & signed flow proxy
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
import numpy as np
import pandas as pd

INPUT_CHAIN_CSV = r"C:\kite-agent\brain\20-market-data\datasets\option_history\SENSEX_30DAYS_5M_FULL_CHAIN.csv"
OUTPUT_DIR = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
OUTPUT_CSV = os.path.join(OUTPUT_DIR, "SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv")


def calculate_signed_flow(df_slice):
  """Calculates the honest Signed Volume Flow Proxy from candle price action."""
  rng = (df_slice["opt_high"] - df_slice["opt_low"]).clip(lower=0.05)
  body = df_slice["opt_close"] - df_slice["opt_open"]
  return (df_slice["volume"] * (body / rng)).round(0)


def build_dynamic_series():
  if not os.path.exists(INPUT_CHAIN_CSV):
    print(f"❌ Error: {INPUT_CHAIN_CSV} not found.")
    print("Run extract_sensex_30days_chain.py first to generate the multi-strike chain.")
    sys.exit(1)

  print("=" * 105)
  print("🚀 COMPILING CONTINUOUS DYNAMICALLY ROLLED ATM SERIES (SENSEX)")
  print(f"📂 Reading Multi-Strike Base: {INPUT_CHAIN_CSV}")
  print("=" * 105)

  df = pd.read_csv(INPUT_CHAIN_CSV)
  df["datetime"] = pd.to_datetime(df["datetime"])

  # 1. Calculate dynamic ATM strike for every timestamp (rounded to nearest 100)
  df["dynamic_atm"] = (df["spot_price"] / 100.0).round() * 100

  # 2. Filter strictly for rows where strike equals dynamic ATM
  atm_rows = df[df["strike"] == df["dynamic_atm"]].copy()

  ce_df = atm_rows[atm_rows["type"] == "CE"].copy()
  pe_df = atm_rows[atm_rows["type"] == "PE"].copy()

  # Deduplicate on timestamp
  ce_df = ce_df.drop_duplicates(subset=["datetime"]).reset_index(drop=True)
  pe_df = pe_df.drop_duplicates(subset=["datetime"]).reset_index(drop=True)

  # Calculate signed flow proxy
  ce_df["ce_flow_proxy"] = calculate_signed_flow(ce_df)
  pe_df["pe_flow_proxy"] = calculate_signed_flow(pe_df)

  # 3. Merge Call and Put into a single continuous row per timestamp
  merged = pd.merge(
      ce_df[[
          "datetime",
          "spot_price",
          "dynamic_atm",
          "symbol",
          "opt_open",
          "opt_high",
          "opt_low",
          "opt_close",
          "volume",
          "iv_pct",
          "delta",
          "gamma",
          "theta",
          "vega",
          "ce_flow_proxy",
      ]],
      pe_df[[
          "datetime",
          "symbol",
          "opt_open",
          "opt_high",
          "opt_low",
          "opt_close",
          "volume",
          "iv_pct",
          "delta",
          "gamma",
          "theta",
          "vega",
          "pe_flow_proxy",
      ]],
      on="datetime",
      suffixes=("_ce", "_pe"),
  )

  # 4. Derive Master Strategy Metrics
  merged["atm_straddle_cost"] = (
      merged["opt_close_ce"] + merged["opt_close_pe"]
  ).round(2)
  merged["atm_straddle_iv"] = (
      (merged["iv_pct_ce"] + merged["iv_pct_pe"]) / 2.0
  ).round(2)
  merged["net_delta_imbalance"] = (
      merged["delta_ce"] + merged["delta_pe"]
  ).round(4)
  merged["total_atm_volume"] = merged["volume_ce"] + merged["volume_pe"]
  merged["net_signed_flow_proxy"] = (
      merged["ce_flow_proxy"] - merged["pe_flow_proxy"]
  ).round(0)

  # Rename columns cleanly for AI consumption
  final_df = merged[[
      "datetime",
      "spot_price",
      "dynamic_atm",
      "opt_close_ce",
      "iv_pct_ce",
      "delta_ce",
      "volume_ce",
      "opt_close_pe",
      "iv_pct_pe",
      "delta_pe",
      "volume_pe",
      "atm_straddle_cost",
      "atm_straddle_iv",
      "net_delta_imbalance",
      "net_signed_flow_proxy",
  ]].copy()

  final_df.columns = [
      "datetime",
      "sensex_spot",
      "rolled_atm_strike",
      "atm_ce_close",
      "atm_ce_iv",
      "atm_ce_delta",
      "atm_ce_volume",
      "atm_pe_close",
      "atm_pe_iv",
      "atm_pe_delta",
      "atm_pe_volume",
      "atm_straddle_cost",
      "atm_straddle_iv",
      "net_delta_imbalance",
      "signed_flow_proxy",
  ]

  os.makedirs(OUTPUT_DIR, exist_ok=True)
  final_df.to_csv(OUTPUT_CSV, index=False)

  print("=" * 105)
  print(
      f"🎉 SUCCESS: Generated {len(final_df):,d} dynamically-rolled ATM bars!"
  )
  print(
      f"📊 Average CE Delta: {final_df['atm_ce_delta'].mean():.4f} (Ideal:"
      f" +0.50) | PE Delta: {final_df['atm_pe_delta'].mean():.4f} (Ideal: -0.50)"
  )
  print(
      f"🪙 Average Straddle Cost: ₹{final_df['atm_straddle_cost'].mean():.2f}"
  )
  print("-" * 105)
  print(
      f"{'Date & Time':<20} | {'Spot':>9} | {'ATM':>6} | {'CE Cls':>8} |"
      f" {'PE Cls':>8} | {'Straddle':>8} | {'CE Del':>6} | {'PE Del':>6}"
  )
  print("-" * 105)
  for _, r in pd.concat([final_df.head(3), final_df.tail(3)]).iterrows():
    print(
        f"{str(r['datetime']):<20} | {r['sensex_spot']:>9.2f} |"
        f" {r['rolled_atm_strike']:>6.0f} | {r['atm_ce_close']:>8.2f} |"
        f" {r['atm_pe_close']:>8.2f} | {r['atm_straddle_cost']:>8.2f} |"
        f" {r['atm_ce_delta']:>6.2f} | {r['atm_pe_delta']:>6.2f}"
    )
  print("=" * 105)
  print(f"📁 Master Single-Sheet Dataset for Manus AI saved to:\n   {OUTPUT_CSV}\n")


if __name__ == "__main__":
  build_dynamic_series()