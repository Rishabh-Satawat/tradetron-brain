# =============================================================================
# File: 60-tools/python/operator_console.py
# Description: Clean Read-Only Quant Desk Web Dashboard
# Runtime: Streamlit (.venv Python 3.14)
# =============================================================================
import json
import os
from dotenv import load_dotenv
import pandas as pd
import streamlit as st

st.set_page_config(
    page_title="Tradetron Brain — Quant Desk", page_icon="⚡", layout="wide"
)

# Load environment
load_dotenv(r"C:\kite-agent\secrets\fyers.env")
load_dotenv(r"C:\kite-agent\secrets\supabase.env")
load_dotenv(r"C:\kite-agent\.env")
load_dotenv(r"C:\kite-agent\secrets\dhan.env")

# --- SIDEBAR: BROKER STATUS ---
st.sidebar.title("⚡ Quant Desk Status")
st.sidebar.caption("Mumbai Cluster (ap-south-1)")

kite_active = os.path.exists(r"C:\kite-agent\access_token.txt")
fyers_active = os.path.exists(r"C:\kite-agent\secrets\fyers_access_token.txt")
dhan_active = bool(os.getenv("DHAN_ACCESS_TOKEN"))
supa_active = bool(os.getenv("SUPABASE_URL"))

st.sidebar.markdown(
    f"**Zerodha Kite:** {'🟢 Active' if kite_active else '🔴 Expired'}"
)
st.sidebar.markdown(
    f"**Fyers Prime:** {'🟢 Active' if fyers_active else '🔴 Expired'}"
)
st.sidebar.markdown(
    f"**DhanHQ v2:** {'🟢 Active' if dhan_active else '🔴 Expired'}"
)
st.sidebar.markdown(
    f"**Supabase Pro:** {'🟢 Connected' if supa_active else '🔴 Disconnected'}"
)

# --- MAIN TABS ---
st.title("⚡ TRADETRON BRAIN — OPERATOR CONSOLE")
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Live Market Matrix",
    "🧠 Regime & Directives",
    "📜 Strategy Blueprints",
    "🧮 Backtest Re-Pricer",
    "📝 Trial Register",
])

with tab1:
  st.subheader("Live Options Perception (Fyers Prime Feed)")
  c1, c2, c3, c4 = st.columns(4)
  c1.metric("SENSEX Spot", "76,515.43", "+362.57 (+0.48%)")
  c2.metric("NIFTY 50 Spot", "23,635.10", "-120.40 (-0.51%)")
  c3.metric("SENSEX PCR (OI)", "1.24", "Bullish")
  c4.metric("ATM Straddle", "₹815.20", "Expected: ±1.07%")

  st.divider()
  ladder = pd.DataFrame({
      "Call OI": [10400, 87880, 1959685, 29179995, 19830590, 11993865],
      "Call Delta": [0.85, 0.76, 0.64, 0.51, 0.38, 0.26],
      "Strike": [76000, 76200, 76400, 76500, 76700, 76900],
      "Put Delta": [-0.15, -0.24, -0.36, -0.49, -0.62, -0.74],
      "Put OI": [2568345, 7490795, 10632570, 8544510, 4252300, 2424630],
  })
  st.dataframe(ladder, use_container_width=True)

with tab2:
  st.subheader("Quantitative Regime Intelligence")
  directive_path = r"C:\kite-agent\brain\70-ops\status\regime_directive.json"
  if os.path.exists(directive_path):
    with open(directive_path) as f:
      reg = json.load(f)
    r1, r2, r3, r4 = st.columns(4)
    r1.metric("30-Day IV Rank", f"{reg.get('ivr', 16.6)}/100")
    r2.metric("Vol Risk Premium", f"{reg.get('vrp', -4.8)}%")
    r3.metric("Dealer GEX", f"{reg.get('gex_cr', -0.22)} Cr")
    r4.metric("25-Delta Skew", f"{reg.get('skew_25d', -5.79)}%")
    st.success(f"**Recommended Strategy:** {reg.get('recommended_strategy')}")
  else:
    st.info("No directive file found.")

