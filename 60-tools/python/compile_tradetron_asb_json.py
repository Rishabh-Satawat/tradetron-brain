# =============================================================================
# TRADETRON ASB v2 STRATEGY COMPILER — NIFTY 0-DTE IRON FLY V6
# Compiles 4-leg defined-risk structure into Tradetron tt-strategy/v2 JSON
# =============================================================================
import datetime
import json
import os

out_dir = r"C:\kite-agent\brain\30-strategies"
os.makedirs(out_dir, exist_ok=True)
json_file_path = os.path.join(out_dir, "NIFTY_Iron_Fly_V6_ASB.json")

# Build the Tradetron v2 AST Schema
tradetron_payload = {
    "_format": "tt-strategy/v2",
    "_readme": {
        "about": (
            "Stockera Quant Tradetron ASB export. Import via the ASB Import"
            " button."
        ),
        "strategy": "NIFTY 0-DTE Weekly Expiry Iron Fly V6",
        "lot_size": 65,
        "underlying": "NIFTY 50 (NFO)",
    },
    "name": "NIFTY_0DTE_Iron_Fly_V6",
    "description": (
        "Stockera Quant: Automated delta-neutral 0-DTE Iron Fly with 150-pt"
        " protective wings."
    ),
    "tags": ["StockeraQuant", "0DTE", "NIFTY", "IronFly"],
    "variables": [],
    "sets": [{
        "list": 0,
        "name": "Set 1 - 0-DTE Entry & Core Legs",
        "conditions": [{
            "type": "Entry",
            "conditionValue": (
                "( tt_Time ( 'NSE' ) >= tt_Number ( '930' ) ) and ( tt_Time ("
                " 'NSE' ) <= tt_Number ( '1400' ) )"
            ),
            "conditionDisplay": (
                "( Time ( 'NSE' ) >= Number ( '930' ) ) and ( Time ( 'NSE' ) <="
                " Number ( '1400' ) )"
            ),
            "subType": "None",
            "visible": 1,
            "legs": [
                # Leg 1: BUY Wing CE (+3 strikes = +150 pts)
                {
                    "optionType": "CE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('NIFTY 50')",
                    "strikeType": "Fx",
                    "strike": "( tt_ATM_SPOT ( 'NIFTY 50', '3' ) )",
                    "strikeDisplay": "( ATM SPOT ( 'NIFTY 50', '3' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','CE')",
                    "qtyType": "Lots",
                    "qtyDisplay": "1",
                    "buySell": "B",
                    "productType": "NRML",
                    "underlyingSymbol": "NIFTY 50",
                    "isOvernightProtectionLeg": "No",
                },
                # Leg 2: BUY Wing PE (-3 strikes = -150 pts)
                {
                    "optionType": "PE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('NIFTY 50')",
                    "strikeType": "Fx",
                    "strike": "( tt_ATM_SPOT ( 'NIFTY 50', '-3' ) )",
                    "strikeDisplay": "( ATM SPOT ( 'NIFTY 50', '-3' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','PE')",
                    "qtyType": "Lots",
                    "qtyDisplay": "1",
                    "buySell": "B",
                    "productType": "NRML",
                    "underlyingSymbol": "NIFTY 50",
                    "isOvernightProtectionLeg": "No",
                },
                # Leg 3: SELL Core CE (ATM 0)
                {
                    "optionType": "CE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('NIFTY 50')",
                    "strikeType": "Fx",
                    "strike": "( tt_ATM_SPOT ( 'NIFTY 50', '0' ) )",
                    "strikeDisplay": "( ATM SPOT ( 'NIFTY 50', '0' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','CE')",
                    "qtyType": "Lots",
                    "qtyDisplay": "1",
                    "buySell": "S",
                    "productType": "NRML",
                    "underlyingSymbol": "NIFTY 50",
                    "isOvernightProtectionLeg": "No",
                },
                # Leg 4: SELL Core PE (ATM 0)
                {
                    "optionType": "PE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('NIFTY 50')",
                    "strikeType": "Fx",
                    "strike": "( tt_ATM_SPOT ( 'NIFTY 50', '0' ) )",
                    "strikeDisplay": "( ATM SPOT ( 'NIFTY 50', '0' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','PE')",
                    "qtyType": "Lots",
                    "qtyDisplay": "1",
                    "buySell": "S",
                    "productType": "NRML",
                    "underlyingSymbol": "NIFTY 50",
                    "isOvernightProtectionLeg": "No",
                },
            ],
            "extra": {"name": None, "variables": []},
        }],
    }],
    "universalExit": {
        "conditionValue": (
            "( PNL ( 'strategy_id' , 'run_counter' ) >= tt_Number ( '2500' ) )"
            " or ( PNL ( 'strategy_id' , 'run_counter' ) <= tt_Number ( '-2500'"
            " ) ) or ( tt_Time ( 'NSE' ) >= tt_Number ( '1510' ) )"
        ),
        "conditionDisplay": (
            "( PNL >= Number ( '2500' ) ) or ( PNL <= Number ( '-2500' ) ) or"
            " ( Time ( 'NSE' ) >= Number ( '1510' ) )"
        ),
    },
}

with open(json_file_path, "w", encoding="utf-8") as f:
  json.dump(tradetron_payload, f, indent=2)

print("=" * 80)
print("🎉 STOCKERA QUANT — TRADETRON ASB JSON COMPILED!")
print(f"📁 Output: {json_file_path}")
print(
    "💡 You can now 1-click import this file directly into Tradetron via 'ASB"
    " Import'!"
)
print("=" * 80)