"""
B1 - KITE <-> DHAN STRUCTURED JOIN (final, verified against B0 probe output)
Join key: (underlying, expiry_iso, strike_paise_int, option_type)
No symbol parsing. No hard-coded lot sizes. No hard-coded expiry dates.
Fail-closed: every Kite option row must find exactly one Dhan row.
"""
import os
from datetime import datetime
import pandas as pd

BRAIN  = r"C:\kite-agent\brain"
KITE   = os.path.join(BRAIN, r"20-market-data\datasets\instruments-2026-08-31.csv")
DHAN   = os.path.join(BRAIN, r"20-market-data\datasets\dhan-scrip-master-2026-08-31.csv")
STATUS = os.path.join(BRAIN, r"70-ops\status")

UNDERLYINGS = ["NIFTY", "SENSEX"]
EXCH_MAP    = {"NFO": "NSE", "BFO": "BSE"}   # Kite exchange -> Dhan EXCH_ID
DHAN_TICK_DIVISOR = 100.0                    # verified by B0: Dhan tick is in paise

fail = []
warn = []

def strike_paise(series):
    """Strike as integer paise. Avoids float equality failures."""
    return (pd.to_numeric(series, errors="coerce") * 100).round().astype("Int64")

def iso_date(series):
    """Both files were verified ISO in B0. Coerce anyway; NaT is reported, not hidden."""
    return pd.to_datetime(series, errors="coerce", format="%Y-%m-%d")

# ---------------------------------------------------------------- load
k = pd.read_csv(KITE, dtype=str, keep_default_na=False, encoding="utf-8-sig")
d = pd.read_csv(DHAN, dtype=str, keep_default_na=False, encoding="utf-8-sig")

ko = k[k["name"].isin(UNDERLYINGS) & k["instrument_type"].isin(["CE", "PE"])].copy()
do = d[(d["INSTRUMENT"] == "OPTIDX")
       & d["UNDERLYING_SYMBOL"].isin(UNDERLYINGS)
       & d["OPTION_TYPE"].isin(["CE", "PE"])].copy()

print(f"KITE option rows : {len(ko)}")
print(f"DHAN option rows : {len(do)}")

# ---------------------------------------------------------------- keys
ko["k_expiry"] = iso_date(ko["expiry"])
do["d_expiry"] = iso_date(do["SM_EXPIRY_DATE"])
ko["k_strike"] = strike_paise(ko["strike"])
do["d_strike"] = strike_paise(do["STRIKE_PRICE"])

for df, cols, label in ((ko, ["k_expiry", "k_strike"], "KITE"),
                        (do, ["d_expiry", "d_strike"], "DHAN")):
    for c in cols:
        n = int(df[c].isna().sum())
        if n:
            fail.append(f"{label}: {n} rows with unparseable {c}")

ko["KEY"] = list(zip(ko["name"], ko["k_expiry"], ko["k_strike"], ko["instrument_type"]))
do["KEY"] = list(zip(do["UNDERLYING_SYMBOL"], do["d_expiry"], do["d_strike"], do["OPTION_TYPE"]))

# ---------------------------------------------------------------- duplicate keys
dup = do["KEY"].duplicated(keep=False)
n_dup = int(dup.sum())
if n_dup:
    fail.append(f"DHAN: {n_dup} rows share a join key (would fan out the merge)")
    print("\nDHAN duplicate-key sample:")
    print(do.loc[dup, ["SECURITY_ID", "UNDERLYING_SYMBOL", "SM_EXPIRY_DATE",
                       "STRIKE_PRICE", "OPTION_TYPE"]].head(10).to_string(index=False))
do_u = do.drop_duplicates(subset="KEY", keep="first")

k_dup = int(ko["KEY"].duplicated().sum())
if k_dup:
    fail.append(f"KITE: {k_dup} duplicate join keys")

# ---------------------------------------------------------------- merge
m = ko.merge(
    do_u[["KEY", "SECURITY_ID", "EXCH_ID", "LOT_SIZE", "TICK_SIZE",
          "SM_FREEZE_QTY", "EXPIRY_FLAG"]],
    on="KEY", how="outer", indicator=True
)

matched   = m[m["_merge"] == "both"]
kite_only = m[m["_merge"] == "left_only"]
dhan_only = m[m["_merge"] == "right_only"]

print(f"\nMATCHED    : {len(matched)}")
print(f"KITE_ONLY  : {len(kite_only)}   <-- must be 0 (fail-closed)")
print(f"DHAN_ONLY  : {len(dhan_only)}   <-- expected, informational")