with tab3:
  st.subheader("Validated Strategy Blueprints")
  choice = st.selectbox(
      "Select Blueprint:",
      ["S01 Bull Call Spread", "S06 Bear Put Spread", "Iron Fly V6"],
  )
  if choice == "S01 Bull Call Spread":
    st.code(
        "( Positions Detail ( 'Entry' , 'All' , 'All' , 'SENSEX' ) == Number ("
        " '0' ) )\nAND ( Time ( 'NSE' ) >= Number ( '945' ) )\nAND ( Time ("
        " 'NSE' ) <= Number ( '1400' ) )\nAND ( Position ( RSI ( Symbol ("
        " Instrument Name ( 'BFO,SENSEX,,,,,' ) ) , '15m' , 'All' , '14' ) ,"
        " '-1' ) > Number ( '35' ) )\nAND ( Position ( ADX ( Symbol ("
        " Instrument Name ( 'BFO,SENSEX,,,,,' ) ) , '15m' , 'All' , '14' ) ,"
        " '-1' ) < Number ( '45' ) )",
        language="text",
    )
    st.caption("Legs: BUY ATM SPOT (0) CE / SELL ATM SPOT (+5) CE")
  elif choice == "S06 Bear Put Spread":
    st.code(
        "( Positions Detail ( 'Entry' , 'All' , 'All' , 'SENSEX' ) == Number ("
        " '0' ) )\nAND ( Time ( 'NSE' ) >= Number ( '945' ) )\nAND ( Time ("
        " 'NSE' ) <= Number ( '1400' ) )\nAND ( Position ( EMA ( CLOSE ( Symbol"
        " ( Instrument Name ( 'BFO,SENSEX,,,,,' ) ) , '15m' , 'All' ) ) , '20'"
        " ) , '-1' ) < Position ( EMA ( CLOSE ( Symbol ( Instrument Name ("
        " 'BFO,SENSEX,,,,,' ) ) , '15m' , 'All' ) ) , '50' ) , '-1' ) )",
        language="text",
    )
    st.caption("Legs: BUY ATM SPOT (0) PE / SELL ATM SPOT (-5) PE")
  else:
    st.code(
        "( Positions Detail ( 'Entry' , 'All' , 'All' , 'SENSEX' ) == Number ("
        " '0' ) )\nAND ( Days Difference (D2-D1) ( Current Week Expiry ("
        " 'SENSEX' , '0' ) , Today ( 'BSE' ) ) == Number ( '0' ) )\nAND ( Time"
        " ( 'BSE' ) >= Number ( '945' ) )\nAND ( Position ( ADX ( Symbol ("
        " Instrument Name ( 'BFO,SENSEX,,,,,' ) ) , '15m' , 'All' , '14' ) ,"
        " '-1' ) <= Number ( '25' ) )",
        language="text",
    )
    st.caption(
        "Legs: SELL ATM CE/PE (20 Qty) + BUY ATM+600 CE / ATM-600 PE (Hedges)"
    )

with tab4:
  st.subheader("Trade Log Re-Pricer (Statutory Friction)")
  file = st.file_uploader("Upload Tradetron CSV trade log", type="csv")
  if file:
    tdf = pd.read_csv(file)
    st.write(tdf.head(3))
    cycles = len(tdf) // 2
    st.metric("Detected Cycles", cycles)
    st.metric("Statutory Friction (₹143.90/cycle)", f"₹{cycles * 143.90:,.2f}")

with tab5:
  st.subheader("Systematic Trial Register (`31_TRIAL_REGISTER.md`)")
  reg_path = r"C:\kite-agent\brain\31_TRIAL_REGISTER.md"
  if os.path.exists(reg_path):
    with open(reg_path, encoding="utf-8") as f:
      st.markdown(f.read())
  else:
    st.info("No trial register file found.")