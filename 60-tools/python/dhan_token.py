"""
dhan_token.py -- get a fresh Dhan access token and write it into secrets\dhan.env.

Modes:
  python dhan_token.py renew     # refresh a still-valid token (no PIN/TOTP)
  python dhan_token.py login     # mint a new token (asks PIN + TOTP, stores neither)
  python dhan_token.py status    # just show current token validity

Never prints the token. Never stores PIN. Rewrites dhan.env in place.
"""
import base64, datetime, getpass, json, os, sys, urllib.error, urllib.parse, urllib.request

SECRETS = r"C:\kite-agent\secrets\dhan.env"
AUTH = "https://auth.dhan.co"
API  = "https://api.dhan.co/v2"

def load_env(path):
    vals, order = {}, []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8-sig") as f:
            for line in f:
                s = line.strip()
                if s and not s.startswith("#") and "=" in s:
                    k, v = s.split("=", 1)
                    k = k.strip()
                    if k not in vals:
                        order.append(k)
                    vals[k] = v.strip().strip('"').strip("'")
    return vals, order

def save_env(path, vals, order):
    keys = order + [k for k in vals if k not in order]
    body = "\n".join("%s=%s" % (k, vals[k]) for k in keys if k in vals) + "\n"
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8", newline="\n") as f:
        f.write(body)
    os.replace(tmp, path)

def token_exp(tok):
    try:
        p = tok.split(".")[1]; p += "=" * (-len(p) % 4)
        return datetime.datetime.fromtimestamp(
            json.loads(base64.urlsafe_b64decode(p))["exp"])
    except Exception:
        return None

def hours_left(tok):
    e = token_exp(tok)
    if not e:
        return None
    return (e - datetime.datetime.now()).total_seconds() / 3600.0

def request(url, method="GET", headers=None):
    req = urllib.request.Request(url, method=method)
    req.add_header("Accept", "application/json")
    for k, v in (headers or {}).items():
        req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return -1, repr(e)

def adopt(new_token, vals, order, meta):
    vals["DHAN_ACCESS_TOKEN"] = new_token
    save_env(SECRETS, vals, order)
    h = hours_left(new_token)
    print("\nNEW TOKEN SAVED to", SECRETS)
    print("  length      :", len(new_token))
    print("  expiry (jwt):", token_exp(new_token))
    if h is not None:
        print("  hours valid :", round(h, 2))
    for k in ("dhanClientName", "dhanClientUcc", "expiryTime", "givenPowerOfAttorney"):
        if k in meta:
            print("  %-12s: %s" % (k, meta[k]))

def do_status(vals):
    tok = vals.get("DHAN_ACCESS_TOKEN", "")
    if not tok:
        print("no token in dhan.env"); return
    h = hours_left(tok)
    print("token length:", len(tok), "| expiry:", token_exp(tok),
          "| hours left:", round(h, 2) if h is not None else "?")
    st, body = request(API + "/profile", headers={
        "access-token": tok, "client-id": vals.get("DHAN_CLIENT_ID", "")})
    print("\nGET /profile -> HTTP", st)
    print(body[:900])

def do_renew(vals, order):
    tok = vals.get("DHAN_ACCESS_TOKEN", "")
    cid = vals.get("DHAN_CLIENT_ID", "")
    if not tok or not cid:
        print("dhan.env needs DHAN_CLIENT_ID and DHAN_ACCESS_TOKEN for renew."); return
    h = hours_left(tok)
    if h is not None and h <= 0:
        print("Current token already expired. RenewToken cannot be used.")
        print("Run:  python dhan_token.py login"); return
    st, body = request(API + "/RenewToken", headers={
        "access-token": tok, "dhanClientId": cid})
    print("GET /RenewToken -> HTTP", st)
    if st != 200:
        print(body[:900])
        print("\nRenew failed. Fall back to:  python dhan_token.py login")
        return
    try:
        d = json.loads(body)
    except Exception:
        print("unparseable response:", body[:400]); return
    new = d.get("accessToken") or d.get("data", {}).get("accessToken")
    if not new:
        print("no accessToken in response. keys:", list(d.keys())); return
    adopt(new, vals, order, d)

def do_login(vals, order):
    cid = vals.get("DHAN_CLIENT_ID", "")
    if not cid:
        cid = input("Dhan client id: ").strip()
        vals["DHAN_CLIENT_ID"] = cid
        if "DHAN_CLIENT_ID" not in order:
            order.insert(0, "DHAN_CLIENT_ID")

    print("\nThis needs your 6-digit Dhan PIN and a TOTP code.")
    print("Neither is stored on disk by this script.")
    pin = getpass.getpass("Dhan PIN (hidden): ").strip()

    totp = ""
    secret = vals.get("DHAN_TOTP_SECRET", "")
    if secret:
        try:
            import pyotp
            totp = pyotp.TOTP(secret).now()
            print("TOTP generated from stored secret.")
        except ImportError:
            print("pyotp not installed; falling back to manual entry.")
        except Exception as e:
            print("stored TOTP secret unusable:", repr(e))
    if not totp:
        totp = input("6-digit TOTP from your authenticator: ").strip()

    if not pin or not totp:
        print("PIN or TOTP empty. Aborting."); return

    qs = urllib.parse.urlencode({"dhanClientId": cid, "pin": pin, "totp": totp})
    st, body = request(AUTH + "/app/generateAccessToken?" + qs, method="POST")
    print("\nPOST /app/generateAccessToken -> HTTP", st)
    if st != 200:
        print(body[:900])
        print("\nCommon causes: TOTP not enabled on the account (Dhan Web >")
        print("DhanHQ Trading APIs > Setup TOTP), wrong PIN, or a stale TOTP")
        print("code - they rotate every 30 seconds, so retry with a fresh one.")
        return
    try:
        d = json.loads(body)
    except Exception:
        print("unparseable response:", body[:400]); return
    new = d.get("accessToken") or d.get("data", {}).get("accessToken")
    if not new:
        print("no accessToken in response. keys:", list(d.keys())); return
    adopt(new, vals, order, d)

def main():
    mode = (sys.argv[1] if len(sys.argv) > 1 else "status").lower()
    if not os.path.exists(SECRETS):
        print("MISSING", SECRETS); return
    vals, order = load_env(SECRETS)
    if mode == "status":
        do_status(vals)
    elif mode == "renew":
        do_renew(vals, order)
    elif mode == "login":
        do_login(vals, order)
    else:
        print("usage: python dhan_token.py [status|renew|login]")

if __name__ == "__main__":
    main()