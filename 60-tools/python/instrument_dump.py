"""instrument_dump.py - read-only snapshot of the Kite instrument master.
No auth. No orders. Public CSV endpoint only."""
from __future__ import annotations
import io, sys, datetime as dt
from pathlib import Path
import requests, pandas as pd

URL = "https://api.kite.trade/instruments"
OUT = Path(__file__).resolve().parents[2] / "20-market-data" / "datasets"
UNDERLYINGS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

def main() -> int:
    stamp = dt.date.today().isoformat()
    OUT.mkdir(parents=True, exist_ok=True)
    r = requests.get(URL, timeout=60)
    r.raise_for_status()
    df = pd.read_csv(io.StringIO(r.text))
    raw = OUT / f"instruments-{stamp}.csv"
    df.to_csv(raw, index=False)
    print(f"rows={len(df)}  saved={raw}")

    opt = df[df["instrument_type"].isin(["CE", "PE"])].copy()
    opt["expiry"] = pd.to_datetime(opt["expiry"], errors="coerce")
    opt = opt.dropna(subset=["expiry"])

    out = ["# Instrument master snapshot", "",
           f"source: {URL}", f"captured: {stamp}",
           f"total rows: {len(df)}", "evidence: [V] primary, unauthenticated", ""]
    for u in UNDERLYINGS:
        sub = opt[opt["name"] == u]
        if sub.empty:
            out += [f"## {u}", "", "NOT FOUND in dump [U]", ""]
            continue
        exp = sorted(sub["expiry"].dt.date.unique())[:8]
        out += [f"## {u}", "",
                f"segment: {sorted(sub['segment'].unique().tolist())}",
                f"lot_size: {sorted(sub['lot_size'].unique().tolist())}",
                f"option rows: {len(sub)}", "",
                "| expiry | weekday |", "|---|---|"]
        out += [f"| {e.isoformat()} | {e.strftime('%A')} |" for e in exp]
        near = sub[sub["expiry"].dt.date == exp[0]]
        d = near["strike"].sort_values().diff().dropna()
        d = d[d > 0]
        out += ["", f"strike step (nearest expiry, modal): {d.mode().iloc[0] if not d.empty else 'unknown'}", ""]

    md = OUT / f"instrument-summary-{stamp}.md"
    md.write_text("\n".join(out), encoding="utf-8")
    print(f"summary={md}")
    return 0

if __name__ == "__main__":
    sys.exit(main())