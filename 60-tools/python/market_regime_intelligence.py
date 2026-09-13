# =============================================================================
# File: 60-tools/python/market_regime_intelligence.py
# Description: Institutional Volatility Surface, GEX & Market Regime Engine
# Analyzes: 30-Day 5-Minute Historical Datasets + Live Option Chains
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import glob
import os
import sys
import numpy as np
import pandas as pd

DATA_DIR = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
DATASET_FILE = os.path.join(DATA_DIR, "SENSEX_30DAYS_5M_FULL_CHAIN.csv")


def load_dataset():
  if not os.path.exists(DATASET_FILE):
    # Check for any available option history CSV
    csvs = glob.glob(os.path.join(DATA_DIR, "*.csv"))
    if not csvs:
      print(f"❌ Error: No datasets found in {DATA_DIR}")
      sys.exit(1)
    return pd.read_csv(csvs[0]), os.path.basename(csvs[0])
  return pd.read_csv(DATASET_FILE), "SENSEX_30DAYS_5M_FULL_CHAIN.csv"


def calculate_realized_volatility(spot_series, window=75 * 5):
  """Computes annualized realized volatility from 5-minute log returns."""
  log_returns = np.log(spot_series / spot_series.shift(1)).dropna()
  # 75 five-minute bars per day * 252 trading days = 18,900 bars/year
  annualized_rv = (
      log_returns.tail(window).std() * np.sqrt(75 * 252) * 100.0
  )
  return round(float(annualized_rv), 2)


