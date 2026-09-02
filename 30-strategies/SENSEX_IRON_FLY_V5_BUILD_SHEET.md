# SENSEX Iron Fly V5 — Tradetron Condition Builder Blueprint
# Generated: 2026-09-02 13:03:45 IST
# Underlying: BSE SENSEX (BFO) | Expiry: Thursday Weekly | Lot Size: 20

## 1. Strategy Parameters
- **Underlying Spot Level     :** ~₹76,950.00
- **ATM Strike (Short Straddle):** 77000 CE & 77000 PE
- **Hedge Strike (Long Wings)  :** 77600 CE (+600 pts) & 76400 PE (-600 pts)
- **Target Profit per Lot      :** ₹1,400.00 (+70 pts)
- **Stop Loss per Lot          :** ₹700.00 (-35 pts)
- **Max Capital Allocation     :** ₹4,12,000 (Max Risk Cap: 2% = ₹8,240)

---

## 2. Tradetron UI Condition Builder Blueprint (Exact UI Order)

### SET 1 — ENTRY CONDITIONS:
  Condition 1:
    Position Detail ( BSE_IDX , SENSEX , Current Week , 0 , Quantity ) == 0
    AND
    Time ( Current Time ) >= 0920
    AND
    Time ( Current Time ) <= 1430
    AND
    ADX ( 15 min , 14 ) < 30

### POSITION BUILDER (LEGS):
  Leg 1: SELL | BFO | SENSEX | Current Week | ATM Strike              | Lot: 1 (Qty: 20) | CE
  Leg 2: SELL | BFO | SENSEX | Current Week | ATM Strike              | Lot: 1 (Qty: 20) | PE
  Leg 3: BUY  | BFO | SENSEX | Current Week | ATM Strike +600         | Lot: 1 (Qty: 20) | CE
  Leg 4: BUY  | BFO | SENSEX | Current Week | ATM Strike -600         | Lot: 1 (Qty: 20) | PE

### SET 1 — UNIVERSAL EXIT (Simultaneous 4-Leg Execution):
  Strategy PnL >= 1400
  OR
  Strategy PnL <= -700
  OR
  Time ( Current Time ) >= 1515

<!-- END OF BLUEPRINT -->
