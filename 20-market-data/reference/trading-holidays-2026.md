# Trading Holidays 2026 (NSE + BSE) — [V] VERIFIED 2026-09-01

## Sources
- NSE circular (primary): https://nsearchives.nseindia.com/content/circulars/CMTR71775.pdf
- BSE list (primary): https://www.bseindia.com/static/markets/marketinfo/listholi
- Cross-check: https://zerodha.com/marketintel/holiday-calendar/
- Machine-readable: 20-market-data/reference/trading-holidays-2026.csv

## Answer to open question
2026-11-24 (Tuesday) IS an NSE and BSE holiday: Prakash Gurpurb Sri Guru Nanak Dev.
CROSS-VALIDATION: B0 probe independently observed NIFTY expiry on Monday 2026-11-23.
This confirms BOTH the calendar AND the previous-trading-day expiry shift rule.

## Expiry-day holidays
NIFTY weekly expiry is Tuesday. Tuesday holidays 2026:
  2026-03-03, 2026-03-31, 2026-04-14, 2026-10-20, 2026-11-10, 2026-11-24
SENSEX weekly expiry is Thursday. Thursday holidays 2026:
  2026-01-15, 2026-03-26, 2026-05-28

## Shifted expiries inside backtest windows
PRIMARY WINDOW 2026-04-01 to 2026-08-31:
  NIFTY  Tue 2026-04-14 -> Mon 2026-04-13
  SENSEX Thu 2026-05-28 -> Wed 2026-05-27
SECONDARY WINDOW 2026-02-01 to 2026-03-31:
  NIFTY  Tue 2026-03-03 -> Mon 2026-03-02
  SENSEX Thu 2026-03-26 -> Wed 2026-03-25
  NIFTY  Tue 2026-03-31 -> Mon 2026-03-30
Five shifted cycles total. Any backtest assuming fixed weekday misprices these five.

## Weekend-falling holidays (no market impact)
2026-02-15 Sun Maha Shivaratri; 2026-03-21 Sat Eid-Ul-Fitr;
2026-08-15 Sat Independence Day; 2026-11-08 Sun Diwali Laxmi Pujan (Muhurat session)

## Open
[O] Muhurat trading session timing for 2026-11-08 to be notified by separate NSE circular.
[O] Shift rule is "previous trading day" - CONFIRMED for 2026-11-23 only. Validate the
    remaining shifted dates against the instrument dumps (see validate_expiry_shifts.py).

<!-- END OF FILE: trading-holidays-2026.md -->
