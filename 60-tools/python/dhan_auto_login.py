# =============================================================================
# File: 60-tools/python/dhan_auto_login.py
# Description: Automated Headless DhanHQ v2 Token Generator (PIN + TOTP)
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
from dotenv import load_dotenv
import pyotp
import requests

SECRETS_PATH = r"C:\kite-agent\secrets\dhan.env"
load_dotenv(SECRETS_PATH)

CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "").strip()
PIN = os.getenv("DHAN_PIN", "").strip()
TOTP_SECRET = os.getenv("DHAN_TOTP_SECRET", "").replace(" ", "").strip()

if not CLIENT_ID or not PIN or not TOTP_SECRET:
  print("❌ Error: DHAN_PIN or DHAN_TOTP_SECRET missing in secrets/dhan.env")
  exit(1)

# Generate 6-digit TOTP code
current_totp = pyotp.TOTP(TOTP_SECRET).now()

print("=" * 65)
print("🚀 DHAN HQ v2 — HEADLESS AUTO-LOGIN (PIN + TOTP)")
print("=" * 65)
print(f"👤 Client ID: {CLIENT_ID}")
print(f"🔢 TOTP Code: {current_totp}")

auth_url = f"https://auth.dhan.co/app/generateAccessToken?dhanClientId={CLIENT_ID}&pin={PIN}&totp={current_totp}"

try:
  res = requests.post(auth_url, timeout=10)
  if res.status_code == 200:
    data = res.json()
    new_token = (
        data.get("data", {}).get("accessToken")
        or data.get("accessToken")
        or data.get("data", {}).get("token")
    )
    if new_token:
      # Update secrets/dhan.env automatically
      with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        f.write(
            f"DHAN_CLIENT_ID={CLIENT_ID}\nDHAN_PIN={PIN}\nDHAN_TOTP_SECRET={TOTP_SECRET}\nDHAN_ACCESS_TOKEN={new_token}\n"
        )
      print("🎉 SUCCESS: Dhan token generated and updated automatically!")
      print(f"🔑 Token: {new_token[:15]}...{new_token[-5:]}")
      print("=" * 65)
    else:
      print(f"⚠️ Unexpected response: {data}")
  else:
    print(f"❌ Login failed (HTTP {res.status_code}): {res.text}")
except Exception as e:
  print(f"❌ Error: {e}")