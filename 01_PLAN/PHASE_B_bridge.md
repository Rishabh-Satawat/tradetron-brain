# PHASE B — KITE/DHAN CONTRACT BRIDGE
STATUS: PASS (2026-09-01, verified twice)
Script: 60-tools\python\bridge_structured_join.py
Evidence: 70-ops\status\B1_join_2026-09-01.txt
          70-ops\status\bridge-report-2026-09-01_092322.md
          70-ops\status\bridge-report-2026-09-01_132233.md

## ARCHITECTURE
Pure structured join. No symbol parsing anywhere in Phase B.
Join key: (underlying, expiry_iso, strike_as_integer_paise, option_type)
  Kite side: name, expiry, strike, instrument_type
  Dhan side: UNDERLYING_SYMBOL, SM_EXPIRY_DATE, STRIKE_PRICE, OPTION_TYPE
Strike compared as integer paise to avoid float equality failure.
Symbol parser lives in Phase D0 (Tradetron trade-log parsing) where it is needed.

## B0 — PROBE (done)
Script: 90-scripts\b0_probe.py
Prints both headers, option universe by exchange/segment, distinct tick and lot sizes,
every expiry with weekday, nearest and farthest symbols per underlying, Dhan samples,
stale-row count. Closed six unknowns. See 00_CORRECTIONS_LEDGER.md V1-V9.

## B1 — JOIN (done, PASS)
KITE option rows : 4072  (NIFTY 1594, SENSEX 2478)
DHAN option rows : 7094
MATCHED          : 4072
KITE_ONLY        : 0      <-- fail-closed criterion, must be 0
DHAN_ONLY        : 3022   <-- expected: Dhan lists contracts Kite does not, informational

Fail-checks, all silent:
  - unparseable expiry or strike on either side
  - duplicate join keys on either side
  - lot size disagreement
  - exchange mapping (NFO->NSE, BFO->BSE)
Warn-check, silent: tick size after /100 rescale.

## OBSERVED REFERENCE TABLES (measured, not assumed)
Lot size   : NIFTY 65 (1594 rows), SENSEX 20 (2478 rows)
Freeze qty : NIFTY 1756 units = 27 lots/order ; SENSEX 1001 units = 50 lots/order

## NOT DONE IN PHASE B
No lot-size assertion against a hard-coded map. Lot sizes are REPORTED, not asserted.
No weekly/monthly classification. EXPIRY_FLAG is unreliable (V5).

## PASS CRITERION
KITE_ONLY == 0 AND zero entries in the fail list. No percentage thresholds.
No "operator judgment" branch. Rejected three times: 95% conditional, <5% tolerance.
