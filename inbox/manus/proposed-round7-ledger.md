---
id: proposed-round7-ledger
title: Proposed Round 7 Ledger Entries
domain: ops
type: proposal
status: review
verified_on: 2026-09-01
owner: manus
---

# Proposed Round 7 Ledger Entries

These entries are proposed for operator review and are not inserted into the canonical ledger.

## V25 — operator capital quarantined
The tracked verdict-policy comment naming operator capital was replaced with a pointer to ignored `70-ops/local/operator-capital.yaml`; `70-ops/local/` is ignored and a keep file exists. [V]

## V26 — canonical ledger promoted
`01_PLAN/00_CORRECTIONS_LEDGER.md` is the sole canonical ledger; root `00_CORRECTIONS_LEDGER.md` is a historical pointer. Non-duplicated root facts were migrated into Section G. [V]

## V27 — rejected calculator archived
`cost_model.py` and `test_cost_model.py` were moved to `90-archive/superseded/`; no tracked source imports them. `cost_engine.py` is superseded for totals. [V]

## V28 — cost reference placed under review
The reference now names `zerodha_charges.py` as computation authority and corrects the historical Rs123/Rs213 friction figures to the V24 empirical approximately Rs144/Rs211 benchmarks. The NFO rate conflict is recorded as Rs3,503 assumed versus Rs3,553 reconciled authority. [V]

## V29 — rates externalized
Charge rates and regime dates used by `zerodha_charges.py` are stored in `70-ops/config/cost-config.yaml` with source URLs and verification date. Slippage is null and explicitly unmeasured; net figures without it are upper bounds. [V]

## V30 — repo map promoted
`01_PLAN/REPO_MAP.md` is canonical and records the stale ledger pointers, tracked capital comment, live `min_net=150`, and 3503-vs-3553 conflict. [V]

## V31 — Manus review artifacts
Architecture review, contradiction register, AGENTS lane proposal, and this proposal are in `inbox/manus/` pending operator review. [V]

Questions remain: operator must approve promotion of V25-V31; the public Git history still contains prior tracked content; and the exact slippage measurement protocol requires live broker-session evidence.
