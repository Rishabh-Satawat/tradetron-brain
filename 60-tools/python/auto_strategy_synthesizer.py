# =============================================================================
# File: 60-tools/python/auto_strategy_synthesizer.py
# Description: Autonomous Quantitative Strategy Discovery & Alpha Mining Engine
# Synthesizes, backtests, and ranks strategy hypotheses across multiple regimes
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import itertools
import os
import sys
import numpy as np
import pandas as pd

DATASET_PATH = r"C:\kite-agent\brain\20-market-data\datasets\option_history\SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv"
LEADERBOARD_PATH = r"C:\kite-agent\brain\70-ops\reports\TOP_10_STRATEGY_LEADERBOARD.md"

if not os.path.exists(DATASET_PATH):
  print(f"❌ Error: {DATASET_PATH} not found.")
  sys.exit(1)

df = pd.read_csv(DATASET_PATH)
df["datetime"] = pd.to_datetime(df["datetime"])
df["date"] = df["datetime"].dt.date
df["time"] = df["datetime"].dt.time

print("=" * 95)
print("🤖 AUTONOMOUS QUANT STRATEGY DISCOVERY & SYNTHESIS ENGINE")
print(
    f"📂 Mining Dataset: SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv ({len(df):,d}"
    " bars)"
)
print("=" * 95)

# 1. Autonomous Hypothesis Combinatorial Matrix
HYPOTHESIS_LIBRARY = [
    # Archetype 1: Trend Pullback Debits
    {
        "family": "BULL_CALL_DEBIT",
        "name": "SENSEX Bullish Momentum Spread",
        "leg_rule": "Buy ATM CE / Sell ATM+500 CE",
        "filter": "MOMENTUM_UP",
    },
    {
        "family": "BEAR_PUT_DEBIT",
        "name": "SENSEX Bearish Breakdown Spread",
        "leg_rule": "Buy ATM PE / Sell ATM-500 PE",
        "filter": "MOMENTUM_DOWN",
    },
    # Archetype 2: Volatility Harvest Credits
    {
        "family": "ATM_STRADDLE",
        "name": "SENSEX Pure Theta Straddle",
        "leg_rule": "Sell ATM CE + PE",
        "filter": "RANGEBOUND",
    },
    {
        "family": "IRON_FLY",
        "name": "SENSEX Defined-Risk Iron Fly V6",
        "leg_rule": "Sell ATM CE/PE + Buy Wings (600 pts)",
        "filter": "RANGEBOUND",
    },
]

TARGET_LEVELS = [1800.0, 2000.0, 2500.0]
STOP_LOSS_LEVELS = [1000.0, 1200.0, 1500.0]
FRICTION = 143.90  # Zerodha statutory friction per cycle

# Pre-extract trading days
daily_sessions = []
for d, group in df.groupby("date"):
  open_b = group[group["time"] >= datetime.time(9, 45)].head(1)
  close_b = group[group["time"] <= datetime.time(15, 10)].tail(1)
  if not open_b.empty and not close_b.empty:
    daily_sessions.append({
        "spot_open": float(open_b["sensex_spot"].values[0]),
        "spot_close": float(close_b["sensex_spot"].values[0]),
        "straddle_open": float(open_b["atm_straddle_cost"].values[0]),
        "straddle_close": float(close_b["atm_straddle_cost"].values[0]),
    })

print(
    f"🧪 Synthesizing candidate strategies across {len(daily_sessions)} market"
    " sessions..."
)

candidates_evaluated = []
variant_counter = 1

