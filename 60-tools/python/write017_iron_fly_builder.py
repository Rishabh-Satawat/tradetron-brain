# =============================================================================
# File: 60-tools/python/write017_iron_fly_builder.py
# Description: Generates Tradetron UI Build Sheet for SENSEX Iron Fly V5
# Target Expiry: Thursday (03-Sep-2026) | Underlying: BSE SENSEX
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os


def generate_sensex_iron_fly(
    spot_price=76950,
    wing_width=600,
    lot_size=20,
    sl_points=35,
    target_points=70,
):
  # Round spot to nearest 100 strike for SENSEX
  atm_strike = int(round(spot_price / 100.0) * 100)
  long_ce_strike = atm_strike + wing_width
  long_pe_strike = atm_strike - wing_width

  target_inr = target_points * lot_size
  sl_inr = sl_points * lot_size

  build_sheet = f"""# SENSEX Iron Fly V5 — Tradetron Condition Builder Blueprint
# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S IST')}
# Underlying: BSE SENSEX (BFO) | Expiry: Thursday Weekly | Lot Size: {lot_size}

## 1. Strategy Parameters
- **Underlying Spot Level     :** ~₹{spot_price:,.2f}
- **ATM Strike (Short Straddle):** {atm_strike} CE & {atm_strike} PE
- **Hedge Strike (Long Wings)  :** {long_ce_strike} CE (+{wing_width} pts) & {long_pe_strike} PE (-{wing_width} pts)
- **Target Profit per Lot      :** ₹{target_inr:,.2f} (+{target_points} pts)
- **Stop Loss per Lot          :** ₹{sl_inr:,.2f} (-{sl_points} pts)
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
  Leg 1: SELL | BFO | SENSEX | Current Week | ATM Strike              | Lot: 1 (Qty: {lot_size}) | CE
  Leg 2: SELL | BFO | SENSEX | Current Week | ATM Strike              | Lot: 1 (Qty: {lot_size}) | PE
  Leg 3: BUY  | BFO | SENSEX | Current Week | ATM Strike +{wing_width}         | Lot: 1 (Qty: {lot_size}) | CE
  Leg 4: BUY  | BFO | SENSEX | Current Week | ATM Strike -{wing_width}         | Lot: 1 (Qty: {lot_size}) | PE

### SET 1 — UNIVERSAL EXIT (Simultaneous 4-Leg Execution):
  Strategy PnL >= {target_inr}
  OR
  Strategy PnL <= -{sl_inr}
  OR
  Time ( Current Time ) >= 1515

<!-- END OF BLUEPRINT -->
"""

  output_dir = r"C:\kite-agent\brain\30-strategies"
  os.makedirs(output_dir, exist_ok=True)
  output_path = os.path.join(output_dir, "SENSEX_IRON_FLY_V5_BUILD_SHEET.md")

  with open(output_path, "w", encoding="utf-8") as f:
    f.write(build_sheet)

  print("=" * 80)
  print("🚀 SENSEX IRON FLY V5 BUILD SHEET GENERATED")
  print("=" * 80)
  print(build_sheet)
  print("=" * 80)
  print(f"📁 Saved to: {output_path}")


if __name__ == "__main__":
  generate_sensex_iron_fly(spot_price=76950, wing_width=600)