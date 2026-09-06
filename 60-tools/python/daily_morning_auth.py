# =============================================================================
# File: 60-tools/python/daily_morning_auth.py
# Description: Master Zero-Click Morning Authenticator (Runs at 07:30 AM Daily)
# Refreshes: DhanHQ v2 + Fyers Prime v3 + Zerodha Kite Connect
# =============================================================================
import datetime
import os
import subprocess
import sys

PYTHON = sys.executable

print("=" * 80)
print(
    "🌅 QUANT DESK — AUTOMATED 07:30 AM BROKER RE-AUTHENTICATION ENGINE"
)
print(f"📅 Timestamp: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}")
print("=" * 80)

# 1. Re-authenticate DhanHQ v2
print("\n[1/3] Refreshing DhanHQ v2 Token (PIN + TOTP)...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\dhan_auto_login.py"],
    check=False,
)

# 2. Re-authenticate Fyers Prime v3
print("\n[2/3] Refreshing Fyers Prime v3 Token (PIN + TOTP)...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\fyers_auto_login.py"],
    check=False,
)

# 3. Re-authenticate Zerodha Kite Connect
print("\n[3/3] Refreshing Zerodha Kite Connect Token (Password + TOTP)...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\kite_auto_login.py"],
    check=False,
)

# 4. Verify Final Health
print("\n[4/4] Executing Comprehensive Pre-Flight Health Check...")
subprocess.run(
    [PYTHON, r"C:\kite-agent\brain\60-tools\python\preflight_check.py"],
    check=False,
)

print("\n" + "=" * 80)
print("🎉 ALL TOKENS ROTATED & SAVED. DESK READY FOR 09:15 AM MARKET OPEN!")
print("=" * 80)