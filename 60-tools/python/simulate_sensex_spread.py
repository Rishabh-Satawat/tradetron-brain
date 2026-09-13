# =============================================================================
# File: 60-tools/python/simulate_sensex_spread.py
# Description: Quantitative Simulation of SENSEX Dynamic ATM Decay & Spreads
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
import numpy as np
import pandas as pd

DATASET_PATH = r"C:\kite-agent\brain\20-market-data\datasets\option_history\SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv"

if not os.path.exists(DATASET_PATH):
  print(f"❌ Error: {DATASET_PATH} not found.")
  sys.exit(1)

df = pd.read_csv(DATASET_PATH)
df["datetime"] = pd.to_datetime(df["datetime"])
df["date"] = df["datetime"].dt.date
df["time"] = df["datetime"].dt.time

print("=" * 95)
print("📊 SENSEX DYNAMIC ROLLED ATM — QUANTITATIVE DECAY & STRATEGY SIMULATION")
print(f"📂 Dataset: SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv ({len(df):,d} bars)")
print("=" * 95)

# 1. Analyze Daily Intraday Straddle Decay (09:45 to 15:10)
sessions = []
for d, group in df.groupby("date"):
  open_slice = group[
      group["time"] >= datetime.time(9, 45)
  ].head(1)
  close_slice = group[
      group["time"] <= datetime.time(15, 10)
  ].tail(1)

  if open_slice.empty or close_slice.empty:
    continue

  entry_straddle = open_slice["atm_straddle_cost"].values[0]
  exit_straddle = close_slice["atm_straddle_cost"].values[0]
  decay_inr = entry_straddle - exit_straddle
  decay_pct = (decay_inr / entry_straddle) * 100.0 if entry_straddle > 0 else 0

  entry_spot = open_slice["sensex_spot"].values[0]
  exit_spot = close_slice["sensex_spot"].values[0]
  spot_move = exit_spot - entry_spot

  sessions.append({
      "date": str(d),
      "spot_open": entry_spot,
      "spot_close": exit_spot,
      "spot_move": spot_move,
      "straddle_open": entry_straddle,
      "straddle_close": exit_straddle,
      "decay_inr": decay_inr,
      "decay_pct": decay_pct,
  })

sess_df = pd.DataFrame(sessions)

if sess_df.empty:
  print("⚠️ No full 09:45–15:10 sessions detected in dataset.")
  sys.exit(0)

print(f"\n1. INTRADAY ATM STRADDLE THETA DECAY (09:45 to 15:10):")
print(f"   • Total Trading Sessions Analyzed : {len(sess_df)} days")
print(f"   • Average Opening Straddle Cost   : ₹{sess_df['straddle_open'].mean():.2f}")
print(f"   • Average Closing Straddle Cost   : ₹{sess_df['straddle_close'].mean():.2f}")
print(f"   • Average Daily Theta Decay       : ₹{sess_df['decay_inr'].mean():+.2f} per lot ({sess_df['decay_pct'].mean():+.2f}%)")
win_decay_days = (sess_df["decay_inr"] > 0).mean() * 100
print(f"   • Sessions with Positive Decay    : {win_decay_days:.1f}% of days")

# 2. Simulate S01 Bull Call Spread with Exact Statutory Friction
# S01: Target = ₹2,000 | SL = -₹1,200 | Net Friction = ₹143.90 per cycle
print(f"\n2. S01 BULL CALL SPREAD STRESS-TEST (Post-Friction):")
FRICTION_PER_CYCLE = 143.90
trades = []

for _, s in sess_df.iterrows():
  if s["spot_move"] > 100:
    gross = 2000.0  # Hit target
  elif s["spot_move"] < -100:
    gross = -1200.0  # Hit stop loss
  else:
    gross = s["spot_move"] * 10  # Partial exit / time square-off

  net = gross - FRICTION_PER_CYCLE
  trades.append(net)

trades_arr = np.array(trades)
win_rate = (trades_arr > 0).mean() * 100
total_net_pnl = trades_arr.sum()
pos_sum = trades_arr[trades_arr > 0].sum()
neg_sum = abs(trades_arr[trades_arr < 0].sum())
profit_factor = (pos_sum / neg_sum) if neg_sum > 0 else 0

print(f"   • Simulated Trades              : {len(trades_arr)} cycles")
print(f"   • Win Rate                      : {win_rate:.1f}%")
print(f"   • Profit Factor                 : {profit_factor:.2f}")
print(f"   • Cumulative Net Realized P&L   : ₹{total_net_pnl:+,.2f} (After ₹143.90 fee/trade)")
print("=" * 95)