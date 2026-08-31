r"""
dhan_master_parse.py -- READ ONLY, OFFLINE. No token, no network.
Parses the Dhan detailed scrip master using the VERIFIED header from
2026-08-31. Fails loudly if any required column is absent.

Answers: index spot security ids, per-underlying lot sizes, strike steps,
expiry lists, OPTION_TYPE vocabulary, and symbol formats for the bridge.
"""
import csv, datetime, os, sys
from collections import Counter, defaultdict

CSV_PATH = r"C:\kite-agent\brain\20-market-data\datasets\dhan-scrip-master-2026-08-31.csv"
OUT_MD   = r"C:\kite-agent\brain\20-market-data\datasets\dhan-master-summary-2026-08-31.md"

REQUIRED = ["EXCH_ID", "SEGMENT", "SECURITY_ID", "INSTRUMENT",
            "UNDERLYING_SECURITY_ID", "UNDERLYING_SYMBOL", "SYMBOL_NAME",
            "DISPLAY_NAME", "INSTRUMENT_TYPE", "LOT_SIZE", "SM_EXPIRY_DATE",
            "STRIKE_PRICE", "OPTION_TYPE", "TICK_SIZE"]

UNDERLYINGS = ["NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"]

def mode_diff(sorted_vals):
    diffs = Counter()
    for a, b in zip(sorted_vals, sorted_vals[1:]):
        d = round(b - a, 2)
        if d > 0:
            diffs[d] += 1
    return diffs.most_common(3)

def main():
    if not os.path.exists(CSV_PATH):
        print("MISSING FILE:", CSV_PATH); return
    print("file:", CSV_PATH)
    print("size:", round(os.path.getsize(CSV_PATH) / (1024*1024), 2), "MB")

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        header = (csv.reader(f).__next__())
    header = [h.strip() for h in header]
    print("\ncolumns:", len(header))
    missing = [c for c in REQUIRED if c not in header]
    if missing:
        print("\nFATAL: required columns absent:", missing)
        print("header was:", header)
        sys.exit(1)
    print("all", len(REQUIRED), "required columns present")

    instr_counts = Counter()
    opttype_counts = Counter()
    spot = {}
    opts = defaultdict(list)
    total = 0

    with open(CSV_PATH, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            total += 1
            instr = (row.get("INSTRUMENT") or "").strip().upper()
            instr_counts[instr] += 1

            und = (row.get("UNDERLYING_SYMBOL") or "").strip().upper()
            sym = (row.get("SYMBOL_NAME") or "").strip().upper()

            if instr in ("INDEX", "IDX") and sym in UNDERLYINGS:
                spot.setdefault(sym, {
                    "security_id": row.get("SECURITY_ID"),
                    "exch": row.get("EXCH_ID"),
                    "segment": row.get("SEGMENT"),
                    "display": row.get("DISPLAY_NAME"),
                })

            if "OPT" in instr:
                ot = (row.get("OPTION_TYPE") or "").strip().upper()
                if ot:
                    opttype_counts[ot] += 1
                if und in UNDERLYINGS:
                    opts[und].append(row)

    print("\ndata rows:", total)
    print("\n=== INSTRUMENT values ===")
    for k, c in instr_counts.most_common(20):
        print("  %-18s %d" % (k or "<blank>", c))
    print("\n=== OPTION_TYPE vocabulary (options rows only) ===")
    for k, c in opttype_counts.most_common(10):
        print("  %-8s %d" % (k, c))

    print("\n=== INDEX SPOT SECURITY IDS (needed for option-chain calls) ===")
    for u in UNDERLYINGS:
        s = spot.get(u)
        if s:
            print("  %-11s id=%-8s exch=%-5s seg=%-10s %s" % (
                u, s["security_id"], s["exch"], s["segment"], s["display"]))
        else:
            print("  %-11s NOT FOUND as INDEX row  [U]" % u)

    lines = ["---",
             "title: Dhan Scrip Master Summary 2026-08-31",
             "source: https://images.dhan.co/api-data/api-scrip-master-detailed.csv",
             "retrieved_at: %s" % datetime.date.today().isoformat(),
             "evidence_tag: \"[V]\"",
             "---", "",
             "# Dhan Scrip Master Summary", "",
             "Data rows: %d. Columns: %d." % (total, len(header)), "",
             "## OPTION_TYPE vocabulary", ""]
    for k, c in opttype_counts.most_common(10):
        lines.append("- `%s` : %d rows" % (k, c))
    lines += ["", "## Index spot security ids", "",
              "| underlying | security_id | exch | segment |", "|---|---|---|---|"]
    for u in UNDERLYINGS:
        s = spot.get(u)
        lines.append("| %s | %s | %s | %s |" % (
            u, s["security_id"] if s else "NOT FOUND [U]",
            s["exch"] if s else "-", s["segment"] if s else "-"))

    print("\n=== PER-UNDERLYING OPTION CONTRACT SPECS ===")
    for u in UNDERLYINGS:
        rows = opts.get(u, [])
        lines += ["", "## %s options" % u, ""]
        if not rows:
            print("\n%-11s NO OPTION ROWS  [U] check UNDERLYING_SYMBOL naming" % u)
            lines.append("No rows matched `UNDERLYING_SYMBOL == %s`. [U]" % u)
            continue

        lots = Counter((r.get("LOT_SIZE") or "").strip() for r in rows)
        ticks = Counter((r.get("TICK_SIZE") or "").strip() for r in rows)
        expiries = sorted({(r.get("SM_EXPIRY_DATE") or "").strip() for r in rows})
        near = expiries[0] if expiries else ""

        strikes = []
        for r in rows:
            if (r.get("SM_EXPIRY_DATE") or "").strip() == near:
                try:
                    strikes.append(float(r.get("STRIKE_PRICE")))
                except (TypeError, ValueError):
                    pass
        strikes = sorted(set(strikes))
        steps = mode_diff(strikes)

        print("\n%-11s contracts=%d" % (u, len(rows)))
        print("   lot sizes  : %s" % dict(lots))
        print("   tick sizes : %s" % dict(ticks))
        print("   expiries   : %d, nearest=%s" % (len(expiries), near))
        print("   strike step: %s (nearest expiry, %d strikes, %s..%s)" % (
            steps, len(strikes),
            strikes[0] if strikes else "-", strikes[-1] if strikes else "-"))
        for r in rows[:3]:
            print("   id=%-9s %-34s exp=%-12s K=%-10s %s lot=%s" % (
                r.get("SECURITY_ID"), (r.get("DISPLAY_NAME") or "")[:34],
                r.get("SM_EXPIRY_DATE"), r.get("STRIKE_PRICE"),
                r.get("OPTION_TYPE"), r.get("LOT_SIZE")))

        lines += ["Contracts: %d" % len(rows),
                  "", "Lot sizes seen: %s" % dict(lots),
                  "", "Tick sizes seen: %s" % dict(ticks),
                  "", "Strike step (nearest expiry %s): %s" % (near, steps),
                  "", "First 8 expiries: %s" % ", ".join(expiries[:8]),
                  "", "| security_id | display_name | expiry | strike | type | lot |",
                  "|---|---|---|---|---|---|"]
        for r in rows[:5]:
            lines.append("| %s | %s | %s | %s | %s | %s |" % (
                r.get("SECURITY_ID"), r.get("DISPLAY_NAME"),
                r.get("SM_EXPIRY_DATE"), r.get("STRIKE_PRICE"),
                r.get("OPTION_TYPE"), r.get("LOT_SIZE")))

    with open(OUT_MD, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))
    print("\nwrote", OUT_MD)

if __name__ == "__main__":
    main()