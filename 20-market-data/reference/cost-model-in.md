---
id: cost-model-in
title: Indian F&O Frictional Cost Model v2
domain: market-data
type: reference
status: canonical
evidence: V
verified_on: 2026-08-31
owner: operator
---

# Frictional Cost Model - Indian F&O  (v2)

## Verified rates

| Component | Rate | Base | Side | Tag |
|---|---|---|---|---|
| Brokerage (Zerodha) | Rs 20 flat | per EXECUTED ORDER | both | [V] |
| STT - options | 0.15% | option premium | SELL only | [V] eff 01-Apr-2026 |
| STT - options (prior) | 0.10% | option premium | SELL only | [V] until 31-Mar-2026 |
| Exchange - BFO Sensex/Bankex opt | Rs 3,250 / crore | premium turnover | both | [V] BSE 27-Sep-2024 |
| Exchange - NFO options | Rs 3,503 / crore (assumed) | premium turnover | both | [U] NSE circular NOT retrieved |
| Stamp duty | 0.003% | PREMIUM value (not notional) | BUY only | [V] NSE |
| SEBI turnover fee | Rs 10 / crore | turnover | both | [V] |
| GST | 18% | brokerage + exchange + SEBI | - | [V] |
| Slippage | 0.05% of turnover | working assumption | - | [I] |

Zerodha caveat: a SECOND Rs 20 applies if the account carries a negative
balance, or a collateral-margin shortfall above Rs 5 lakh. [V]

## RULE 1 - brokerage scales with ORDERS, not trades

Orders = legs x 2 sides. A 4-leg structure round trip = 8 orders =
Rs 160 brokerage + Rs 28.80 GST = Rs 188.80 before any statutory levy.
Leg count is a FIRST-ORDER cost decision.

## RULE 2 - Tradetron Cost Lab defaults are WRONG for us

Two defaults must be overridden on every single run:
  Brokerage / order : 0     ->  20
  STT %             : 0.1   ->  0.15
Leaving them concealed Rs 6,259 of real cost in the V7 backtest and
turned a real loss into an apparent profit.

## RULE 3 - expectancy gate, derived not guessed

Required gross expectancy per STRATEGY round trip >= 3x total friction.
  2-leg SENSEX : friction ~Rs 123  ->  need >= Rs 370 gross / RT
  4-leg SENSEX : friction ~Rs 213  ->  need >= Rs 640 gross / RT

## RULE 4 - "Total Trades" means LEG round-trips  [V]

Proven from report b96e4cf2: 132 leg entries / 4 legs = 33 = "Days
traded 33 of 239"; Cost Lab "Orders in window 264" = 132 x 2.
Expectancy / trade is therefore PER LEG. Multiply by leg count before
comparing to per-round-trip friction. A reported day count means
sessions-with-fills, not calendar days.