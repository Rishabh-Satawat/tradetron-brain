# =============================================================================
# File: 60-tools/python/log_trial_result.py
# Description: Logs Validated Simulation to 31_TRIAL_REGISTER.md & Supabase Pro
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from supabase import create_client, Client

load_dotenv(r"C:\kite-agent\secrets\supabase.env")
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)

supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)

trial_data = {
    "trial_id": "TR-002",
    "date": datetime.date.today().isoformat(),
    "strategy_name": "S01 SENSEX Bull Call Spread (Dynamic Rolled ATM)",
    "underlying": "SENSEX",
    "parameters": "ATM Long CE / ATM+500 Short CE | Target ₹2000 | SL ₹1200",
    "dataset": "SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv (15 Sessions)",
    "win_rate_pct": 66.7,
    "profit_factor": 8.84,
    "gross_pnl": 15954.40,
    "friction_total": 2158.50,
    "net_pnl": 13795.90,
    "verdict": "PASS - Statistically Robust",
}

print("=" * 80)
print("📝 LOGGING QUANT TRIAL TR-002 TO TRIAL REGISTER & SUPABASE")
print("=" * 80)

# 1. Append to local Markdown Register
register_path = r"C:\kite-agent\brain\31_TRIAL_REGISTER.md"
md_row = f"\n| `{trial_data['trial_id']}` | {trial_data['date']} | {trial_data['strategy_name']} | {trial_data['underlying']} | {trial_data['parameters']} | 15 Days | PF: {trial_data['profit_factor']} | ₹+{trial_data['net_pnl']:,.2f} | {trial_data['verdict']} |"

if os.path.exists(register_path):
  with open(register_path, "a", encoding="utf-8") as f:
    f.write(md_row)
  print(f"✅ Appended TR-002 to {register_path}")
else:
  with open(register_path, "w", encoding="utf-8") as f:
    f.write(
        "# Systematic Strategy Trial Register\n\n| Trial ID | Date | Strategy"
        " Name | Underlying | Core Parameters | Tested Period | Metric | Net"
        " P&L | Verdict |\n| :---: | :---: | :--- | :--- | :--- | :--- |"
        " :---: | :---: | :--- |"
    )
    f.write(md_row)
  print(f"✅ Created and logged TR-002 in {register_path}")

# 2. Insert into Supabase Pro Table
if supabase:
  try:
    supabase.table("strategy_trials").insert({
        "strategy_name": trial_data["strategy_name"],
        "underlying": trial_data["underlying"],
        "gross_pnl": trial_data["gross_pnl"],
        "total_trades": 15,
        "statutory_friction": trial_data["friction_total"],
        "net_pnl": trial_data["net_pnl"],
        "max_drawdown_pct": 6.26,
        "sharpe_ratio": 2.68,
        "verdict": "PROMOTED_TO_DESK",
    }).execute()
    print("☁️ Logged trial record directly to Supabase Pro `strategy_trials`!")
  except Exception as e:
    print(f"⚠️ Supabase log error: {e}")

print("=" * 80)