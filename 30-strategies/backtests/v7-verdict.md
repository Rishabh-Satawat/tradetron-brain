---
id: v7-verdict
title: V7 CLEAN 700 CACHE BUST BASELINE - Verdict REJECT
domain: strategy
type: reference
status: canonical
evidence: V
sources:
  - https://tradetron.tech/bt/view/b96e4cf285df9f32f63dae05afc6ce8f
verified_on: 2026-08-31
owner: operator
---

# V7 - VERDICT: REJECT. DO NOT DEPLOY. DO NOT TUNE.

Window 2025-09-01 -> 2026-08-26, 239 sessions, 33 traded.
4-leg SENSEX structure, 132 leg round-trips, 264 orders.

## Cost reconciliation

Tradetron reported gross Rs 4,842 / net Rs 4,157 (cost Rs 685).
Reproduced Rs 684.76 exactly from its default profile - so the model
is understood, and its defaults are wrong.

Corrected: brokerage 264 x Rs 20 = Rs 5,280; GST on it Rs 979;
STT 0.15% Rs 359; BFO exchange Rs 156; stamp Rs 7; SEBI Rs 0.48;
slippage Rs 240.  TRUE COST ~ Rs 7,020.

  Gross  +Rs 4,842
  Cost   -Rs 7,020
  NET    -Rs 2,178      (about -1.7% of stated capital)

Per round trip: gross Rs 147 vs cost Rs 213. Structurally negative.

## Independent reasons to reject

1. Oct-2025 = 79% of gross profit; other 11 months = Rs 995.
2. Top 3 months = 75% of profits.
3. Winning leg FLIPPED vs the prior version (was PE-led, now CE +13.1K
   / PE -10.7K). A neutral structure whose P&L migrates between legs
   is harvesting directional drift, not theta.
4. Thursday is the only profitable weekday; t-stat 0.9, insignificant.
5. Peak margin Rs 2.05L vs stated capital Rs 1.25L, breached on 32 of
   239 days. Return on peak margin +2.03% GROSS, negative net.
6. Monte-Carlo 73.2% profitable is computed on GROSS; on true net it
   falls below a coin flip.

## Transferable lesson

Leg count is a cost decision. At Rs 20/order a 4-leg SENSEX structure
starts each round trip Rs 189 down. The 2-leg RSI spread survives the
same test purely by having half the legs. Prefer 2 legs unless the
extra pair buys measurably more gross than Rs 95 per round trip.