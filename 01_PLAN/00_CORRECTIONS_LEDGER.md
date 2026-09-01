# CORRECTIONS LEDGER — VERIFIED FACTS
All entries below were printed by a script on this machine, or cited to a URL.
Evidence: 70-ops\status\B0_probe_2026-09-01.txt, B1_join_2026-09-01.txt

## V1 — Dhan TICK_SIZE is in paise (scale /100)
Kite tick_size = 0.05 ; Dhan TICK_SIZE = 5.0000 on identical contracts.
Slippage MUST use 0.05. Using 5.00 inflates cost 100x.

## V2 — Dhan LOT_SIZE is a float string ("65.0", "20.0")
int(x) raises ValueError. Use int(float(x)).

## V3 — Dhan header has a trailing comma
Column 33 parses as "Unnamed: 32". Any len(columns)==32 check breaks.

## V4 — Dhan INSTRUMENT_TYPE is inconsistent across exchanges
NSE NIFTY rows show "OP"; BSE SENSEX rows show "OPTIDX".
Filter on INSTRUMENT == "OPTIDX" instead. Never on INSTRUMENT_TYPE.

## V5 — EXPIRY_FLAG cannot classify weekly vs monthly
NIFTY: M=912, W=682. SENSEX: H=260, M=454, Q=346, W=1418.
NIFTY "M" includes far-dated 2031 contracts. Classify from the expiry DATE.

## V6 — Expiry day is NOT always Tuesday/Thursday
NIFTY 2026-11-23 = Monday. NIFTY 2029-12-24 = Monday (Dec 25 2029 = Tue, Christmas).
Holiday shift moves expiry back one business day.
NEVER derive expiry as "last Tuesday of month". ALWAYS read from the instrument dump.
HYPOTHESIS for C0: 2026-11-24 is an NSE holiday. Confirm against circular.

## V7 — Symbol grammar (both forms verified against real rows)
Weekly : {UND}{YY}{M}{DD}{STRIKE}{CE|PE}   e.g. NIFTY2690124200CE, SENSEX2690377300CE
Monthly: {UND}{YY}{MMM}{STRIKE}{CE|PE}     e.g. NIFTY31JUN16500CE, SENSEX31JUN79000CE
Month char map (weekly): 1-9 = Jan-Sep, O=Oct, N=Nov, D=Dec.
RETRACTED: "SENSEX26090578000PE" was fabricated by the Super Agent. No such format exists.

## V8 — Freeze quantity caps single-order size
NIFTY SM_FREEZE_QTY = 1756 units = 27 lots max. SENSEX = 1001 units = 50 lots max.
Scaling ladder 1/2/5/10/20 is safe. Beyond 27 NIFTY lots requires order splitting.

## V9 — Dhan option universe has zero stale rows
NIFTY/SENSEX OPTIDX: 7094 rows, SM_EXPIRY_DATE min 2026-09-01 max 2031-06-26.
CORRECTION OF A PRIOR ASSISTANT CLAIM: the Dhan master was asserted to be cumulative
and to contain expired option rows. False for this subset. The 2024 USDINR rows are
FUTCUR, not OPTIDX. Directional fail-closed still correct, but because Dhan lists
3022 contracts Kite does not, not because of staleness.

## V10 — IPFT: NSE only, not BSE  [U14 CLOSED]
NSE equity options: INR 0.01 per crore of premium value + 18% GST.
Source: https://zerodha.com/charges/ and
https://support.zerodha.com/category/account-opening/resident-individual/ri-charges/articles/ipft-charges
BSE levies no separate IPFT; its transaction charge already embeds an
INR 1 per INR 1 crore Investor Protection Fund contribution.
NOTE: some sources quote INR 10/crore instead of INR 0.01/crore. At our scale the
difference is under one rupee. Record both readings; do not resolve by guessing.

## V11 — STT (unchanged, previously verified)
Options sale of premium: 0.10% through 2026-03-31, then 0.15% from 2026-04-01.
Exercise: 0.125% through 2026-03-31, then 0.15%. STT on exercise is payable by the purchaser.

## V12 — PowerShell here-string array interpolation
A subexpression like git status inside a double-quoted here-string joins the output
array with SPACES, collapsing it to one line. Capture first into a variable using
-join with a newline, then interpolate the variable.

## V13 — Tooling discipline
Python is never pasted at a PS> prompt. "print" at PS> invokes print.exe (the DOS
printer spooler) and emits "Unable to initialize device PRN". "do" is a reserved
PowerShell keyword. See 01_PLAN\00_CONVENTIONS.md.

## V14 — Join is reproducible
bridge_structured_join.py run twice on 2026-09-01 (092322, 132233) produced
identical counts: MATCHED 4072, KITE_ONLY 0, DHAN_ONLY 3022. Idempotent.
