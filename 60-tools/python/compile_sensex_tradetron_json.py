import json
import os

out_dir = r"C:\kite-agent\brain\30-strategies"
json_path = os.path.join(out_dir, "SENSEX_Iron_Fly_ASB.json")

payload = {
    "_format": "tt-strategy/v2",
    "_readme": {"strategy": "SENSEX 0-DTE Thursday Expiry Iron Fly", "lot": 20},
    "name": "SENSEX_0DTE_Iron_Fly_V1",
    "description": "Stockera Quant: BSE SENSEX 0-DTE Iron Fly with 400-pt wings",
    "sets": [{
        "list": 0,
        "conditions": [{
            "type": "Entry",
            "conditionValue": (
                "( tt_Time ( 'BSE' ) >= tt_Number ( '930' ) ) and ( tt_Time ("
                " 'BSE' ) <= tt_Number ( '1400' ) )"
            ),
            "legs": [
                {
                    "optionType": "CE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('SENSEX')",
                    "strike": "( tt_ATM_SPOT ( 'SENSEX', '4' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','CE')",
                    "buySell": "B",
                    "productType": "NRML",
                    "underlyingSymbol": "SENSEX",
                },
                {
                    "optionType": "PE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('SENSEX')",
                    "strike": "( tt_ATM_SPOT ( 'SENSEX', '-4' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','PE')",
                    "buySell": "B",
                    "productType": "NRML",
                    "underlyingSymbol": "SENSEX",
                },
                {
                    "optionType": "CE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('SENSEX')",
                    "strike": "( tt_ATM_SPOT ( 'SENSEX', '0' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','CE')",
                    "buySell": "S",
                    "productType": "NRML",
                    "underlyingSymbol": "SENSEX",
                },
                {
                    "optionType": "PE",
                    "expiryType": "Current Week",
                    "expiry": "tt_curr_weekexpiry('SENSEX')",
                    "strike": "( tt_ATM_SPOT ( 'SENSEX', '0' ) )",
                    "qty": "tt_lots(1,'INSTRUMENT','PE')",
                    "buySell": "S",
                    "productType": "NRML",
                    "underlyingSymbol": "SENSEX",
                },
            ],
        }],
    }],
    "universalExit": {
        "conditionValue": (
            "( PNL >= tt_Number ( '2000' ) ) or ( PNL <= tt_Number ( '-2000' )"
            " ) or ( tt_Time ( 'BSE' ) >= tt_Number ( '1510' ) )"
        )
    },
}

with open(json_path, "w", encoding="utf-8") as f:
  json.dump(payload, f, indent=2)

print(f"🎉 SENSEX Tradetron ASB JSON generated: {json_path}")