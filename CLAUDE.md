# TRADETRON BRAIN — INSTITUTIONAL QUANT PROP DESK & RISK TERMINAL
**System Codename:** `TRADETRON-BRAIN-V3`
**Target Markets:** Indian Derivatives — National Stock Exchange (NSE) & Bombay Stock Exchange (BSE)
**Core Assets:** BSE SENSEX (`BFO`), NSE NIFTY 50 (`NFO`), NSE FINNIFTY (`NFO`)
**Environment Root:** `C:\kite-agent\brain\`
**Python Virtual Environment:** `C:\kite-agent\.venv\Scripts\python.exe` (Python 3.14.7)
**Cloud Database:** Supabase Pro (`quant-desk`) in Mumbai (`ap-south-1`)
**Remote Repository:** `https://github.com/Rishabh-Satawat/tradetron-brain` (Branch: `main`)

---

## 1. VISION & SYSTEM PURPOSE
This platform is an institutional-grade quantitative research, market perception, and algorithmic trading terminal for Indian index options.

### Core Objectives:
1. **Continuous Market Perception:** Ingests live order books, 41-strike option chains, and historical candles from Fyers Prime API v3, DhanHQ v2, and Zerodha Kite Connect.
2. **Mathematical Inversion & Greeks:** Solves point-in-time Implied Volatility (IV) using Fisher Black’s 1976 model (Black-76) via Brent’s root-finding method. Computes true Delta, Gamma, Theta, and Vega across all active strikes.
3. **6-Dimensional Market Regime Intelligence:** Evaluates Spot Momentum, Volatility Risk Premium (VRP = IV - RV), 30-Day IV Rank, Net Dealer Gamma Exposure (GEX Proxy), 4-Quadrant Open Interest Dynamics, and Strike Centroid Migration to prescribe the statistically optimal strategy structure.
4. **Deterministic Tradetron AST Compiler:** Converts regime prescriptions into fail-closed, syntax-validated Tradetron Advanced Strategy Builder (ASB v2) condition-builder blueprints (with dynamically snapped strikes and multiplier-safe exits).
5. **Live Demat Risk & Real-Time Hedging Assistant:** Inspects open broker positions and portfolio Greeks, detects institutional volume delta and OI unwinding against active positions, and issues automated risk-mitigation and hedging directives.

---

## 2. NON-NEGOTIABLE REPOSITORY POLICIES & LESSONS LEARNED

The following rules represent hard-won operational lessons and must never be violated:

