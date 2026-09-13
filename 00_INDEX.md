# TRADETRON BRAIN — MASTER TASK REGISTER
**Generated:** 2026-08-31 | **Repo:** C:\kite-agent\brain | **Underlyings:** NIFTY, SENSEX

## STATUS LEGEND
- 🔴 BLOCKED — dependency not met
- 🟡 READY — preconditions satisfied
- 🟢 DONE — evidence artifact exists
- ⚫ SKIPPED — out of scope

## PHASE 0 — BLOCKERS RESOLVED

| ID | Task | Status | Blocker | Evidence |
|----|------|--------|---------|----------|
| 0.1 | Backtest window confirmed | 🟢 DONE | - | 2026-02-01 to 2026-08-31 |
| 0.2 | Underlyings confirmed | 🟢 DONE | - | NIFTY, SENSEX (weekly-capable) |
| 0.3 | STT regime split identified | 🟢 DONE | - | 0.10% (Feb–Mar), 0.15% (Apr–Aug) |
| 0.4 | Tradetron cost setting unknown | 🔴 BLOCKED | Operator must check backtest settings | [needs manual check] |

## PHASE A — FOUNDATION

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| A1 | Snapshot repo state | 5m | - | 🟡 READY | - | 70-ops/status/repo-manifest-[DATE].md |
| A2 | Verify Python environment | 5m | A1 | 🟡 READY | - | Console output (Python 3.14.7, dhanhq 2.2.0) |
| A3 | Capture Dhan CSV header | 5m | A1 | 🟡 READY | - | 33 column names printed |
| A4 | Pip freeze + commit | 10m | A2 | 🟡 READY | - | 70-ops/env/pip-freeze-2026-08-31.txt |
| A5 | Verify Kite session file | 5m | A1 | 🟡 READY | - | 60-tools/python/kite_session.py exists |

## PHASE B — KITE↔DHAN BRIDGE

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| B1 | Create Kite symbol parser | 15m | A3 | 🟡 READY | - | 60-tools/python/kite_symbol_parse.py |
| B2 | Join Kite↔Dhan master | 20m | B1, A3 | 🟡 READY | - | 70-ops/status/bridge-report-[DATE].md |
| B3 | Validate lot sizes | 10m | B2 | 🟡 READY | - | NIFTY=65, SENSEX=20 match count |
| B4 | Enforce 100% match | 15m | B2 | 🟡 READY | - | Zero unmatched rows assertion |

## PHASE C — COST MODEL

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| C1 | Date-aware STT table | 10m | 0.3 | 🟡 READY | - | 60-tools/python/cost_model_stt.py |
| C2 | Golden fixture test (₹119.87) | 20m | C1 | 🟡 READY | - | Console diff: expected vs actual |
| C3 | Brokerage model (Zerodha) | 10m | - | 🟡 READY | - | ₹20/order, ₹0 on expired/exercised |
| C4 | Exchange charges (NSE/BSE) | 10m | - | 🟡 READY | - | NSE 0.03553%, BSE 0.0325% |
| C5 | SEBI + stamp + GST | 15m | C3, C4 | 🟡 READY | - | SEBI 0.0001%, stamp 0.003%, GST 18% |
| C6 | Slippage model (half-spread) | 10m | - | 🟡 READY | - | Default 0.5 tick, parameterised |

## PHASE D — TRADE SEMANTICS

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| D1 | Extract observed first/last trade | 15m | 0.1 | 🔴 BLOCKED | Trade log file not yet provided | [needs trade log path] |
| D2 | Verify divisor formula | 20m | D1 | 🔴 BLOCKED | D1 | Total trades ÷ (2 × legs) = cycles |
| D3 | Detect BANKNIFTY weekly usage | 10m | D1 | 🔴 BLOCKED | D1 | Should find zero (regression guard) |

## PHASE E — VERDICT

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| E1 | Re-price Apr–Aug window | 30m | C1–C6, D2, 0.4 | 🔴 BLOCKED | D2, 0.4 | 70-ops/status/verdict-primary-[DATE].md |
| E2 | Re-price Feb–Mar window | 20m | C1–C6, D2, 0.4 | 🔴 BLOCKED | D2, 0.4 | 70-ops/status/verdict-secondary-[DATE].md |
| E3 | Compute net expectancy | 10m | E1 | 🔴 BLOCKED | E1 | ₹/cycle, ₹/session metrics |
| E4 | Emit verdict (PASS/CONDITIONAL/FAIL) | 5m | E3 | 🔴 BLOCKED | E3 | PASS if net expectancy > ₹150/cycle |

## PHASE F — STRATEGY ENGINE (V1 SCOPE)

| ID | Task | Est | Depends | Status | Blocker | Evidence |
|----|------|-----|---------|--------|---------|----------|
| F1 | Capture Tradetron keyword ledger | 60m | - | 🟡 READY | - | 30-strategies/tradetron-keywords.md |
| F2 | Design Iron Fly framework | 90m | F1 | 🟡 READY | - | 30-strategies/ironfly-v8-spec.md |
| F3 | Parameterise 2-leg/4-leg variants | 30m | F2 | 🟡 READY | - | Entry/exit rules table |
| F4 | Build Tradetron instruction sheet | 60m | F2, F3 | 🟡 READY | - | 30-strategies/ironfly-v8-build.md |
| F5 | Add position sizing table | 20m | - | 🟡 READY | - | 1/2/5/10/20 lot scaling |
| F6 | Add risk management rules | 30m | - | 🟡 READY | - | Stop-loss, time-exit, P&L limits |

## TOTAL ESTIMATED TIME
- Phase A: 30 min
- Phase B: 60 min
- Phase C: 75 min
- Phase D: 45 min (blocked)
- Phase E: 65 min (blocked)
- Phase F: 290 min (5 hours, V1 scope only)

**Critical Path:** A1 → A3 → B1 → B2 → B4 → C1 → C2 → [D1 unblocks] → D2 → E1 → E3 → E4
**Parallel Track:** F1 can start immediately (no technical dependencies)
