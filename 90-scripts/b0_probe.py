import sys
import pandas as pd

K = r"C:\kite-agent\brain\20-market-data\datasets\instruments-2026-08-31.csv"
D = r"C:\kite-agent\brain\20-market-data\datasets\dhan-scrip-master-2026-08-31.csv"

print("python :", sys.version)
print("pandas :", pd.__version__)

k = pd.read_csv(K, dtype=str, keep_default_na=False, encoding="utf-8-sig")
d = pd.read_csv(D, dtype=str, keep_default_na=False, encoding="utf-8-sig")

print("\nKITE shape:", k.shape)
print("KITE cols :", list(k.columns))
print("\nDHAN shape:", d.shape)
print("DHAN cols :", list(d.columns))
print("DHAN unnamed cols:", [c for c in d.columns if str(c).startswith("Unnamed")])
print("DHAN INSTRUMENT distinct:", sorted(d["INSTRUMENT"].unique())[:40])

ko = k[k["name"].isin(["NIFTY", "SENSEX"]) & k["instrument_type"].isin(["CE", "PE"])].copy()
print("\n=== KITE option universe (join denominator) ===")
print(ko.groupby(["name", "exchange", "segment", "instrument_type"]).size().to_string())
print("\nKITE distinct tick_size:", sorted(ko["tick_size"].unique()))
print("KITE distinct lot_size :", sorted(ko["lot_size"].unique()))

print("\n=== KITE expiries with weekday ===")
e = ko[["name", "expiry"]].drop_duplicates()
e["dow"] = pd.to_datetime(e["expiry"]).dt.day_name()
print(e.sort_values(["name", "expiry"]).to_string(index=False))

print("\n=== NEAREST vs FARTHEST symbols (monthly grammar check) ===")
for n in ["NIFTY", "SENSEX"]:
    s = ko[ko["name"] == n]
    if s.empty:
        print(n, "NO ROWS")
        continue
    print(n, "NEAREST ", s["expiry"].min(), s[s["expiry"] == s["expiry"].min()]["tradingsymbol"].head(4).tolist())
    print(n, "FARTHEST", s["expiry"].max(), s[s["expiry"] == s["expiry"].max()]["tradingsymbol"].head(4).tolist())

dopt = d[d["UNDERLYING_SYMBOL"].isin(["NIFTY", "SENSEX"]) & d["OPTION_TYPE"].isin(["CE", "PE"])].copy()
print("\n=== DHAN option rows ===", len(dopt))
print("\nDHAN NIFTY sample:")
print(dopt[dopt["UNDERLYING_SYMBOL"] == "NIFTY"].head(3).to_string())
print("\nDHAN SENSEX sample:")
print(dopt[dopt["UNDERLYING_SYMBOL"] == "SENSEX"].head(3).to_string())
print("\nDHAN distinct TICK_SIZE:", sorted(dopt["TICK_SIZE"].unique()))
print("DHAN distinct LOT_SIZE :", sorted(dopt["LOT_SIZE"].unique()))
print("DHAN INSTRUMENT values on these rows:", sorted(dopt["INSTRUMENT"].unique()))
print("DHAN exchange-id col values:", [c for c in dopt.columns if "EXCH" in c.upper()])
stale = (dopt["SM_EXPIRY_DATE"] < "2026-08-31").sum()
print("\nDHAN stale rows (expiry < 2026-08-31):", stale, "of", len(dopt))
print("DHAN SM_EXPIRY_DATE min/max:", dopt["SM_EXPIRY_DATE"].min(), dopt["SM_EXPIRY_DATE"].max())
print("\nDONE")
