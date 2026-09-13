# =============================================================================
# File: 60-tools/python/seed_keywords.py
# Description: Seeds Verified Tradetron AST Keyword Ledger to Supabase Cloud
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import os
from dotenv import load_dotenv
from supabase import create_client

load_dotenv(r"C:\kite-agent\secrets\supabase.env")
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY")

supabase = create_client(url, key)

verified_keywords = [
    {
        "keyword_name": "Positions Detail",
        "category": "Position",
        "argument_count": 4,
        "argument_schema": {
            "inputs": [
                "Condition Type (Entry/Exit)",
                "Transaction Type (All/Buy/Sell)",
                "Instrument Type (All/Futures/Options)",
                "Underlying (e.g. SENSEX)",
            ],
            "outputs": ["Quantity", "Value", "Count"],
        },
        "return_type": "Float",
        "verified": True,
        "notes": "Scans strategy level. Safe replacement for Open positions.",
    },
    {
        "keyword_name": "Time",
        "category": "Timing",
        "argument_count": 1,
        "argument_schema": {
            "inputs": ["Exchange (NSE/BSE)"],
            "format": "Integer HHMM (e.g. 945, 1400, 1510 - No leading zero)",
        },
        "return_type": "Integer",
        "verified": True,
        "notes": "Returns exchange time as pure integer.",
    },
    {
        "keyword_name": "Days Difference (D2-D1)",
        "category": "Date",
        "argument_count": 2,
        "argument_schema": {
            "inputs": [
                "Date 1 (D1 - Subtrahend)",
                "Date 2 (D2 - Minuend)",
            ],
            "formula": "D2 - D1 (Positive when D2 is in future)",
        },
        "return_type": "Integer",
        "verified": True,
        "notes": (
            "In UI popup: Date 1 = Today, Date 2 = Expiry. Subtracts Date 1"
            " from Date 2."
        ),
    },
    {
        "keyword_name": "Position",
        "category": "SeriesWrapper",
        "argument_count": 2,
        "argument_schema": {
            "inputs": [
                "Series/Indicator",
                "Candle Offset (-1 for closed, -2 for prior)",
            ]
        },
        "return_type": "Series",
        "verified": True,
        "notes": (
            "Mandatory wrapper around RSI, ADX, EMA, Supertrend, Close, High."
        ),
    },
    {
        "keyword_name": "RSI",
        "category": "Indicator",
        "argument_count": 3,
        "argument_schema": {
            "inputs": [
                "Symbol (Instrument Name)",
                "Timeframe (e.g. 15m)",
                "Period (e.g. 14)",
            ]
        },
        "return_type": "Float",
        "verified": True,
        "notes": "Used under Position keyword.",
    },
    {
        "keyword_name": "ADX",
        "category": "Indicator",
        "argument_count": 2,
        "argument_schema": {
            "inputs": ["Symbol (Instrument Name)", "Period (e.g. 14)"]
        },
        "return_type": "Float",
        "verified": True,
        "notes": (
            "Measures trend strength, NOT direction. Used under Position."
        ),
    },
    {
        "keyword_name": "DI+",
        "category": "Indicator",
        "argument_count": 2,
        "argument_schema": {
            "inputs": ["Symbol (Instrument Name)", "Period (e.g. 14)"]
        },
        "return_type": "Float",
        "verified": True,
        "notes": (
            "Positive directional movement index. Used under Position."
        ),
    },
    {
        "keyword_name": "DI-",
        "category": "Indicator",
        "argument_count": 2,
        "argument_schema": {
            "inputs": ["Symbol (Instrument Name)", "Period (e.g. 14)"]
        },
        "return_type": "Float",
        "verified": True,
        "notes": (
            "Negative directional movement index. Used under Position."
        ),
    },
    {
        "keyword_name": "PNL",
        "category": "PnL",
        "argument_count": 2,
        "argument_schema": {
            "inputs": ["strategy_id", "run_counter"],
            "scaling": "Compare with Target/Stop * Multiplier",
        },
        "return_type": "Float",
        "verified": True,
        "notes": "Whole-strategy PnL. Belongs in Universal Exit only.",
    },
    {
        "keyword_name": "Multiplier",
        "category": "Scaling",
        "argument_count": 1,
        "argument_schema": {"inputs": ["strategy_id"]},
        "return_type": "Integer",
        "verified": True,
        "notes": "Returns deployment multiplier (1, 2, 3...).",
    },
    {
        "keyword_name": "ATM SPOT",
        "category": "StrikeSelector",
        "argument_count": 2,
        "argument_schema": {
            "inputs": [
                "Underlying (e.g. SENSEX)",
                "Offset in strike steps (e.g. 0, +5, -5)",
            ]
        },
        "return_type": "Integer",
        "verified": True,
        "notes": "Spot index-anchored strike selector.",
    },
]

print("=" * 65)
print("🧠 SEEDING TRADETRON KEYWORD BRAIN TO SUPABASE CLOUD")
print("=" * 65)

res = (
    supabase.table("tradetron_keywords")
    .upsert(verified_keywords, on_conflict="keyword_name")
    .execute()
)
print(f"✅ Successfully seeded {len(verified_keywords)} verified AST keywords!")
print("=" * 65)