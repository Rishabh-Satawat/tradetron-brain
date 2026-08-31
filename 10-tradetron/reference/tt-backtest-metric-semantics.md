---
id: tt-backtest-metric-semantics
title: Tradetron Backtest Metric Semantics
domain: tradetron
type: reference
status: canonical
evidence: V
sources:
  - https://tradetron.tech/bt/view/b96e4cf285df9f32f63dae05afc6ce8f
verified_on: 2026-08-31
owner: operator
---

# Tradetron Backtest Report - what each field actually means

| Field | Meaning | Tag |
|---|---|---|
| Total Trades / Trades | LEG round-trips, not strategy round-trips | [V] |
| Expectancy / Trade | per LEG round-trip | [V] |
| Days traded "N of M" | sessions with fills or carried position, of total sessions | [V] |
| Entries / Exits (monthly) | LEG fills | [V] |
| Orders in window (Cost Lab) | legs x 2 sides | [V] |
| Gross P&L | before ALL costs | [V] |
| Net P&L | after the Cost Lab profile ONLY - audit the profile first | [V] |
| Capital Required | stated input, NOT margin actually blocked | [V] |
| Peak margin | what the book really blocks. Use THIS for return-on-capital | [V] |

## Report capabilities present (ledger updated)

The report DOES include: performance by India VIX regime, block-bootstrap
Monte-Carlo (2000 paths), Ulcer/Pain index, per-leg P&L attribution,
day-of-week t-stats, top-5 drawdowns, MAE/MFE per trade, a live Cost Lab,
and auto-fired risk flags. [V]

## CRITICAL DISTINCTION - open item

Report-level VIX conditioning is NOT proof the strategy ENGINE accepts
India VIX as an entry condition. The ledger line "engine does not
recognise India VIX" is VOID AS WRITTEN and needs precise restatement:
report analytics vs engine-condition availability are different claims.
Assigned to agents for verification. [U]