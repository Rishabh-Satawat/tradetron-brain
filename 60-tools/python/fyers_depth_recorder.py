# =============================================================================
# File: 60-tools/python/fyers_depth_recorder.py
# Description: Live Market 1-Minute Ingestion with Level-2 Bid/Ask Depth
# Ingests: NIFTY 50, SENSEX Spot + Active ATM Options into Supabase & Parquet
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
import time
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import pandas as pd
from supabase import create_client, Client

# Load environment
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")

APP_ID = os.getenv("FYERS_APP_ID", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip()
SUPABASE_KEY = (
    os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "").strip()
)
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"

if not os.path.exists(TOKEN_PATH):
  print(f"❌ Error: {TOKEN_PATH} missing. Run start_desk.ps1 first.")
  sys.exit(1)

with open(TOKEN_PATH) as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)
supabase: Client = (
    create_client(SUPABASE_URL, SUPABASE_KEY)
    if (SUPABASE_URL and SUPABASE_KEY)
    else None
)

# Active Contracts for Today's Session
TRACKED_SYMBOLS = [
    "NSE:NIFTY50-INDEX",
    "BSE:SENSEX-INDEX",
    "NSE:FINNIFTY-INDEX",
    "NSE:NIFTY2691523650CE",
    "NSE:NIFTY2691523650PE",
    "BSE:SENSEX2691774800CE",
    "BSE:SENSEX2691774800PE",
]


def record_depth_snapshot():
  now_ist = datetime.datetime.now()
  now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()

  symbols_str = ",".join(TRACKED_SYMBOLS)
  q_res = fyers.quotes(data={"symbols": symbols_str})

  if q_res.get("s") != "ok":
    print(f"⚠️ Quotes fetch failed: {q_res.get('message')}")
    return

  quotes_data = q_res.get("d", [])
  records = []

  for item in quotes_data:
    v = item.get("v", {})
    sym = item.get("n", "")

    lp = float(
        v.get("lp") or v.get("prev_close_price") or v.get("cmd", {}).get("c", 0)
    )
    open_p = float(v.get("open_price", lp))
    high_p = float(v.get("high_price", lp))
    low_p = float(v.get("low_price", lp))
    vol = int(v.get("volume", 0))
    oi = int(v.get("oi", 0))

    # Level-2 Bid/Ask Depth
    bid = float(v.get("bid", lp))
    ask = float(v.get("ask", lp))
    bid_qty = int(v.get("bid_qty", 0))
    ask_qty = int(v.get("ask_qty", 0))
    spread = round(ask - bid, 2)

    records.append({
        "timestamp": now_ist.strftime("%Y-%m-%d %H:%M:%S"),
        "event_time_utc": now_utc,
        "symbol": sym,
        "open": open_p,
        "high": high_p,
        "low": low_p,
        "close": lp,
        "volume": vol,
        "oi": oi,
        "bid_price": bid,
        "ask_price": ask,
        "bid_qty": bid_qty,
        "ask_qty": ask_qty,
        "spread": spread,
    })

  if not records:
    return

  df_batch = pd.DataFrame(records)

  # 1. Local Parquet Append (Zero-Loss Archive)
  today_str = now_ist.strftime("%Y%m%d")
  out_dir = r"C:\kite-agent\brain\20-market-data\datasets\snapshots"
  os.makedirs(out_dir, exist_ok=True)
  parquet_file = os.path.join(out_dir, f"depth_1m_{today_str}.parquet")

  if os.path.exists(parquet_file):
    existing_df = pd.read_parquet(parquet_file)
    df_batch = pd.concat([existing_df, df_batch], ignore_index=True)
  df_batch.to_parquet(parquet_file, index=False)

  # 2. Supabase Cloud Ingestion
  if supabase:
    supabase_payload = []
    for r in records:
      supabase_payload.append({
          "timestamp": r["timestamp"],
          "symbol": r["symbol"],
          "open": r["open"],
          "high": r["high"],
          "low": r["low"],
          "close": r["close"],
          "volume": r["volume"],
          "oi": r["oi"],
          "bid_price": r["bid_price"],
          "ask_price": r["ask_price"],
      })
    try:
      supabase.table("market_bars_1m").insert(supabase_payload).execute()
    except Exception as e:
      pass

  sensex_spot = next(
    (r["close"] for r in records if "SENSEX-INDEX" in r["symbol"]),
    records[0]["close"],
)
sensex_spread = next(
    (r["spread"] for r in records if "SENSEX-INDEX" in r["symbol"]),
    records[0]["spread"],
)
print(
    f"⚡ [{now_ist.strftime('%H:%M:%S')}] Logged {len(records)} symbols with"
    f" Bid/Ask Depth (SENSEX: ₹{sensex_spot:,.2f} | Spread: ₹{sensex_spread})"
)


def start_recorder_daemon():
  print("=" * 85)
  print("📡 LIVE 1-MINUTE MARKET DEPTH RECORDER — ACTIVE")
  print(f"🎯 Tracking: {len(TRACKED_SYMBOLS)} Core Index & Option Contracts")
  print("=" * 85)

  while True:
    try:
      record_depth_snapshot()
      time.sleep(60.0)  # Runs every 60 seconds
    except KeyboardInterrupt:
      print("\n🛑 Recorder stopped by user.")
      break
    except Exception as e:
      print(f"⚠️ Error: {e}")
      time.sleep(5.0)


if __name__ == "__main__":
  start_recorder_daemon()