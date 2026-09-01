---
id: architecture-review
title: Architecture Review
domain: ops
type: review
status: review
verified_on: 2026-09-01
owner: manus
---

# Architecture Review

## Q1. Biggest structural flaw

The biggest remaining flaw is that policy, executable calculations, market-data provenance, and deployment state are still represented as neighboring documents rather than enforced interfaces. The repo can now identify the canonical ledger and cost authority, but it cannot yet mechanically prevent a strategy artifact from consuming stale data or an unmeasured cost assumption. I would replace implicit conventions with typed contracts: every input gets provenance, effective date, unit, and nullability; every output carries an evidence bundle; and CI rejects untagged rates, non-null slippage without a source, and imports from `90-archive/`.

## Q2. Correct build order

The correct order is **skill contracts → position sizing → risk management → option-chain snapshotter → feasibility register → blueprint generator**. Skill contracts define interfaces and evidence obligations. Position sizing then determines quantities and order count. Risk management depends on those quantities and margin exposure. The snapshotter supplies point-in-time chain data to the feasibility register, which can finally test liquidity, costs, margin, and execution constraints. Only then should a blueprint generator emit a strategy.

If built out of order, the first break is usually the generator: it will emit syntactically valid but infeasible structures because it lacks measured liquidity, margin, and cost inputs. Building the snapshotter before contracts creates an unversioned data dump; building risk before sizing creates undefined exposure; building feasibility before the snapshotter forces guessed spreads and slippage.

## Q3. Cheapest reliable slippage measurement

The cheapest reliable method is a read-only, timestamped capture of the actual SENSEX weekly option chain and five available depth levels at the exact planned entry times, joined to the eventual broker fills. Use Kite WebSocket `full` mode for the instrument tokens, record best bid/ask, five-level depth, last traded price, exchange timestamp, and local receipt timestamp, then compute quoted half-spread and fill-versus-midpoint slippage for each leg. Repeat across enough real entry events to cover both liquid and stressed conditions; the required sample count is deliberately **not specified here** because no operator-approved number was provided. Kite's 20-level derivative DOM is discontinued, so a 20-level requirement must not be invented or substituted.

## Q4. Desktop Scheduled Task or Cloud Computer?

Recommend **Manus Desktop Scheduled Task**, with the broker session kept on the operator's machine and the snapshotter read-only. A Cloud Computer would make unattended uptime easier but expands the credential-exposure surface and creates a second host that must be hardened, monitored, and revoked. Desktop scheduling is acceptable only if the local credential/token file remains outside Git, logs redact identifiers, the process never places orders, and the operator explicitly accepts that sleep, logout, or network interruption can create gaps. For unattended production-grade capture, a hardened Cloud Computer with short-lived tokens and secret injection would be stronger operationally, but it is not the safer first deployment for this repo because credential exposure is the dominant risk.

## Q5. Numbers I refused to invent

I raised rather than invented: the verdict minimum net expectancy; maximum cycles per month; maximum capital at risk; slippage percentage; a sample size for real spread measurement; a 20-level DOM replacement; any new lookback, threshold, or margin figure; and any capital or account identifier. The configured `slippage_pct` is `null`, not zero. The unresolved policy fields remain null and fail closed.

Could not verify current broker credentials, live depth availability, or the exact future option-chain capture schedule from this repository.
