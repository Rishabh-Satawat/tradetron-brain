# =============================================================================
# File: 60-tools/python/fyers_auth.py
# Description: Automated OAuth 2.0 Token Generator for Fyers API v3
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import threading
import time
import urllib.parse
import webbrowser
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
if not os.path.exists(SECRETS_PATH):
  print(f"❌ BLOCKED - Missing file: {SECRETS_PATH}")
  exit(1)

load_dotenv(SECRETS_PATH)
APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SECRET_KEY = os.getenv("FYERS_SECRET_KEY", "").strip()
REDIRECT_URI = os.getenv(
    "FYERS_REDIRECT_URI", "http://127.0.0.1:5000/fyers/callback"
).strip()

if (
    not APP_ID
    or not SECRET_KEY
    or SECRET_KEY == "paste_your_secret_key_here"
):
  print("❌ BLOCKED - Please enter your actual FYERS_SECRET_KEY in secrets/fyers.env")
  exit(1)

captured_auth_code = None


class FyersCallbackHandler(BaseHTTPRequestHandler):

  def do_GET(self):
    global captured_auth_code
    parsed_path = urllib.parse.urlparse(self.path)
    query_params = urllib.parse.parse_qs(parsed_path.query)

    if "auth_code" in query_params:
      captured_auth_code = query_params["auth_code"][0].strip()
      self.send_response(200)
      self.send_header("Content-type", "text/html; charset=utf-8")
      self.end_headers()
      self.wfile.write(b"""
                <html><body style="font-family:sans-serif; text-align:center; padding-top:50px; background:#0f172a; color:#fff;">
                    <h1 style="color:#22c55e;">&#10004; Fyers Authentication Successful!</h1>
                    <p>Auth code captured. You can close this tab now.</p>
                </body></html>
            """)
    else:
      self.send_response(400)
      self.end_headers()

  def log_message(self, format, *args):
    return


def main():
  print("=" * 65)
  print("🚀 FYERS API v3 — Token Generator")
  print("=" * 65)
  print(f"🔑 App ID      : {APP_ID}")
  print(f"🌐 Redirect URI: {REDIRECT_URI}")

  server = HTTPServer(("127.0.0.1", 5000), FyersCallbackHandler)
  threading.Thread(target=server.serve_forever, daemon=True).start()
  print("🟢 Listener active on http://127.0.0.1:5000/fyers/callback")

  session = fyersModel.SessionModel(
      client_id=APP_ID,
      secret_key=SECRET_KEY,
      redirect_uri=REDIRECT_URI,
      response_type="code",
      grant_type="authorization_code",
  )
  auth_url = session.generate_authcode()
  print("\n🌐 Opening browser for Fyers login...")
  webbrowser.open(auth_url)
  print(f"👉 If browser does not open, visit:\n   {auth_url}\n")
  print("⏳ Waiting for login confirmation in browser...")

  timeout = 90
  start_time = time.time()
  while captured_auth_code is None:
    if time.time() - start_time > timeout:
      print("❌ Timeout waiting for Fyers login.")
      exit(1)
    time.sleep(0.5)

  print(f"✅ Captured auth_code: {captured_auth_code[:12]}...")

  session.set_token(captured_auth_code)
  response = session.generate_token()

  if response.get("s") == "ok":
    access_token = response.get("access_token")
    token_path = r"C:\kite-agent\secrets\fyers_access_token.txt"
    with open(token_path, "w") as f:
      f.write(access_token)

    print("-" * 65)
    print(f"🎉 SUCCESS: Fyers Access Token generated!")
    print(f"🔑 Access Token: {access_token[:15]}...{access_token[-5:]}")
    print(f"📁 Saved to: {token_path}")
    print("-" * 65)

    fyers = fyersModel.FyersModel(
        client_id=APP_ID, is_async=False, token=access_token, log_path=""
    )
    prof = fyers.get_profile()
    if prof.get("s") == "ok":
      print(f"👤 Account Name: {prof.get('data', {}).get('name')}")
      print(f"🆔 Client ID   : {prof.get('data', {}).get('fy_id')}")
      print("=" * 65)
  else:
    print(f"❌ Failed to exchange token: {response}")


if __name__ == "__main__":
  main()