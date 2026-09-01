---
id: ledger-contradictions
title: Ledger Contradictions and Resolutions
domain: ops
type: review
status: review
verified_on: 2026-09-01
owner: manus
---

# Ledger Contradictions and Resolutions

| Contradiction | Resolution | Why |
|---|---|---|
| Root ledger claimed the Kite app expired 08-Sep-2026; canonical V16 records operator-observed expiry 09-Oct-2026. | V16 is current; stale root date is historical only. | Later direct operator observation supersedes the stale entry. |
| Root ledger claimed root path was canonical; `01_PLAN/00_CORRECTIONS_LEDGER.md` contains V1-V24. | `01_PLAN/00_CORRECTIONS_LEDGER.md` is canonical and root is a pointer stub. | It contains the newer correction rounds and is the path agents must read. |
| Root/reference cost material used Rs3,503/crore for NFO; `zerodha_charges.py` and reconciliation use Rs3,553/crore. | Executable authority remains Rs3,553/crore; reference is review status. | The executable value reconciles against five calculator panels; the 3,503 figure was explicitly marked assumed. |
| Historical reference RULE 3 used Rs123 / Rs213 friction; V24 records approximately Rs144 / Rs211. | Corrected to V24 values and marked review. | V24 is the latest empirical BSE benchmark. |
| `cost_engine.py` rounds once at total; V17 says component-first rounding is correct. | `zerodha_charges.py` is authority; cost engine is totals-superseded. | Five-panel evidence rejects the old rounding design. |
| `cost_model.py` included `min_net=150`; verdict policy rejects AI-invented thresholds. | Archived; no replacement policy threshold added. | The policy remains null until operator sets it. |
| Root ledger said only a generic root file should be read; AGENTS and llms pointed there. | Both pointers now name the canonical path. | Eliminates duplicate-ledger drift. |

The repository contains a market-data strike containing the digit string `410250`; it is not an operator-capital value. The operator-capital comment was removed and replaced with a gitignored-local-file pointer.

Could not verify public-history removal because no history rewrite was authorized.
