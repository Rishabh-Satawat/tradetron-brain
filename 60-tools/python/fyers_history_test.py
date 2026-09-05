# =============================================================================
# File: 60-tools/python/fyers_history_test.py
# Description: Test Fyers v3 1-Minute and 15-Minute Historical Candle API
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


def fetch_historical_candles(
    symbol="NSE:NIFTY50-INDEX", resolution="1", days_back=3
):
  today = datetime.date.today()
  from_date = (today - datetime.timedelta(days=days_back)).strftime("%Y-%m-%d")
  to_date = today.strftime("%Y-%m-%d")

  print("\n" + "=" * 80)
  print(
      f"📊 FYERS HISTORICAL DATA PROBE: {symbol} | Resolution: {resolution}m |"
      f" {from_date} to {to_date}"
  )
  print("=" * 80)

  data = {
      "symbol": symbol,
      "resolution": str(resolution),
      "date_format": "1",  # YYYY-MM-DD
      "range_from": from_date,
      "range_to": to_date,
      "cont_flag": "1",
  }

  response = fyers.history(data=data)

  if response.get("s") != "ok":
    print(f"❌ Error fetching historical data: {response.get('message')}")
    return

  candles = response.get("candles", [])
  print(
      f"✅ SUCCESS: Retrieved {len(candles)} historical {resolution}-minute"
      f" candles!"
  )

  # Convert to Pandas DataFrame for easy viewing
  df = pd.DataFrame(
      candles, columns=["epoch", "open", "high", "low", "close", "volume"]
  )
  df["datetime"] = (
    pd.to_datetime(df["epoch"], unit="s")
    .dt.tz_localize("UTC")
    .dt.tz_convert("Asia/Kolkata")
)

  # Format columns for display
  print("-" * 80)
  print(f"{'Date & Time (IST)':<20} | {'Open':>9} | {'High':>9} | {'Low':>9} | {'Close':>9} | {'Volume':>9}")
  print("-" * 80)
  for _, row in df.tail(10).iterrows():
    print(
        f"{str(row['datetime']):<20} | {row['open']:>9.2f} | {row['high']:>9.2f}"
        f" | {row['low']:>9.2f} | {row['close']:>9.2f} | {row['volume']:>9,d}"
    )
  print("=" * 80)


if __name__ == "__main__":
  # 1. Test 1-Minute Historical Data on NIFTY Spot
  fetch_historical_candles(
      symbol="NSE:NIFTY50-INDEX", resolution="1", days_back=2
  )

  # 2. Test 15-Minute Historical Data on SENSEX Spot
  fetch_historical_candles(
      symbol="BSE:SENSEX-INDEX", resolution="15", days_back=5
  )