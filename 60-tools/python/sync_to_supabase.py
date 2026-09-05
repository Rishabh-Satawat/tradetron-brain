# =============================================================================
# File: 60-tools/python/sync_to_supabase.py
# Description: Streams Fyers Option Chain & Greeks into Supabase Cloud Database
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
from supabase import create_client, Client

# 1. Load Secrets
load_dotenv(r"C:\kite-agent\secrets\supabase.env")
load_dotenv(r"C:\kite-agent\secrets\fyers.env")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

if not SUPABASE_URL or not SUPABASE_KEY:
    print("❌ Error: Missing SUPABASE_URL or SUPABASE_KEY in secrets/supabase.env")
    exit(1)

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
    FYERS_TOKEN = f.read().strip()

# Initialize API Clients
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
fyers = fyersModel.FyersModel(client_id=APP_ID, is_async=False, token=FYERS_TOKEN, log_path="")

def get_val(d, keys, default=0.0):
    for k in keys:
        v = d.get(k)
        if v is not None and v != 0 and v != "":
            return float(v)
    return default

def sync_chain_to_cloud(symbol="NSE:NIFTY50-INDEX", strike_count=15):
    print(f"\n🔄 Fetching {symbol} from Fyers and syncing to Supabase...")
    res = fyers.optionchain(data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""})

    if res.get("s") != "ok":
        print(f"❌ Fyers Error for {symbol}: {res.get('message')}")
        return

    chain_data = res.get("data", {})
    spot_price = float(chain_data.get("spotPrice", 0))
    options_list = chain_data.get("optionsChain", [])

    records_to_insert = []
    for item in options_list:
        strike = item.get("strike_price")
        if strike == -1:
            if spot_price == 0:
                spot_price = get_val(item, ["ltp", "prev_close_price", "close_price"], default=0.0)
            continue

        records_to_insert.append({
            "underlying": symbol,
            "spot_price": spot_price,
            "strike_price": float(strike),
            "option_type": item.get("option_type"),
            "ltp": get_val(item, ["ltp", "prev_close_price", "close_price"], default=0.0),
            "oi": int(get_val(item, ["oi"], default=0)),
            "volume": int(get_val(item, ["volume"], default=0)),
            "iv": get_val(item, ["iv"], default=0.0),
            "delta": get_val(item, ["delta"], default=0.0),
            "gamma": get_val(item, ["gamma"], default=0.0),
            "theta": get_val(item, ["theta"], default=0.0),
            "vega": get_val(item, ["vega"], default=0.0)
        })

    if records_to_insert:
        supabase.table("option_chain_snapshots").insert(records_to_insert).execute()
        print(f"✅ Synced {len(records_to_insert)} strike records for {symbol} to Supabase Cloud!")

if __name__ == "__main__":
    print("=" * 70)
    print("☁️ SUPABASE OPTION CHAIN SYNC ENGINE")
    print("=" * 70)
    sync_chain_to_cloud("NSE:NIFTY50-INDEX", strike_count=15)
    sync_chain_to_cloud("BSE:SENSEX-INDEX", strike_count=15)
    print("=" * 70)