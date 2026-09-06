# =============================================================================
# File: 60-tools/python/dhan_token_rotate.py
# Description: Automated DhanHQ v2 Token Rotation & Self-Renewal Engine
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import requests
from dotenv import load_dotenv

SECRETS_PATH = r"C:\kite-agent\secrets\dhan.env"

if not os.path.exists(SECRETS_PATH):
  print(f"❌ Error: {SECRETS_PATH} not found.")
  exit(1)

load_dotenv(SECRETS_PATH)
CLIENT_ID = os.getenv("DHAN_CLIENT_ID", "").strip()
OLD_TOKEN = os.getenv("DHAN_ACCESS_TOKEN", "").strip()

if not CLIENT_ID or not OLD_TOKEN:
  print(
      "❌ Error: DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN missing in"
      " secrets/dhan.env"
  )
  exit(1)

print("=" * 65)
print("🔄 DHAN HQ v2 — TOKEN ROTATION ENGINE")
print("=" * 65)

# Call the official Dhan RenewToken endpoint
renew_url = "https://api.dhan.co/v2/RenewToken"
headers = {
    "access-token": OLD_TOKEN,
    "dhanClientId": CLIENT_ID,
    "client-id": CLIENT_ID,
    "Content-Type": "application/json",
}

try:
  resp = requests.get(renew_url, headers=headers, timeout=10)
  if resp.status_code == 200:
    res_json = resp.json()
    new_token = (
        res_json.get("data", {}).get("accessToken")
        or res_json.get("accessToken")
        or res_json.get("data", {}).get("token")
    )

    if new_token:
      # Automatically rewrite secrets/dhan.env with the fresh token
      with open(SECRETS_PATH, "w", encoding="utf-8") as f:
        f.write(f"DHAN_CLIENT_ID={CLIENT_ID}\nDHAN_ACCESS_TOKEN={new_token}\n")

      print("✅ SUCCESS: Dhan token rotated and extended!")
      print(f"🔑 New Token: {new_token[:15]}...{new_token[-5:]}")
      print(f"📁 Updated   : {SECRETS_PATH}")

      # Verify the new token immediately
      prof_resp = requests.get(
          "https://api.dhan.co/v2/profile",
          headers={
              "access-token": new_token,
              "client-id": CLIENT_ID,
              "dhanClientId": CLIENT_ID,
          },
          timeout=10,
      )
      if prof_resp.status_code == 200:
        p_data = prof_resp.json()
        print(f"👤 Client ID    : {p_data.get('dhanClientId', CLIENT_ID)}")
        print(f"📅 New Validity : {p_data.get('dataValidity')}")
      print("=" * 65)
    else:
      print(f"⚠️ Response format unexpected: {res_json}")
  else:
    print(f"❌ Renewal rejected (HTTP {resp.status_code}): {resp.text}")

except Exception as e:
  print(f"❌ Network/Request error: {e}")