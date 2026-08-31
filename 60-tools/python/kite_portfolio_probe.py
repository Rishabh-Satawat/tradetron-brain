"""
kite_portfolio_probe.py -- READ ONLY.
Proves the Kite Personal session works and snapshots the account.
Snapshots are written OUTSIDE the git repo, because positions and fund
balances must never end up in version control.
"""
import datetime, json, os
from kiteconnect import KiteConnect

SECRETS_DIR = r"C:\kite-agent\secrets"
ENV = os.path.join(SECRETS_DIR, "kite.env")
TOKEN = os.path.join(SECRETS_DIR, "kite_token.json")
SNAPDIR = r"C:\kite-agent\runtime\snapshots"

def load_env(path):
    vals = {}
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                vals[k.strip()] = v.strip().strip('"').strip("'")
    return vals

def try_call(label, fn):
    try:
        out = fn()
        print("  OK   ", label)
        return {"ok": True, "data": out}
    except Exception as e:
        print("  FAIL ", label, "->", repr(e))
        return {"ok": False, "error": repr(e)}

def main():
    env = load_env(ENV)
    api_key = env.get("KITE_API_KEY", "")
    if not os.path.exists(TOKEN):
        print("No token file. Run kite_session.py first.")
        return
    with open(TOKEN, "r", encoding="utf-8") as f:
        tok = json.load(f)

    kite = KiteConnect(api_key=api_key)
    kite.set_access_token(tok["access_token"])

    print("\nProbing Kite Personal endpoints (read only):")
    results = {}
    results["profile"]   = try_call("profile",   kite.profile)
    results["margins"]   = try_call("margins",   kite.margins)
    results["positions"] = try_call("positions", kite.positions)
    results["holdings"]  = try_call("holdings",  kite.holdings)
    results["orders"]    = try_call("orders",    kite.orders)

    print("\nExpected to FAIL on the free Personal tier (this is correct):")
    results["ltp_expected_fail"] = try_call("ltp NIFTY 50",
                                           lambda: kite.ltp(["NSE:NIFTY 50"]))

    # ---- console summary, no rupee values printed to screen beyond totals ----
    pos = results["positions"]
    if pos["ok"]:
        net = pos["data"].get("net", [])
        day = pos["data"].get("day", [])
        open_legs = [p for p in net if p.get("quantity", 0) != 0]
        print("\nPositions: %d net rows, %d day rows, %d OPEN legs"
              % (len(net), len(day), len(open_legs)))
        for p in open_legs:
            print("   %-28s qty=%-6s avg=%-10s pnl=%s"
                  % (p.get("tradingsymbol"), p.get("quantity"),
                     p.get("average_price"), round(p.get("pnl", 0), 2)))

    hold = results["holdings"]
    if hold["ok"]:
        print("Holdings: %d rows" % len(hold["data"]))

    mar = results["margins"]
    if mar["ok"]:
        eq = mar["data"].get("equity", {}).get("available", {})
        print("Equity available cash:", eq.get("live_balance", eq.get("cash")))

    os.makedirs(SNAPDIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d_%H%M%S")
    out = os.path.join(SNAPDIR, "kite-account-%s.json" % stamp)
    with open(out, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, default=str)
    print("\nFull snapshot written to", out)
    print("(that folder is outside the repo - do not move it inside)")

if __name__ == "__main__":
    main()