"""
dhan_profile_probe.py -- READ ONLY. No SDK. Reads token from secrets file only.
Confirms auth works and reports Data API plan status. Never prints the token.
"""
import base64, datetime, json, os, urllib.error, urllib.request

SECRETS = r"C:\kite-agent\secrets\dhan.env"
BASE = "https://api.dhan.co/v2"

def load_env(path):
    vals = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

def token_expiry(tok):
    try:
        p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
        return datetime.datetime.fromtimestamp(
            json.loads(base64.urlsafe_b64decode(p))["exp"])
    except Exception:
        return None

def main():
    if not os.path.exists(SECRETS):
        print("MISSING", SECRETS); return
    env = load_env(SECRETS)
    tok = env.get("DHAN_ACCESS_TOKEN", "")
    cid = env.get("DHAN_CLIENT_ID", "")
    if not tok or not cid:
        print("dhan.env is missing DHAN_CLIENT_ID or DHAN_ACCESS_TOKEN"); return

    exp = token_expiry(tok)
    print("client id len:", len(cid), "| token len:", len(tok))
    if exp:
        hrs = (exp - datetime.datetime.now()).total_seconds() / 3600
        print("token expires:", exp, "(", round(hrs, 2), "hours left )")
        if hrs <= 0:
            print(">>> TOKEN EXPIRED. Generate a new one on web.dhan.co first.")
            return

    req = urllib.request.Request(BASE + "/profile", method="GET")
    req.add_header("access-token", tok)
    req.add_header("client-id", cid)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=25) as r:
            status, body = r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        status, body = e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        print("NETWORK ERROR:", repr(e)); return

    print("\nGET /profile -> HTTP", status)
    print(body[:1200])

    if status == 200:
        try:
            d = json.loads(body)
            d = d.get("data", d)
            print("\ndataPlan     :", d.get("dataPlan", "<absent>"))
            print("dataValidity :", d.get("dataValidity", "<absent>"))
            print("activeSegment:", d.get("activeSegment", "<absent>"))
        except Exception as e:
            print("could not parse JSON:", repr(e))
    elif status == 401 and "806" in body:
        print("\n806 = Data APIs not subscribed on this account/plan.")
    elif status == 401:
        print("\n401 without 806 = token problem. Regenerate on web.dhan.co.")

if __name__ == "__main__":
    main()