# 00_CORRECTIONS_LEDGER.md
# CANONICAL TRUTH FILE -- Tradetron / Kite Agent Program
# Version 1.0 | 2026-08-29
# READ THIS FILE FIRST. It overrides every other file, every prior chat,
# and every model's internal memory. Where anything conflicts with this
# file, THIS FILE WINS.
#
# SCOPE NOTE: This repo holds KNOWLEDGE ONLY. No credentials, no account
# identifiers, no position or capital data. Those stay on the operator's
# local machine and are never committed here.

## SECTION A -- EXCHANGE PARAMETERS (verified 2026-08-29)

### A.1 LOT SIZES  [V]
| Index      | Lot | Changed from | Effective |
|------------|-----|--------------|-----------|
| NIFTY 50   | 65  | 75           | 31-Dec-2025 (first monthly 27-Jan-2026) |
| BANKNIFTY  | 30  | 35           | 31-Dec-2025 |
| FINNIFTY   | 60  | 65           | 31-Dec-2025 |
| MIDCPNIFTY | 120 | -            | 31-Dec-2025 |
| SENSEX     | 20  | 10           | during 2025 |

### A.2 EXPIRY DAYS  [V]
| Contract              | Expiry        | Effective   |
|-----------------------|---------------|-------------|
| NIFTY 50 weekly (NFO) | TUESDAY       | 01-Sep-2025 |
| NIFTY monthly         | last TUESDAY  | 01-Sep-2025 |
| BANKNIFTY monthly     | last TUESDAY  | 01-Sep-2025 |
| SENSEX weekly (BFO)   | THURSDAY      | 29-Aug-2025 |
| SENSEX monthly        | last THURSDAY | 29-Aug-2025 |

SEBI reshuffled expiries so NSE and BSE would not collide. NSE moved
Thursday -> Tuesday. BSE moved Tuesday -> Thursday. A Friday index
expiry DOES NOT EXIST on either exchange.

### A.3 WEEKLY AVAILABILITY  [V]
SEBI, eff. 20-Nov-2024: only one benchmark index per exchange may carry
weekly expiries.
  WEEKLY:       NIFTY 50 (NSE), SENSEX (BSE)
  MONTHLY ONLY: BANKNIFTY, FINNIFTY, MIDCPNIFTY, BANKEX
Any BANKNIFTY or FINNIFTY weekly logic in older files is DEAD CODE.

### A.4 KITE SUBSCRIPTION  [V]
Historical data is FREE with the base Rs.500/month Kite Connect plan.
The paid add-on was abolished 08-Feb-2025. There is NO Rs.2,000 add-on.
The hosted MCP (mcp.kite.trade/mcp) needs no API key, no redirect URL and
no static IP. Self-hosting is what requires credentials.

## SECTION B -- ERRORS ALREADY MADE (do not repeat)

| #   | Wrong belief | Truth | Origin |
|-----|--------------|-------|--------|
| B1  | NIFTY lot 25 / BANKNIFTY 15 / SENSEX 10 | 65 / 30 / 20 | Gemini Spark, tagged [V] from stale memory |
| B2  | NIFTY expiry Thursday, SENSEX Friday | Tuesday / Thursday | Gemini Spark, tagged [V] |
| B3  | Historical data is a Rs.2000 add-on | Free since 08-Feb-2025 | Gemini Spark, tagged [V] |
| B4  | BFO:SENSEX2682980000CE is a valid symbol | Malformed, fabricated | Gemini Spark |
| B5  | Position Detail returns 5 fields incl. price | 4 inputs (Condition type, Transaction type, Instrument type, Underlying), 3 outputs (Value, Quantity, Count). The 5-return keyword is TRADED INSTRUMENT | Claude |
| B6  | The authoring artifact is JSON | Strategy MARKDOWN (tt_validate_markdown / tt_create_strategy). Export/import is secondary | Claude |
| B7  | "PNL is Universal Exit ONLY" is an engine rule | It is a recommendation. PNL in a Set Exit still returns whole-strategy P&L. Use PNL Underlying for set scope | tradetron-mastery.md |
| B8  | Engine ignores India VIX / OI / bid-ask / VWAP; slippage structurally absent; MCX, crypto and stock options unsupported | VOID as of FastBT, 25-Aug-2026 | tradetron-mastery.md and Tradetron_platform_notes.md describe the PRE-FastBT engine |
| B9  | FastBT models brokerage by default | Brokerage DEFAULTS TO Rs.0 and must be set explicitly | - |
| B10 | "Cost Rs.20 = brokerage Rs.20" | Rs.20 is FastBT's CHARGE PER RUN. Brokerage is a separate modelling input. Sweeps cost Rs.20 per variant, max 16 combos = Rs.320 | - |