if len(kite_only):
    fail.append(f"{len(kite_only)} Kite option rows found no Dhan row")
    print("\nKITE_ONLY sample:")
    print(kite_only[["tradingsymbol", "name", "expiry", "strike",
                     "instrument_type"]].head(20).to_string(index=False))
    print("\nKITE_ONLY grouped by (name, expiry):")
    print(kite_only.groupby(["name", "expiry"]).size().to_string())

# ---------------------------------------------------------------- field agreement
ml = matched.copy()
ml["k_lot"] = pd.to_numeric(ml["lot_size"], errors="coerce").astype("Int64")
ml["d_lot"] = pd.to_numeric(ml["LOT_SIZE"], errors="coerce").round().astype("Int64")
lot_bad = ml[ml["k_lot"] != ml["d_lot"]]
if len(lot_bad):
    fail.append(f"{len(lot_bad)} rows disagree on lot size")
    print("\nLOT DISAGREEMENTS:")
    print(lot_bad[["tradingsymbol", "k_lot", "d_lot"]].head(20).to_string(index=False))

ml["k_tick"] = pd.to_numeric(ml["tick_size"], errors="coerce")
ml["d_tick"] = pd.to_numeric(ml["TICK_SIZE"], errors="coerce") / DHAN_TICK_DIVISOR
tick_bad = ml[(ml["k_tick"] - ml["d_tick"]).abs() > 1e-9]
if len(tick_bad):
    warn.append(f"{len(tick_bad)} rows disagree on tick size after /100 rescale")

ml["exp_exch"] = ml["exchange"].map(EXCH_MAP)
exch_bad = ml[ml["exp_exch"] != ml["EXCH_ID"]]
if len(exch_bad):
    fail.append(f"{len(exch_bad)} rows disagree on exchange mapping")

# ---------------------------------------------------------------- observed reference tables
print("\nOBSERVED LOT SIZE (measured, not assumed):")
print(ml.groupby(["name", "k_lot"]).size().to_string())

print("\nOBSERVED FREEZE QTY -> max lots per single order:")
fz = ml.copy()
fz["freeze"]   = pd.to_numeric(fz["SM_FREEZE_QTY"], errors="coerce")
fz["max_lots"] = (fz["freeze"] / fz["k_lot"]).astype(float)
print(fz.groupby("name")[["freeze", "max_lots"]].min().to_string())

print("\nOBSERVED EXPIRY_FLAG distribution (do NOT use to classify weekly/monthly):")
print(ml.groupby(["name", "EXPIRY_FLAG"]).size().to_string())

# ---------------------------------------------------------------- evidence artifact
os.makedirs(STATUS, exist_ok=True)
stamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
path  = os.path.join(STATUS, f"bridge-report-{stamp}.md")

verdict = "PASS" if not fail else "FAIL"
with open(path, "w", encoding="utf-8") as f:
    f.write(f"# KITE-DHAN BRIDGE REPORT\n\nGenerated: {stamp}\n\n")
    f.write(f"- Kite option rows: {len(ko)}\n- Dhan option rows: {len(do)}\n")
    f.write(f"- Dhan duplicate keys: {n_dup}\n")
    f.write(f"- MATCHED: {len(matched)}\n- KITE_ONLY: {len(kite_only)}\n")
    f.write(f"- DHAN_ONLY: {len(dhan_only)}\n\n## VERDICT: {verdict}\n\n")
    for x in fail:
        f.write(f"- FAIL: {x}\n")
    for x in warn:
        f.write(f"- WARN: {x}\n")
    f.write("\n## OBSERVED LOT SIZE\n```\n" + ml.groupby(["name", "k_lot"]).size().to_string() + "\n```\n")
    if len(kite_only):
        f.write("\n## KITE_ONLY BY (name, expiry)\n```\n"
                + kite_only.groupby(["name", "expiry"]).size().to_string() + "\n```\n")
    if len(matched):
        f.write("\n## SAMPLE MATCHES\n```\n"
                + matched[["tradingsymbol", "SECURITY_ID", "EXCH_ID"]].head(10).to_string(index=False)
                + "\n```\n")

print(f"\nEvidence: {path}")
print("\n=== VERDICT ===")
if fail:
    print("FAIL")
    for x in fail:
        print("  -", x)
    print("Do NOT proceed to Phase C.")
else:
    print("PASS - every Kite option row matched exactly one Dhan row.")
    for x in warn:
        print("  WARN:", x)
