# =============================================================================
# File: 60-tools/python/write016_fyers_snapshotter.py
# Description: Automated Parquet Option Chain Snapshotter for SENSEX & NIFTY
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import pandas as pd

SECRETS_PATH = r"C:\kite-agent\secrets\fyers.env"
TOKEN_PATH = r"C:\kite-agent\secrets\fyers_access_token.txt"
DATASET_DIR = r"C:\kite-agent\brain\20-market-data\datasets\snapshots"

os.makedirs(DATASET_DIR, exist_ok=True)
load_dotenv(SECRETS_PATH)
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(TOKEN_PATH) as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


def get_val(d, keys, default=0.0):
  for k in keys:
    v = d.get(k)
    if v is not None and v != 0 and v != "":
      return float(v)
  return default


def snapshot_symbol(symbol="NSE:NIFTY50-INDEX", strike_count=20):
  res = fyers.optionchain(
      data={"symbol": symbol, "strikecount": strike_count, "timestamp": ""}
  )
  if res.get("s") != "ok":
    print(f"❌ Error snapshotting {symbol}: {res.get('message')}")
    return None

  chain = res.get("data", {})
  spot = float(chain.get("spotPrice", 0))
  options = chain.get("optionsChain", [])
  now_iso = datetime.datetime.now().isoformat()

  rows = []
  for item in options:
    strike = item.get("strike_price")
    if strike == -1:
      continue
    rows.append({
        "timestamp": now_iso,
        "underlying": symbol,
        "spot_price": spot,
        "strike_price": strike,
        "option_type": item.get("option_type"),
        "ltp": get_val(
            item, ["ltp", "prev_close_price", "close_price"], default=0.0
        ),
        "oi": int(get_val(item, ["oi"], default=0)),
        "volume": int(get_val(item, ["volume"], default=0)),
        "iv": get_val(item, ["iv"], default=0.0),
        "delta": get_val(item, ["delta"], default=0.0),
        "gamma": get_val(item, ["gamma"], default=0.0),
        "theta": get_val(item, ["theta"], default=0.0),
        "vega": get_val(item, ["vega"], default=0.0),
    })

  df = pd.DataFrame(rows)
  today_str = datetime.date.today().strftime("%Y%m%d")
  sym_clean = symbol.replace(":", "_").replace("-", "_")
  parquet_path = os.path.join(
      DATASET_DIR, f"{sym_clean}_chain_{today_str}.parquet"
  )

  if os.path.exists(parquet_path):
    existing_df = pd.read_parquet(parquet_path)
    df = pd.concat([existing_df, df], ignore_index=True)

  df.to_parquet(parquet_path, index=False)
  print(
      f"✅ Snapshotted {len(rows)} rows for {symbol} ->"
      f" {os.path.basename(parquet_path)}"
  )
  return len(rows)


if __name__ == "__main__":
  print("=" * 75)
  print("📦 FYERS OPTION CHAIN PARQUET SNAPSHOTTER")
  print("=" * 75)
  snapshot_symbol("NSE:NIFTY50-INDEX", 20)
  snapshot_symbol("BSE:SENSEX-INDEX", 20)
  print("=" * 75)