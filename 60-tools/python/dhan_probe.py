"""dhan_probe.py - read-only connectivity probe. Expiry list only. No orders."""
from __future__ import annotations
import os, sys, json
from pathlib import Path
import requests

ENV = Path(r"C:\kite-agent\secrets\dhan.env")
BASE = "https://api.dhan.co/v2"
# [U] security ids to be confirmed against Dhan scrip master
UNDERLYING = {"NIFTY": 13, "BANKNIFTY": 25, "FINNIFTY": 27, "MIDCPNIFTY": 442}

def load_env() -> dict[str, str]:
    if not ENV.exists():
        sys.exit(f"missing {ENV}")
    out = {}
    for line in ENV.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            out[k.strip()] = v.strip()
    return out

def main() -> int:
    e = load_env()
    tok, cid = e.get("DHAN_ACCESS_TOKEN", ""), e.get("DHAN_CLIENT_ID", "")
    if not tok or not cid:
        sys.exit("token or client id not set")
    print(f"token length: {len(tok)}  client id length: {len(cid)}")
    h = {"access-token": tok, "client-id": cid,
         "Content-Type": "application/json", "Accept": "application/json"}
    body = {"UnderlyingScrip": UNDERLYING["NIFTY"], "UnderlyingSeg": "IDX_I"}
    r = requests.post(f"{BASE}/optionchain/expirylist", headers=h,
                      json=body, timeout=30)
    print(f"HTTP {r.status_code}")
    try:
        print(json.dumps(r.json(), indent=2)[:1500])
    except Exception:
        print(r.text[:1500])
    return 0 if r.status_code == 200 else 1

if __name__ == "__main__":
    sys.exit(main())