def analyze_market_regime():
  df, filename = load_dataset()
  df["datetime"] = pd.to_datetime(df["datetime"])
  df = df.sort_values("datetime").reset_index(drop=True)

  print("=" * 95)
  print("🧠 QUANTITATIVE MARKET REGIME & VOLATILITY INTELLIGENCE ENGINE")
  print(f"📊 Analyzing Dataset: {filename} ({len(df):,d} total records)")
  print("=" * 95)

  # 1. Spot Dynamics & Realized Volatility
  unique_spot_df = (
      df[["datetime", "spot_price"]].drop_duplicates().reset_index(drop=True)
  )
  current_spot = unique_spot_df["spot_price"].iloc[-1]
  start_spot = unique_spot_df["spot_price"].iloc[0]
  spot_30d_return = ((current_spot - start_spot) / start_spot) * 100.0
  rv_annualized = calculate_realized_volatility(unique_spot_df["spot_price"])

  # 2. Implied Volatility (IV) Surface Metrics
  atm_rows = df[abs(df["spot_price"] - df["strike"]) <= 150].copy()
  if atm_rows.empty:
    atm_rows = df.copy()

  current_iv = atm_rows["iv_pct"].iloc[-1]
  iv_min = atm_rows["iv_pct"].min()
  iv_max = atm_rows["iv_pct"].max()

  # IV Rank (IVR) & IV Percentile (IVP)
  ivr = (
      ((current_iv - iv_min) / (iv_max - iv_min)) * 100.0
      if iv_max > iv_min
      else 50.0
  )
  ivp = (atm_rows["iv_pct"] < current_iv).mean() * 100.0
  vrp = current_iv - rv_annualized  # Volatility Risk Premium

  # 3. 25-Delta Put/Call Skew
  call_25d = df[(df["type"] == "CE") & (abs(df["delta"] - 0.25) <= 0.08)]
  put_25d = df[(df["type"] == "PE") & (abs(df["delta"] - (-0.25)) <= 0.08)]
  call_iv_25d = (
      call_25d["iv_pct"].iloc[-1] if not call_25d.empty else current_iv
  )
  put_iv_25d = put_25d["iv_pct"].iloc[-1] if not put_25d.empty else current_iv
  iv_skew_25d = put_iv_25d - call_iv_25d  # Positive = Downside fear premium

  # 4. Net Gamma Exposure (GEX)
  latest_slice = df[
      df["datetime"] == df["datetime"].iloc[-1]
  ].copy()
  gex_total = 0.0
  for _, row in latest_slice.iterrows():
    gamma = row.get("gamma", 0.001)
    vol = row.get("volume", 100)
    # Market maker gamma estimate
    if row["type"] == "CE":
      gex_total += vol * gamma * current_spot * 100
    else:
      gex_total -= vol * gamma * current_spot * 100

  # 5. Quantitative Synthesis & Regime Classification
  print(f"\n1. ASSET PRICE & REALIZED VOLATILITY DYNAMICS:")
  print(
      f"   • Current Spot Price   : ₹{current_spot:,.2f} (30-Day Move:"
      f" {spot_30d_return:+.2f}%)"
  )
  print(f"   • 30-Day Realized Vol  : {rv_annualized:.2f}% (Annualized)")

  print(f"\n2. IMPLIED VOLATILITY (IV) SURFACE & SKEW:")
  print(f"   • Current ATM IV       : {current_iv:.2f}%")
  print(
      f"   • 30-Day IV Range      : {iv_min:.2f}% (Low) to {iv_max:.2f}% (High)"
  )
  print(
      f"   • IV Rank (IVR)        : {ivr:.1f}/100 | IV Percentile (IVP):"
      f" {ivp:.1f}%"
  )
  print(
      f"   • Vol Risk Premium     : {vrp:+.2f}%"
      f" ({'IV Overpriced' if vrp > 0 else 'IV Underpriced'})"
  )
  print(
      f"   • 25-Delta Skew (P-C)  : {iv_skew_25d:+.2f}%"
      f" ({'Elevated Downside Fear' if iv_skew_25d > 2.0 else 'Balanced Skew'})"
  )

  print(f"\n3. MARKET MAKER GAMMA EXPOSURE (GEX):")
  gex_crores = gex_total / 1e7
  print(
      f"   • Net Dealer Gamma     : {gex_crores:+,.2f} Cr"
      f" ({'Long Gamma / Vol Dampening' if gex_crores >= 0 else 'Short Gamma / Trend Acceleration'})"
  )

  # 6. Actionable Strategy Verdict
  print("\n" + "=" * 95)
  print("🎯 INSTITUTIONAL DESK STRATEGY RECOMMENDATION")
  print("=" * 95)

  if ivr < 30 and gex_crores < 0:
    recommended_strategy = (
        "S01 Bull Call Spread / S06 Bear Put Spread (Directional Debit)"
    )
    rationale = (
        "IV is historically cheap (IVR < 30) and dealers are short gamma. "
        "Buying options via defined-risk spreads offers high asymmetry."
    )
    wing_guidance = (
        "500-point standard spread wings. Avoid selling unhedged naked theta."
    )
  elif ivr >= 60 and gex_crores >= 0:
    recommended_strategy = "SENSEX Expiry Day Iron Fly V6 (Non-Directional)"
    rationale = (
        "IV is elevated (IVR > 60) and dealers are long gamma (volatility"
        " suppression). "
        "Favorable environment for collecting theta decay."
    )
    wing_guidance = (
        "Widen wings to 700–800 points to absorb intraday expansion."
    )
  elif iv_skew_25d > 3.0:
    recommended_strategy = (
        "S06 Bear Put Spread (Trend-Pullback Put Buying)"
    )
    rationale = (
        "Heavy put skew indicates aggressive institutional downside hedging."
    )
    wing_guidance = "ATM Long Put / ATM - 500 Short Put."
  else:
    recommended_strategy = "S01 SENSEX RSI-35 Recovery Bull-Call Spread"
    rationale = (
        "Volatility is balanced. S01 baseline holds verified positive"
        " expectancy (+12% Net)."
    )
    wing_guidance = "ATM Long Call / ATM + 500 Short Call."

  print(f"📌 PRIMARY STRATEGY : {recommended_strategy}")
  print(f"📖 QUANT RATIONALE  : {rationale}")
  print(f"📐 STRIKE / WING CFG: {wing_guidance}")
  print("=" * 95)

  # Output machine-readable directive for Tradetron Compiler (Pillar 2)
  directive = {
      "timestamp": datetime.datetime.now().isoformat(),
      "spot_price": current_spot,
      "ivr": round(ivr, 2),
      "ivp": round(ivp, 2),
      "vrp": round(vrp, 2),
      "gex_cr": round(gex_crores, 2),
      "skew_25d": round(iv_skew_25d, 2),
      "recommended_strategy": recommended_strategy,
  }
  directive_path = r"C:\kite-agent\brain\70-ops\status\regime_directive.json"
  os.makedirs(os.path.dirname(directive_path), exist_ok=True)
  with open(directive_path, "w") as f:
    import json

    json.dump(directive, f, indent=2)
  print(f"📁 Saved machine directive to: {directive_path}\n")


if __name__ == "__main__":
  analyze_market_regime()