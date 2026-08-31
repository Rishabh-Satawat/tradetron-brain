"""
kite_session.py -- interactive daily login for Kite Connect Personal.
Kite access tokens die every morning (~06:00 IST). Run this once each day.
Writes the token to C:\kite-agent\secrets\kite_token.json (never into the repo).
"""
import datetime, json, os, webbrowser
from kiteconnect import KiteConnect

SECRETS_DIR = r"C:\kite-agent\secrets"
ENV = os.path.join(SECRETS_DIR, "kite.env")
TOKEN = os.path.join(SECRETS_DIR, "kite_token.json")

def load_env(path):
    vals = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

def main():
    env = load_env(ENV)
    api_key = env.get("KITE_API_KEY", "")
    api_secret = env.get("KITE_API_SECRET", "")
    if not api_key or not api_secret:
        print("kite.env is missing KITE_API_KEY or KITE_API_SECRET.")
        return

    kite = KiteConnect(api_key=api_key)
    url = kite.login_url()
    print("\n1) A browser window will open. Log in to Zerodha.")
    print("2) You will land on a 127.0.0.1 page that fails to load. THAT IS FINE.")
    print("3) Copy the value of request_token= from the address bar.\n")
    print("If the browser does not open, paste this URL manually:\n", url, "\n")
    try:
        webbrowser.open(url)
    except Exception:
        pass

    request_token = input("Paste request_token here: ").strip()
    if not request_token:
        print("Nothing pasted. Aborting.")
        return

    try:
        data = kite.generate_session(request_token, api_secret=api_secret)
    except Exception as e:
        print("\nLOGIN FAILED:", repr(e))
        print("Common causes: request_token already used (they are single-use),")
        print("token older than a couple of minutes, or wrong api_secret.")
        return

    payload = {
        "access_token": data["access_token"],
        "public_token": data.get("public_token", ""),
        "user_id": data.get("user_id", ""),
        "login_time": str(data.get("login_time", "")),
        "saved_at": datetime.datetime.now().isoformat(timespec="seconds"),
    }
    os.makedirs(SECRETS_DIR, exist_ok=True)
    with open(TOKEN, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)

    print("\nSUCCESS. Token saved to", TOKEN)
    print("user_id:", payload["user_id"], " login_time:", payload["login_time"])
    print("This token is valid until roughly 06:00 IST tomorrow.")

if __name__ == "__main__":
    main()