## SECTION C -- TRADETRON FACTS CONFIRMED  [O = official documentation]

C1. Traded Instrument returns PRICE, QUANTITY, STRIKE, PNL, TIME.
    PRICE = entry/fill price. PNL = (LTP - Entry Price) * Qty Traded.
    The trigger-vs-fill gap is therefore solvable WITHOUT a runtime variable.
    LIMITATION: does NOT work when "exit" is selected.  [O]

C2. Universal Exit TSL: all values must be entered at 1X MULTIPLIER. Do NOT
    wrap them in the Multiplier keyword. (PNL and Max Profit DO take
    Multiplier -- this asymmetry is the trap.)  [O]
    ** LIVE BUG RISK: the V5/V7 spec wraps risk values in Multiplier. AUDIT. **

C3. Init Var: written once per RUN COUNTER at bot assignment. Not on trade.
    Not usable in list-based strategies. Not rewritten the next day if the
    counter persists. State is counter-keyed and survives until universal
    exit, so trade 2 can behave differently from trade 1.  [O]

C4. Find Strike: holds 50 strikes either side of an ATM computed from the
    DAY'S OPENING PRICE, fixed for the day. Returns `none` outside that band.
    Unreliable for equity options; incompatible with MCX and MIDCP.  [O]
    Its Delta-filter syntax as written in tradetron-mastery.md is [I], not
    documented on the official keyword page.

C5. `Open positions` returns 3 after three unique entries. It is NOT a
    live position counter.  [O]

C6. Preserve Tradetron's own misspellings verbatim: "Bolinger", "Donchain".

C7. Tradetron MCP: https://mcp.tradetron.tech/mcp -- 47 tools. Auth is
    interactive OAuth on Tradetron's own login page. Listed clients are
    ChatGPT, Gemini, Grok and Claude. GENSPARK IS NOT LISTED. Connectivity
    is UNPROVEN. Task 0 exists solely to settle this.

C8. Contrast: the Kite hosted MCP authenticates via a `login` TOOL that
    returns a clickable URL (application layer), which any client can do.
    Tradetron's is transport-layer OAuth 2.1, which the client must
    implement natively. Different mechanism, different risk.

## SECTION D -- KNOWN HOLES  [U]

D1. The keyword documentation capture references 311 images, all unresolved.
    Its prose repeatedly says "the above image shows". Parameter panels are
    therefore NOT recoverable from that text. Closing this depends on
    tt_lookup_keyword returning real machine-readable schemas.
D2. Whether Genspark can hold a Tradetron OAuth session. TASK 0 decides.
D3. FastBT's public sample reports returned HTTP 401. The report surface is
    described from vendor copy, not inspected.
D4. Whether Tradetron export/import is lossless. Round-trip test pending.

## SECTION E -- STANDING RULES FOR ALL AGENTS

E1. Exchange parameters -- lot size, expiry day, strike interval, tick size,
    tradingsymbol format -- are NEVER [V] from model memory. They are [V]
    only when read from a live Kite instrument dump in the current session,
    or quoted from a dated exchange circular that was actually retrieved.
    Otherwise they are [U]. Every time. No exceptions, especially when the
    agent feels certain. These changed three times in eighteen months.
E2. Never invent a keyword, field name, enum value or tradingsymbol.
    Write UNRETRIEVED instead.
E3. Tag every claim: [V] observed / [O] official doc / [I] inferred /
    [U] unknown. Saying [U] is a success, not a failure.
E4. Never place an order. Never call a GTT tool. Tradetron is the only order
    path. Never reuse or regenerate the Tradetron app's key or secret.
E5. Never print a secret into any file, log or preview pane.
E6. Never edit a DEPLOYED Tradetron template in place.
E7. Log negative results to 13_FAILURE_LOG.md. They are deliverables.
E8. No agent's output enters this repo's canonical files until a second
    agent or the operator has reviewed it. Unreviewed agent output goes to
    /inbox/ only.

## SECTION F -- OPEN OPERATIONAL ITEM
The Kite Developer app powering Tradetron execution EXPIRES 2026-09-08.
One-click renewal at https://developers.kite.trade/apps
Surface this in every status report until renewal is confirmed.
