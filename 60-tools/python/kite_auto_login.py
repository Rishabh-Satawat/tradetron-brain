# =============================================================================
# File: 60-tools/python/kite_auto_login.py
# Description: 100% Headless Automated Token Generator for Zerodha Kite Connect
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
import urllib.parse
from dotenv import load_dotenv
from kiteconnect import KiteConnect
import pyotp
import requests

load_dotenv(r"C:\kite-agent\.env")

API_KEY = os.getenv("KITE_API_KEY", "").strip()
API_SECRET = os.getenv("KITE_API_SECRET", "").strip()
USER_ID = os.getenv("KITE_USER_ID", "").strip()
PASSWORD = os.getenv("KITE_PASSWORD", "").strip()
TOTP_SECRET = os.getenv("KITE_TOTP_SECRET", "").replace(" ", "").strip()

print("=" * 70)
print("🚀 ZERODHA KITE CONNECT — 100% HEADLESS ZERO-CLICK TOKEN GENERATOR")
print("=" * 70)

if not API_KEY or not API_SECRET or not USER_ID or not PASSWORD or not TOTP_SECRET:
  print("❌ Error: Missing credentials in C:\\kite-agent\\.env")
  sys.exit(1)

session = requests.Session()
headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    ),
    "Referer": "https://kite.zerodha.com/",
    "X-Kite-Version": "3",
}

try:
  # 1. Login with User ID & Password
  print(f"👤 Authenticating User: {USER_ID}...")
  r1 = session.post(
      "https://kite.zerodha.com/api/login",
      data={"user_id": USER_ID, "password": PASSWORD},
      headers=headers,
      timeout=10,
  )
  res1 = r1.json()

  if res1.get("status") != "success":
    print(f"❌ Login failed: {res1.get('message')}")
    sys.exit(1)

  request_id = res1["data"]["request_id"]
  print("   ✅ Password verified.")

  # 2. Complete 2FA via live TOTP
  totp_val = pyotp.TOTP(TOTP_SECRET).now()
  r2 = session.post(
      "https://kite.zerodha.com/api/twofa",
      data={
          "user_id": USER_ID,
          "request_id": request_id,
          "twofa_value": totp_val,
          "twofa_type": "totp",
      },
      headers=headers,
      timeout=10,
  )
  res2 = r2.json()

  if res2.get("status") != "success":
    print(f"❌ TOTP verification failed: {res2.get('message')}")
    sys.exit(1)

  print(f"   ✅ TOTP {totp_val} verified.")

  # 3. Intercept request_token via 302 Redirect (allow_redirects=False avoids ConnectionRefusedError)
  connect_url = f"https://kite.zerodha.com/connect/login?api_key={API_KEY}&v=3"
  r3 = session.get(connect_url, headers=headers, allow_redirects=False)

  redirect_url = r3.headers.get("Location") or r3.headers.get("location")
  parsed = urllib.parse.urlparse(redirect_url)
  request_token = urllib.parse.parse_qs(parsed.query)["request_token"][0]
  print(f"   ✅ Captured request_token: {request_token[:8]}...")

  # 4. Generate Access Token via KiteConnect SDK
  kite = KiteConnect(api_key=API_KEY)
  data = kite.generate_session(request_token, api_secret=API_SECRET)
  access_token = data["access_token"]
  user_name = data.get("user_name", "Trader")

  # Write to both paths
  paths = [
      r"C:\kite-agent\access_token.txt",
      r"C:\kite-agent\brain\access_token.txt",
  ]
  for p in paths:
    with open(p, "w", encoding="utf-8") as f:
      f.write(access_token)

  print("-" * 70)
  print(f"🎉 SUCCESS: Kite token generated for {user_name}!")
  print(f"🔑 Access Token: {access_token[:12]}...{access_token[-5:]}")
  print("=" * 70)

except Exception as e:
  print(f"❌ Headless Kite Auth Error: {e}")
  print("ℹ️ Note: generate_token.py remains available as 1-click fallback.")