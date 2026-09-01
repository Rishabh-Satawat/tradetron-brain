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

## V15 — Repo state verified [prior UNVERIFIED item CLOSED]
Commit d793348 "Phase A+B PASS: Kite-Dhan bridge 4072/4072 reproducible, ledger V1-V14"
Parent 25d0f77 "Brain write 011-013: Dhan probe, token lifecycle, verified-schema master parser"
Grandparent cd75973 "Add dhan_profile_probe.py, write010.ps1, and Dhan master summary"
The hash 25d0f77 was earlier flagged [UNVERIFIED] and struck from the plan.
It is now CONFIRMED as the prior origin/main. Restore it as the Phase-A baseline.
Line endings: .gitattributes added. LF/CRLF warnings on add are expected on Windows.

## Round 4 - Cost model reconciliation (2026-09-01)

V16 KITE TOKEN EXPIRY. App shows "Expires on 09 Oct 2026". The 2026-09-08
    date carried in the hub register was WRONG. Not time-critical.
    Evidence: operator browser check, developers.kite.trade/apps.

V17 ZERODHA ROUNDING ALGORITHM. Zerodha rounds EACH component then sums:
    STT and stamp duty -> nearest whole rupee; brokerage/exch/SEBI/GST -> 2dp.
    GST = 18% x (brokerage + exch + SEBI) on unrounded inputs.
    Proof: 82.86 = 40+24+9.85+8.98+0.03+0 across 5 calculator panels.
    RETRACTS the round-once-at-total design in cost_engine.py, which was
    WRONG (Fixture C: engine 210.89 vs Zerodha 210.61).
    Superseded by 60-tools/python/zerodha_charges.py.
    Evidence: operator screenshots + 70-ops/status/C2_zerodha_recon_2026-09-01.txt

V18 RATE CORRECTIONS. Equity delivery/intraday NSE exch = 0.00307% (NOT
    0.00297%). F&O futures STT = 0.05% sell (NOT 0.02%). F&O options
    brokerage = Rs20 x num_executed_orders (NOT hard-coded Rs40).

V19 CALCULATOR QUANTITY SEMANTICS. The QUANTITY field is the position size
    on ONE side. One SENSEX lot = 20. A buy+sell round trip is 2 ORDERS,
    not 2 lots. Entering 40 for a 1-lot round trip DOUBLES every charge.
    Proof: turnover 27720 = (589+797) x 20.

V20 EXCHANGE SELECTOR IS MATERIAL. SENSEX is BSE. Pricing a SENSEX option
    under NSE inflates exch fee by 9.3% (0.03553% vs 0.0325%).

V21 LIVE TRADE 2026-09-01 - CORRECTED AUDIT. The two Tradetron positions
    are ONE bear put spread on SENSEX 03SEP2026 (long 77700 PE / short
    77200 PE), 4 executed orders, entries 11:45:04 and 11:45:05.
      Buy t/o 21330 | Sell t/o 21569 | GROSS +239.00
      Friction 143.90 | NET +95.10 | friction = 60.2% of gross
      Return on 6179 net debit: 3.87% gross -> 1.54% net
    RETRACTS the GenSpark figure of gross 6190 / net 5960.89, which
    double-counted leg A and fabricated a sell turnover of 23362.

V22 OPERATIONAL RISK - UNPAIRED EXIT. Long leg exited 13:16:02, short leg
    13:50:48. For 34 minutes the account held a BARE SHORT 77200 PE
    (undefined risk, different margin profile). Both legs were labelled
    "Universal Exit" => Tradetron sequencing issue, not discretionary.
    ACTION REQUIRED: paired/atomic exit condition before any live capital.

V23 EXPIRY CROSS-VALIDATION. SENSEX 03SEP2026 = Thursday. Live fills
    independently confirm V6 and the Step-3 holiday calendar. Third
    independent confirmation of the expiry-weekday model.

