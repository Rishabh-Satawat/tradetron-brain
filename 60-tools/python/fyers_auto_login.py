# =============================================================================
# File: 60-tools/python/fyers_auto_login.py
# Description: 100% Headless Automated Token Generator for Fyers API v3
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import base64
import datetime
import hashlib
import json
import os
import sys
import urllib.parse
from dotenv import load_dotenv
import pyotp
import requests

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

load_dotenv(SECRETS_PATH)
APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "").strip()
REDIRECT_URI = os.getenv(
    "FYERS_REDIRECT_URI", "http://127.0.0.1:5000/fyers/callback"
).strip()
USER_ID = os.getenv("FYERS_USER_ID", "").strip()
PIN = os.getenv("FYERS_PIN", "").strip()
TOTP_SECRET = os.getenv("FYERS_TOTP_SECRET", "").replace(" ", "").strip()

print("=" * 70)
print("🚀 FYERS API v3 — 100% HEADLESS ZERO-CLICK TOKEN GENERATOR")
print("=" * 70)

if not APP_ID or not SECRET_KEY or not USER_ID or not PIN or not TOTP_SECRET:
  print(
      "❌ Error: FYERS_USER_ID, FYERS_PIN, or FYERS_TOTP_SECRET missing in"
      " secrets/fyers.env"
  )
  sys.exit(1)

session = requests.Session()
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ),
    "Accept": "application/json",
}

try:
  # 1. Send Login OTP request via TOTP
  totp_code = pyotp.TOTP(TOTP_SECRET).now()
  print(f"👤 User ID  : {USER_ID}")
  print(f"🔢 Live TOTP: {totp_code}")

  # Step A: Validate TOTP on Fyers Auth Server
  send_otp_url = "https://api-t2.fyers.in/vagator/v2/send_login_otp"
  res_otp = session.post(
      send_otp_url,
      headers=headers,
      json={"fy_id": USER_ID, "app_id": "2"},
      timeout=10,
  )
  request_key = res_otp.json().get("request_key")

  if not request_key:
    # Alternate flow: Direct TOTP verification
    verify_totp_url = "https://api-t2.fyers.in/vagator/v2/verify_totp"
    res_totp = session.post(
        verify_totp_url,
        headers=headers,
        json={"fy_id": USER_ID, "app_id": "2", "otp": totp_code},
        timeout=10,
    )
    request_key = res_totp.json().get("request_key")

  # Step B: Verify PIN with request_key
  verify_pin_url = "https://api-t2.fyers.in/vagator/v2/verify_pin"
  res_pin = session.post(
      verify_pin_url,
      headers=headers,
      json={"request_key": request_key, "identity_type": "pin", "identifier": PIN},
      timeout=10,
  )
  token_details = res_pin.json().get("data", {})
  bearer_token = token_details.get("token")

  # Step C: Get Auth Code
  token_headers = {
      "Authorization": f"Bearer {bearer_token}",
      "User-Agent": (
          "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
      ),
  }
  auth_code_payload = {
      "fyers_id": USER_ID,
      "app_id": APP_ID,
      "redirect_uri": REDIRECT_URI,
      "appType": "100",
      "code_challenge": "",
      "state": "None",
      "scope": "",
      "nonce": "",
      "response_type": "code",
      "create_cookie": True,
  }
  res_token = session.post(
      "https://api-t1.fyers.in/api/v3/token",
      headers=token_headers,
      json=auth_code_payload,
      timeout=10,
  )
  auth_url = res_token.json().get("Url")

  parsed = urllib.parse.urlparse(auth_url)
  auth_code = urllib.parse.parse_qs(parsed.query)["auth_code"][0]

  # Step D: Exchange auth_code with appIdHash for Access Token
  app_id_hash = hashlib.sha256(f"{APP_ID}:{SECRET_KEY}".encode()).hexdigest()
  validate_url = "https://api-t1.fyers.in/api/v3/validate-authcode"
  res_access = session.post(
      validate_url,
      headers=headers,
      json={
          "grant_type": "authorization_code",
          "appIdHash": app_id_hash,
          "code": auth_code,
      },
      timeout=10,
  )
  access_token = res_access.json().get("access_token")

  if access_token:
    with open(TOKEN_PATH, "w", encoding="utf-8") as f:
      f.write(access_token)
    print("🎉 SUCCESS: Fyers 100% Headless Token Generated & Saved!")
    print(f"🔑 Access Token: {access_token[:15]}...{access_token[-5:]}")
    print(f"📁 Path: {TOKEN_PATH}")
    print("=" * 70)
  else:
    print(f"❌ Failed to exchange token: {res_access.text}")

except Exception as e:
  print(f"❌ Headless Fyers Auth Exception: {e}")
  print(
      "ℹ️ Note: If Fyers security policy requires browser, fyers_live_desk.py"
      " will serve as 1-click fallback."
  )