for hyp in HYPOTHESIS_LIBRARY:
  for target, sl in itertools.product(TARGET_LEVELS, STOP_LOSS_LEVELS):
    family = hyp["family"]
    trades = []

    for s in daily_sessions:
      spot_move = s["spot_close"] - s["spot_open"]

      if family == "BULL_CALL_DEBIT":
        gross = (
            target
            if spot_move >= 100
            else (-sl if spot_move <= -100 else spot_move * 12.5)
        )
      elif family == "BEAR_PUT_DEBIT":
        gross = (
            target
            if spot_move <= -100
            else (-sl if spot_move >= 100 else -spot_move * 12.5)
        )
      elif family == "ATM_STRADDLE":
        decay = (s["straddle_open"] - s["straddle_close"]) * 20
        gross = min(target, max(-sl, decay))
      elif family == "IRON_FLY":
        decay = (s["straddle_open"] - s["straddle_close"]) * 16
        gross = min(target, max(-sl, decay))
      else:
        gross = 0.0

      net = gross - FRICTION
      trades.append(net)

    trades_arr = np.array(trades)
    wins = trades_arr[trades_arr > 0]
    losses = trades_arr[trades_arr < 0]
    total_trades = len(trades_arr)
    win_rate = (len(wins) / total_trades) * 100.0 if total_trades > 0 else 0.0
    net_pnl = trades_arr.sum()
    pos_sum = wins.sum() if len(wins) > 0 else 0.0
    neg_sum = abs(losses.sum()) if len(losses) > 0 else 0.0
    pf = (pos_sum / neg_sum) if neg_sum > 0 else 99.0

    eq = np.cumsum(trades_arr)
    peak = np.maximum.accumulate(eq)
    dd = (peak - eq).max() if len(eq) > 0 else 0.0

    # Institutional Quality Score (Penalizes drawdowns and low win rates)
    score = (net_pnl / (dd + 1.0)) * (win_rate / 50.0)

    candidates_evaluated.append({
        "variant_id": f"ALPHA-{variant_counter:03d}",
        "name": hyp["name"],
        "family": family,
        "legs": hyp["leg_rule"],
        "target": target,
        "stop_loss": sl,
        "win_rate": round(win_rate, 1),
        "profit_factor": round(pf, 2),
        "net_pnl": round(net_pnl, 2),
        "max_drawdown": round(dd, 2),
        "score": round(score, 2),
    })
    variant_counter += 1

# 2. Select Top 10 Winners
res_df = pd.DataFrame(candidates_evaluated)
top10 = res_df.sort_values(by="score", ascending=False).head(10).reset_index(
    drop=True
)

print("\n" + "=" * 105)
print("🏆 TOP 10 AUTONOMOUSLY MINED QUANT STRATEGIES")
print("=" * 105)
print(
    f"{'Rank':<4} | {'Variant':<9} | {'Strategy Name':<32} | {'Target':>7} |"
    f" {'SL':>6} | {'Win %':>6} | {'PF':>5} | {'Net P&L (₹)':>12} |"
    f" {'Max DD':>8}"
)
print("-" * 105)
for i, r in top10.iterrows():
  print(
      f"#{i+1:<3} | {r['variant_id']:<9} | {r['name'][:32]:<32} |"
      f" ₹{r['target']:>6,.0f} | ₹{r['stop_loss']:>5,.0f} | {r['win_rate']:>5.1f}%"
      f" | {r['profit_factor']:>5.2f} | ₹{r['net_pnl']:>+11,.2f} |"
      f" -₹{r['max_drawdown']:>7,.2f}"
  )
print("=" * 105)

# 3. Export Top Strategy Directly into Tradetron Build Sheet
top_winner = top10.iloc[0]
best_sheet_path = (
    r"C:\kite-agent\brain\30-strategies\AUTONOMOUS_WINNING_STRATEGY.md"
)
os.makedirs(os.path.dirname(best_sheet_path), exist_ok=True)

with open(best_sheet_path, "w", encoding="utf-8") as f:
  f.write(
      "# Autonomously Mined Winning Strategy — Tradetron Build Sheet\n\n"
  )
  f.write(
      f"* Strategy Name: {top_winner['name']} (`{top_winner['variant_id']}`)\n"
  )
  f.write(f"* Family: {top_winner['family']}\n")
  f.write(f"* Win Rate: {top_winner['win_rate']}%\n")
  f.write(f"* Profit Factor: {top_winner['profit_factor']}\n")
  f.write(f"* Net Simulated P&L: ₹{top_winner['net_pnl']:+,.2f}\n")
  f.write(f"* Max Drawdown: -₹{top_winner['max_drawdown']:,.2f}\n\n")
  f.write("## Execution Directives:\n")
  f.write(f"- Legs: {top_winner['legs']}\n")
  f.write(f"- Target: ₹{top_winner['target']:,.0f} * Multiplier\n")
  f.write(f"- Stop Loss: -₹{top_winner['stop_loss']:,.0f} * Multiplier\n")
  f.write("- Exit at Market: YES | Exit Shorts First: YES\n")

print(f"📁 Highest-ranked strategy exported to:\n   {best_sheet_path}\n")