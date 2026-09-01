---
id: repo-map
title: Repository Map
domain: ops
type: reference
status: canonical
verified_on: 2026-09-01
owner: operator
---

# Repository Map

`01_PLAN/00_CORRECTIONS_LEDGER.md` is the canonical ledger. The root `00_CORRECTIONS_LEDGER.md` is a historical pointer only. `AGENTS.md` and `llms.txt` now point to the canonical path.

## Domains

| Path | Role | Authority |
|---|---|---|
| `01_PLAN/` | Plans, conventions, canonical ledger, repository map | Current planning truth |
| `10-tradetron/` | Tradetron documentation and semantics | Ledger plus official docs |
| `20-market-data/` | Instrument masters, market-data references, charge inputs | Dated primary evidence |
| `60-tools/python/` | Reproducible probes and calculators | Executable outputs, with `zerodha_charges.py` as cost authority |
| `70-ops/` | Policies, config, status, and operator-local boundary | Policy/config contracts |
| `90-archive/` | Historical or superseded artifacts | Evidence only, never current truth |
| `inbox/manus/` | Unreviewed Manus proposals and reports | Operator review required |

## Newly promoted findings

1. `AGENTS.md` and `llms.txt` previously pointed at the stale root ledger.
2. `70-ops/policies/verdict-policy.yaml` previously exposed an operator capital figure in a tracked comment.
3. `60-tools/python/cost_model.py` contained live AI-invented `min_net=150` logic and is now archived.
4. `20-market-data/reference/cost-model-in.md` cited Rs3,503/crore while the reconciled computation authority uses Rs3,553/crore for the NSE options rate.

All claims in this map are [V] verified from the repository tree and dated status files on 2026-09-01.