### A. Credential Security & Sanitization:
* **ZERO CREDENTIAL LEAKAGE:** Never log, print, or expose raw passwords, TOTP codes, access tokens, API secrets, client IDs, or available cash balances to stdout or terminal logs.
* **SECRETS LOCATION:** All credentials live exclusively in `C:\kite-agent\secrets\` (`fyers.env`, `dhan.env`, `supabase.env`) and `C:\kite-agent\.env` (Kite). These directories are strictly git-ignored.
* **READ-ONLY CLOUD BOUNDARY:** Any cloud background worker must use read-only market-data credentials. Never store order-placement credentials on remote cloud VMs without registered static IPs (SEBI Algorithmic Trading Compliance).

### B. Mathematical & Greeks Precision:
* **ZERO-VOLUME GUARD:** Never invert IV on zero-volume candles or stale prints. A frozen option price combined with a decaying clock forces mathematical solvers to collapse IV to unphysical levels (e.g. 2% or 6%), creating false VRP signals. If Volume == 0, mark IV as NULL or carry the last valid active trade IV.
* **CORRECT GEX FORMULATION:** Never double-count contract multipliers. Fyers Open Interest (`oi`) is already reported in total shares (quantity). GEX Proxy formula:
  $$\text{Call GEX} = \text{Call OI} \times S^2 \times \Gamma_{\text{Call}} \times 0.01$$
  $$\text{Put GEX} = \text{Put OI} \times S^2 \times \Gamma_{\text{Put}} \times 0.01$$
  $$\text{Net GEX} = \text{Call GEX} - \text{Put GEX}$$
* **FAIL-CLOSED SPOT RESOLUTION:** Never use hardcoded spot fallbacks. If live index spot cannot be verified from active quotes or the `strike == -1` record, the pipeline must halt with an error.

### C. Tradetron Architecture & Syntax:
* **MULTIPLIER-SAFE EXITS:** Whole-strategy PNL exits belong strictly in **Universal Exit**, never duplicated in Set Exit. Always multiply rupee thresholds by the deployment multiplier:
  `PNL >= Number(2000) * Multiplier` and `PNL <= Number(-1200) * Multiplier`.
* **DAYS DIFFERENCE ORIENTATION:** Tradetron calculates $D2 - D1$. In the UI popup: Date 1 = `Today`, Date 2 = `Current Week Expiry`. Result is positive for future expiries:
  `Days Difference ( Current Week Expiry , Today ) >= Number(1)`.
* **CANDLE OFFSETS:** Technical indicators (RSI, ADX, EMA, Supertrend) must always evaluate on completed closed candles (offset `-1`, with `-2` for crossover verification).
* **INTEGER TIME FORMAT:** Clocks evaluate as raw integers without leading zeros: `Number(945)`, `Number(1400)`, `Number(1510)`. Never write `0945`.
* **EXECUTION SETTINGS:** Always configure `Exit At Market Price = YES` and `Exit Shorts First = YES` with a 60-second revision timeout.

### D. Code Architecture:
* **STREAMLIT READ-ONLY INTEGRITY:** Dashboards must never write to disk or execute file-modifying scripts on page load. File modifications trigger Streamlit's file watcher, causing infinite reload loops.
* **PURE PYTHON EXECUTION:** Never paste PowerShell wrapper syntax (`@' ... '@`) inside `.py` files.

---

## 3. FILE INVENTORY & LOCAL RUNTIME REPOSITORY MAP

C:\kite-agent

├── .env                               <── Kite Connect API Key, Secret, User ID, Password, TOTP Secret
├── access_token.txt                   <── Active Zerodha Kite 24-hour access token
├── generate_token.py                  <── 1-click Kite OAuth listener on port 5000
├── test_kite.py                       <── Verified Kite profile & funds probe (₹4.09L cash)
├── secrets

│   ├── fyers.env                      <── Fyers App ID, Secret, User ID, PIN, TOTP Secret
│   ├── fyers_access_token.txt         <── Active Fyers Prime 24-hour JWT token
│   ├── dhan.env                       <── Dhan Client ID (1111831735), PIN, TOTP Secret, Access Token
│   └── supabase.env                   <── Supabase Pro URL (Mumbai) & Service Role API keys
└── brain\                             <── Git Repository Root (github.com/Rishabh-Satawat/tradetron-brain)
├── .cursorrules                   <── Cursor IDE System Rules
├── CLAUDE.md                      <── Claude Code Context & Instructions
├── 31_TRIAL_REGISTER.md           <── Canonical strategy trial ledger (TR-001, TR-002 logged)
├── start_desk.ps1                 <── 1-click master launcher calling preflight_check.py
│
├── 20-market-data

│   └── datasets\option_history\   <── Historical Options CSVs (1m, 5m, 15m with Greeks)
│       ├── SENSEX_30DAYS_5M_FULL_CHAIN.csv
│       ├── SENSEX_DYNAMIC_ROLLED_ATM_SERIES.csv
│       └── DATASET_SENSEX_60DAYS_1M_*.csv
│
├── 30-strategies\                 <── Verified Tradetron Blueprints & Build Sheets
│   ├── SENSEX_RSI_BULL_SPREAD.md             <── S01 Bull Call Spread (+12% Net, 2.22x Payoff)
│   ├── S06_SENSEX_BEAR_PUT_SPREAD.md         <── S06 Bear Put Spread (EMA Pullback Rejection)
│   ├── SENSEX_IRON_FLY_V5_BUILD_SHEET.md     <── SENSEX 0-DTE Expiry Iron Fly V6
│   └── DYNAMIC_REGIME_STRATEGY.md            <── Live strategy generated by tradetron_compiler.py
│
├── 60-tools\python\               <── Production Quantitative Engines & Tools
│   ├── preflight_check.py                    <── Fail-closed health audit across all 4 systems
│   ├── dhan_auto_login.py                    <── Headless automated PIN+TOTP login for DhanHQ v2
│   ├── dhan_profile_probe.py                 <── Probes Dhan profile & subscription validity
│   ├── fyers_live_desk.py                    <── Real-time 41-strike matrix & Black-76 Greeks engine
│   ├── kite_auto_login.py                    <── Headless Kite Connect login & consent handler
│   ├── zerodha_charges.py                    <── Statutory friction engine (reconciled to ₹0.00)
│   ├── universal_greeks_history.py           <── Universal historical candle & Greeks engine
│   ├── extract_sensex_30days_chain.py        <── 30-day 5m multi-strike chain extractor
│   ├── build_dynamic_rolled_atm_series.py    <── Compiles continuous dynamic ATM series
│   ├── simulate_sensex_spread.py             <── Quantitative backtester on dynamic series
│   ├── unified_quant_engine.py               <── 6D Quant Brain (Spot, IV, GEX, 4-Quadrant OI)
│   ├── tradetron_compiler.py                 <── Deterministic Tradetron AST strategy compiler
│   ├── log_trial_result.py                   <── Logs trials to Markdown & Supabase
│   └── operator_console.py                   <── Streamlit Web Console running at localhost:8501
│
└── 70-ops\status

└── regime_directive.json                 <── Active machine directive emitted by quant engine

--

## 4. SUPABASE PRO DATABASE ARCHITECTURE (`quant-desk`)
Host: `https://yhbbnqiwkwquvoxussjj.supabase.co` | Region: South Asia (Mumbai `ap-south-1`):
* `public.market_instruments`: Master directory for exchange contracts, lot sizes, tick sizes.
* `public.market_bars_1s`: Partitioned time-series for raw high-resolution ticks.
* `public.market_bars_1m`: Continuous 1-minute pre-aggregated OHLCV & OI table.
* `public.market_bars_15m`: 15-minute strategy bars (enables scanning full trading sessions in 25 rows).
* `public.option_chain_snapshots`: Full strike matrix storing Spot, Strike, Type, LTP, OI, Volume, IV, Delta, Gamma, Theta, Vega.
* `public.tradetron_keywords`: Cloud store of 11 verified Tradetron AST keywords, argument schemas, and return types.
* `public.strategy_trials`: Strategy ledger logging Gross P&L, Friction, Net P&L, Drawdown, Sharpe Ratio, and Verdicts.
* `public.get_resampled_bars(...)`: Stored SQL function executing dynamic on-demand time-bucket resampling.

---

## 5. STATUTORY FRICTION & EXECUTION COST STANDARDS
All backtests and strategy evaluations must pass through `zerodha_charges.py`. We never evaluate gross returns.
* **Standard Friction per 2-Leg Round Trip:** ~**₹143.90** (Brokerage: ₹40, STT: 0.15% on sell turnover post-April 2026, Exchange fees, GST, Stamp Duty).
* **Standard Friction per 4-Leg Iron Fly:** ~**₹211.50**.
* **Slippage Modeling:** Add 1 tick (₹0.05 on NIFTY, ₹0.05 on SENSEX) or minimum 1.5–2.0 points on market-order entries.