V24 EMPIRICAL COST BENCHMARKS (BSE, post-2026-04-01, squared off):
      2-leg spread, 4 orders  -> ~Rs144 per cycle  [V] live fills
      4-leg iron fly, 8 orders -> ~Rs211 per cycle [V] Zerodha algorithm
    These are the floor any strategy must clear. Input to verdict-policy.yaml.

<!-- END OF ROUND 4 -->

## SECTION G - MIGRATED FROM ROOT LEDGER

The following facts were present in the historical root ledger and were not duplicated by V1-V24. Original evidence tags are preserved.

### G1. Exchange and platform facts

- NIFTY 50 lot size is 65, BANKNIFTY is 30, FINNIFTY is 60, MIDCPNIFTY is 120, and SENSEX is 20. [V]
- Weekly expiries are available for NIFTY 50 on NSE and SENSEX on BSE; BANKNIFTY, FINNIFTY, MIDCPNIFTY, and BANKEX are monthly-only under the recorded rule. [V]
- Kite historical data is included with the base plan; the formerly cited paid historical-data add-on was abolished on 08-Feb-2025. [V]

### G2. Prior agent errors and Tradetron semantics

- A fabricated BFO SENSEX symbol was rejected as malformed. [B]
- `Position Detail` returns four inputs and three outputs; the five-return keyword is `TRADED INSTRUMENT`. [B]
- The authoring artifact is strategy Markdown; JSON is not the primary authoring format. [B]
- PNL in a Set Exit returns whole-strategy P&L; `PNL Underlying` is required when set scope is intended. [B]
- FastBT can model India VIX, OI, bid-ask, VWAP, slippage, MCX, crypto, and stock options; older engine descriptions that denied these capabilities are pre-FastBT and stale. [B]
- FastBT brokerage defaults to zero and must be overridden explicitly; its separate run charge is not brokerage. [B]

### G3. Official and unresolved Tradetron items

- `Traded Instrument` returns PRICE, QUANTITY, STRIKE, PNL, and TIME; PRICE is entry/fill price and PNL is `(LTP - Entry Price) * Qty Traded`, but exit selection is unsupported. [O]
- Universal Exit TSL values are entered at 1X multiplier; PNL and Max Profit have different multiplier behavior. [O]
- Init Var is written once per run counter at bot assignment, is not trade-scoped, and is not rewritten daily while the counter persists. [O]
- Find Strike uses the day's opening price and a bounded strike band; it returns `none` outside that band and is not reliable for equity options or compatible with MCX/MIDCP. [O]
- `Open positions` is not a live position counter. [O]
- Tradetron's documented spellings `Bolinger` and `Donchain` must be preserved. [O]
- Tradetron MCP connectivity and OAuth behavior remain unproven; the hosted Kite MCP uses a separate application-layer login mechanism. [O]

### G4. Known holes and standing rules

- The keyword documentation references unresolved images, so parameter panels are not recoverable from prose alone. [U]
- FastBT report-surface behavior remains uninspected because the public sample returned HTTP 401. [U]
- Tradetron export/import losslessness remains pending a round-trip test. [U]
- Exchange parameters must come from a current instrument dump or retrieved dated circular; never from model memory. [E1]
- Unknown keyword names, fields, enums, and symbols must be marked UNRETRIEVED rather than invented. [E2]
- Every claim must carry [V], [O], [I], or [U]; [U] is an acceptable result. [E3]
- Agents never place orders or create/modify/delete GTTs, and no deployed Tradetron template is edited in place. [E4-E6]
- Negative results belong in the failure log, and unreviewed agent output stays in `inbox/`. [E7-E8]

### G5. Superseded root-ledger item

The historical root ledger said the Kite Developer app expired on 08-Sep-2026. V16 supersedes that date with the operator-observed 09-Oct-2026 expiry. The stale date is retained only as a contradiction record, not as current truth. [B/U -> V16]

<!-- END OF MIGRATED SECTION G -->
