# =============================================================================
# File: 60-tools/python/fetch_option_history.py
# Description: Download Historical 1m/15m Candles for any Index Option Strike
# Runtime: Python 3.14.7 (.venv)
# =============================================================================
import datetime
import os
import sys
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


def get_option_history(
    symbol="NSE:NIFTY2690823900CE", resolution="15", days=5
):
  today = datetime.date.today()
  from_date = (today - datetime.timedelta(days=days)).strftime("%Y-%m-%d")
  to_date = today.strftime("%Y-%m-%d")

  print(f"\n📊 Fetching {resolution}m candles for: {symbol} ({from_date} to {to_date})")
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
    return None

  df = pd.DataFrame(
      res.get("candles", []),
      columns=["epoch", "open", "high", "low", "close", "volume"],
  )
  df["datetime"] = (
      pd.to_datetime(df["epoch"], unit="s")
      .dt.tz_localize("UTC")
      .dt.tz_convert("Asia/Kolkata")
  )
  df = df[["datetime", "open", "high", "low", "close", "volume"]]

  # Save to CSV in datasets
  out_dir = r"C:\kite-agent\brain\20-market-data\datasets\option_history"
  os.makedirs(out_dir, exist_ok=True)
  csv_file = os.path.join(
      out_dir, f"{symbol.replace(':', '_')}_{resolution}m.csv"
  )
  df.to_csv(csv_file, index=False)
  print(f"✅ Saved {len(df)} candles to: {csv_file}")
  print(df.tail(5).to_string(index=False))
  return df


if __name__ == "__main__":
  sym = sys.argv if len(sys.argv) > 1 else "NSE:NIFTY2690823900CE"
  res = sys.argv if len(sys.argv) > 2 else "15"
  get_option_history(symbol=sym, resolution=res)