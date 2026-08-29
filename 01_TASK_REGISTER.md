# 01_TASK_REGISTER.md
# LIVE PROGRAM STATUS -- Tradetron / Kite Agent Program
# Updated: 2026-08-29
# Status key: [ ] not started  [~] in progress  [x] done  [!] blocked
# This file is the running to-do list. Update it whenever a task closes.

## P0 -- DO THIS WEEKEND

| # | Task | Owner | Status | Notes |
|---|------|-------|--------|-------|
| P0.1 | Install Git, set identity | Operator | [x] | PATH fix required after winget |
| P0.2 | Create GitHub repo tradetron-brain (public) | Operator | [ ] | |
| P0.3 | Clone to C:\kite-agent\brain | Operator | [ ] | |
| P0.4 | Push 00_CORRECTIONS_LEDGER.md | Operator | [ ] | write001.ps1 |
| P0.5 | Push 01_TASK_REGISTER.md | Operator | [ ] | write002.ps1 |
| P0.6 | Send correction prompt to Gemini Spark | Operator | [ ] | includes raw ledger URL |
| P0.7 | Send onboarding prompt to Genspark SuperAgent | Operator | [ ] | must quote Section A.2 back |
| P0.8 | RENEW KITE APP -- expires 2026-09-08 | Operator | [ ] | developers.kite.trade/apps. LIVE CAPITAL DEPENDS ON THIS |
| P0.9 | V7 Universal Exit TSL multiplier audit | Operator | [ ] | See ledger C2. Highest-severity live bug risk. Free to check |
| P0.10 | Report `python --version` and `pip list` | Operator | [ ] | needed to spec the snapshotter |

## MAIN TASK SEQUENCE

| # | Task | Owner | Status | Gate / blocker | Cost |
|---|------|-------|--------|----------------|------|
| 0 | Genspark <-> Tradetron MCP connectivity probe | SuperAgent | [!] | blocked on P0.7 | Rs.0 |
| 0b | Kite instrument-dump probe (lot sizes, expiry weekdays, historical-data permission) | Spark | [!] | blocked on P0.6 | Rs.0 |
| 1 | MCP tool inventory + keyword ground truth | SuperAgent | [!] | blocked on Task 0 | Rs.0 |
| 2 | Strategy Markdown schema + validator silent-failure map | SuperAgent | [!] | blocked on Task 1 | Rs.0 |
| 3 | Instruments, strikes, expiries; Q1-Q8 closure | SuperAgent | [ ] | patch issued, not executed | Rs.0 |
| 4 | Runtime variables, state, RESET AUDIT | SuperAgent | [ ] | shrunk -- Traded Instrument PRICE solves trigger-vs-fill | Rs.0 |
| 5 | FastBT re-baseline of V7 | SuperAgent | [ ] | prior engine verdict VOID; brokerage defaults Rs.0 | Rs.20/run |
| 6 | Positions, exits, repair logic | SuperAgent | [ ] | Position Detail != Traded Instrument (ledger B5) | Rs.0 |
| 7 | Option-chain snapshotter to DuckDB | Operator + Claude | [ ] | blocked on P0.10. TIME-SENSITIVE: each day lost is unrecoverable | Rs.0 |
| 8 | Local FastMCP server (chain, Greeks, PCR, max pain) | Operator + Claude | [ ] | after Task 7 | Rs.0 |
| 9 | Blueprint generator (build sheet + edited baseline) | SuperAgent | [ ] | after Task 2 | Rs.0 |
| 10 | Streamlit operator console, one-click run | Operator + Claude | [ ] | last -- needs 7, 8, 9 working | Rs.0 |
| 11 | Market intelligence / regime taxonomy | Spark | [ ] | after Task 8 | Rs.0 |
| 12 | Own intrabar backtest engine | deferred | [ ] | build only when FastBT bias distorts sizing | - |

## AGENT LANES (no overlap)

- Gemini Spark    : Kite market data, option chain, regime reads, live position verdicts.
- Genspark SuperAgent : Tradetron MCP, keyword ground truth, schema, blueprint generation.
- Claude          : reviews both, authors specs, catches fabrications.
- Operator        : runs PowerShell, exports strategies, approves spend, owns final call.

RULE E8: no agent writes to canonical files. Agent output goes to /inbox/
and is promoted only after review by a second agent or the operator.

## DECISIONS PENDING

- Is the Rs.500 Kite Connect app still needed? Historical data is free and
  the hosted MCP needs no key. Decide before 2026-09-08.
- Does Genspark support interactive OAuth for MCP? Task 0 settles it.
  If not, choose: local proxy / run Tradetron MCP in another client /
  fall back to export-import files.
