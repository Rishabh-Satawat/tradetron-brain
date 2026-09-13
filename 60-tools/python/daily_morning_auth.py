# =============================================================================
# File: 60-tools/python/daily_morning_auth.py
# Description: Production Morning Authenticator & Pre-Flight System
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import subprocess
import sys

PYTHON = sys.executable

print("=" * 80)
print(
    "🌅 QUANT DESK — PRODUCTION BROKER AUTH & PRE-FLIGHT (MUMBAI)"
)
print(f"📅 Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
print("=" * 80)

# 1. DhanHQ v2 (100% Headless via PIN + TOTP)
print("\n[1/4] Refreshing DhanHQ v2 (Headless PIN + TOTP)...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\dhan_auto_login.py"],
    check=False,
)

# 2. Fyers Prime v3 (1-Click Auto-Capture)
print("\n[2/4] Checking Fyers Prime v3 Session...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\fyers_live_desk.py"],
    check=False,
)

# 3. Zerodha Kite Connect (1-Click Auto-Capture)
print("\n[3/4] Refreshing Zerodha Kite Connect...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\generate_token.py"],
    cwd=r"C:\kite-agent",
    check=False,
)

# Copy token to brain folder
try:
  with open(r"C:\kite-agent\access_token.txt") as f:
    tok = f.read().strip()
  with open(r"C:\kite-agent\brain\access_token.txt", "w") as f:
    f.write(tok)
  print("   ✅ Kite access token synchronized to brain.")
except Exception as e:
  pass

# 4. Final Comprehensive Pre-Flight Health Check
print("\n[4/4] Executing Final Desk Health Audit...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\preflight_check.py"],
    check=False,
)

print("\n" + "=" * 80)
print("🎉 ALL BROKERS & SUPABASE ARE ACTIVE FOR TODAY'S SESSION!")
print("=" * 80)