# Foundation Cleanup Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `01_PLAN/00_CORRECTIONS_LEDGER.md` canonical, quarantine rejected calculators, externalize verified charge rates, and produce an auditable foundation-cleanup report on `feat/foundation-cleanup`.

**Architecture:** Canonical knowledge remains under `01_PLAN/`; executable calculation authority remains `60-tools/python/zerodha_charges.py`; all operator-local values remain under ignored `70-ops/local/`. Unreviewed findings and proposals are written only under `inbox/manus/`.

**Tech Stack:** Git, Python 3.11 standard library, YAML configuration consumed by a small dependency-free loader, Markdown, shell regression checks.

**Spec:** `/home/ubuntu/upload/pasted_content.txt`

## Global Constraints

- Never invent a numeric rate, threshold, lookback, or market fact; unresolved values remain `null`/`None` and fail closed.
- Never write capital figures, account IDs, or credentials to tracked files, commits, logs, or status output.
- Never reset, rebase, force-push, merge to main, create a PR, or commit `00_INDEX.md`.
- Agent output goes only to `inbox/manus/` unless the task explicitly authorizes a canonical edit.
- `zerodha_charges.py` is the only importable cost calculator; `cost_model.py` is superseded and archived.

---

### Task 1: Security scrub and local-value quarantine

**Files:** modify `70-ops/policies/verdict-policy.yaml`, `.gitignore`; create `70-ops/local/.gitkeep`.

- [ ] Replace the capital comment with the gitignored-local-file pointer.
- [ ] Ignore `70-ops/local/` and create its keep file.
- [ ] Run exact and adjacent-number grep over the complete tracked tree and preserve every hit in the report.

### Task 2: Canonical ledger and repository map

**Files:** modify `00_CORRECTIONS_LEDGER.md`, `01_PLAN/00_CORRECTIONS_LEDGER.md`, `AGENTS.md`, `llms.txt`; create `01_PLAN/REPO_MAP.md`.

- [ ] Append non-duplicated root-ledger facts under `SECTION G - MIGRATED FROM ROOT LEDGER` with original evidence tags.
- [ ] Replace the root ledger with a historical pointer stub.
- [ ] Point both agent entry files at the canonical ledger.
- [ ] Promote the repository map with the four newly identified findings.
- [ ] Record ledger contradictions, including the stale Kite-expiry fact and the corrected 3503/3553 and V16-V24 resolutions, in `inbox/manus/ledger-contradictions-2026-09-01.md`.

### Task 3: Quarantine rejected calculators and fix reference authority

**Files:** move `60-tools/python/cost_model.py` and `test_cost_model.py` to `90-archive/superseded/`; modify `60-tools/python/cost_engine.py`, `20-market-data/reference/cost-model-in.md`.

- [ ] Prepend superseded headers to both archived files.
- [ ] Confirm no tracked source imports either archived module.
- [ ] Preserve the cost engine superseded-for-totals warning.
- [ ] Mark the reference document `status: review`, name `zerodha_charges.py` as computation authority, and reconcile the two friction figures to V24 with the existing cited evidence.

### Task 4: Externalize charge rates and run regressions

**Files:** create `70-ops/config/cost-config.yaml`; modify `60-tools/python/zerodha_charges.py`.

- [ ] Move every hard-coded charge rate and regime date into YAML with source URL and verification date.
- [ ] Add `slippage_pct: null` with an explicit unmeasured/upper-bound comment.
- [ ] Load config using only the Python standard library and fail closed for absent/null rates.
- [ ] Run the five-panel regression, live SENSEX audit, and all seven negative tests; tee complete stdout to `70-ops/status/C3_config_externalised_2026-09-01.txt`.

### Task 5: Manus delivery documents

**Files:** create `inbox/manus/.gitkeep`, `inbox/manus/proposed-round7-ledger.md`, `inbox/manus/architecture-review-2026-09-01.md`, `inbox/manus/ledger-contradictions-2026-09-01.md`, `inbox/manus/AGENTS-lane-proposal.md`.

- [ ] Cover V25 onward for every change without editing the canonical ledger.
- [ ] Answer all architecture-review questions bluntly, including credential exposure and the five raised-number cases.
- [ ] Propose the AGENTS lane-table line without editing `AGENTS.md`.

### Task 6: Validation, commit, and push

- [ ] Run the repository test suite or explicitly document that no suite is configured.
- [ ] Run syntax checks, regression output, import grep, secret grep, and staged-diff review.
- [ ] Commit atomic logical slices with conventional messages.
- [ ] Push `feat/foundation-cleanup` to origin; do not merge or open a PR.
- [ ] Report stdout, status, last five commits, grep results, and unanswered questions.
