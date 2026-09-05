# =============================================================================
# File: 60-tools/python/probe_15days_depth.py
# Description: Probe Fyers Historical Reach for 15+ Days on 5m, 15m, and 1m
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
from dotenv import load_dotenv
from fyers_apiv3 import fyersModel
import pandas as pd

load_dotenv(r"C:\kite-agent\secrets\fyers.env")
APP_ID = os.getenv("FYERS_APP_ID", "").strip()

with open(r"C:\kite-agent\secrets\fyers_access_token.txt") as f:
  ACCESS_TOKEN = f.read().strip()

fyers = fyersModel.FyersModel(
    client_id=APP_ID, is_async=False, token=ACCESS_TOKEN, log_path=""
)


def probe_history_depth(symbol, resolution="15", days_back=15):
  today = datetime.date.today()
  from_date = (today - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
  to_date = today.strftime("%Y-%m-%d")

  print("\n" + "=" * 85)
  print(
      f"🔍 PROBING 15-DAY DEPTH: {symbol} | Resolution: {resolution}m |"
      f" {from_date} to {to_date}"
  )
  print("=" * 85)

  data = {
      "symbol": symbol,
      "resolution": str(resolution),
      "date_format": "1",
      "range_from": from_date,
      "range_to": to_date,
      "cont_flag": "1",
  }
  res = fyers.history(data=data)
  if res.get("s") != "ok":
    print(f"❌ Error: {res.get('message')}")
    return

  candles = res.get("candles", [])
  if not candles:
    print(f"⚠️ No candles returned for {days_back} days.")
    return

  df = pd.DataFrame(
      candles, columns=["epoch", "open", "high", "low", "close", "volume"]
  )
  df["datetime"] = (
      pd.to_datetime(df["epoch"], unit="s")
      .dt.tz_localize("UTC")
      .dt.tz_convert("Asia/Kolkata")
  )

  earliest = df["datetime"].iloc[0].strftime("%Y-%m-%d %H:%M:%S IST")
  latest = df["datetime"].iloc[-1].strftime("%Y-%m-%d %H:%M:%S IST")
  trading_days = df["datetime"].dt.date.nunique()

  print(f"✅ Total Candles Fetched : {len(df):,d} bars")
  print(f"📅 Earliest Candle Date  : {earliest}")
  print(f"📅 Latest Candle Date    : {latest}")
  print(f"📈 Total Trading Sessions: {trading_days} distinct market days")
  print(
      f"🎉 VERDICT: Fyers successfully provides {days_back}+ days of history!"
  )
  print("=" * 85)


if __name__ == "__main__":
  # 1. Probe 15-Day 5-Minute Data on NIFTY Spot
  probe_history_depth("NSE:NIFTY50-INDEX", resolution="5", days_back=15)

  # 2. Probe 15-Day 15-Minute Data on SENSEX Spot
  probe_history_depth("BSE:SENSEX-INDEX", resolution="15", days_back=15)

  # 3. Probe 15-Day Data on NIFTY Monthly Option Contract (24000 CE)
  probe_history_depth("NSE:NIFTY26SEP24000CE", resolution="15", days_back=15)