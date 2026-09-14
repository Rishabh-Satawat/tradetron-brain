# NIFTY 50 0-DTE Weekly Expiry Iron Fly V6 — Tradetron Build Sheet
# Generated on 2026-09-14 15:37:32 IST for Tuesday Expiry
# Underlying: NSE NIFTY 50 (NFO) | Lot Size: 65 | Strike Step: 50 points

## Strategy Profile:
- Strategy Name: NIFTY 0-DTE Expiry Iron Fly V6
- Target Profit: +₹2,500 * Multiplier
- Stop Loss: -₹2,500 * Multiplier
- Intraday Time Exit: 03:10 PM IST
- Dynamic ATM Anchor: 23400
- Protective Wings: +250 pts (23650 CE) / -250 pts (23150 PE)

---

## SET 1 — ENTRY CONDITION (0-DTE Tuesday Expiry Rangebound):
```text
( Positions Detail ( 'Entry' , 'All' , 'All' , 'NIFTY 50' ) == Number ( '0' ) )
AND ( Days Difference (D2-D1) ( Current Week Expiry ( 'NIFTY 50' , '0' ) , Today ( 'NSE' ) ) == Number ( '0' ) )
AND ( Time ( 'NSE' ) >= Number ( '930' ) )
AND ( Time ( 'NSE' ) <= Number ( '1400' ) )
AND ( Position ( ADX ( Symbol ( Instrument Name ( 'NFO,NIFTY 50,,,,,' ) ) , '15m' , 'All' , '14' ) , '-1' ) <= Number ( '25' ) )
```

---

## POSITION BUILDER (4 LEGS — MARGIN HEDGED SEQUENCE):
> Note: On entry, execute BUY wing legs (Leg 3 & 4) first to get SEBI margin relief before writing ATM legs!

| Leg # | Action | Exchange | Underlying | Expiry Selector | Strike Selection | Lots | Type | Order Type | Product |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| Leg 1 | SELL | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( 0 ) | 1 (65 Qty) | CE | Market | NRML |
| Leg 2 | SELL | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( 0 ) | 1 (65 Qty) | PE | Market | NRML |
| Leg 3 | BUY  | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( +5 ) | 1 (65 Qty) | CE | Market | NRML |
| Leg 4 | BUY  | NFO | NIFTY 50 | Current Week (0) | ATM SPOT ( -5 ) | 1 (65 Qty) | PE | Market | NRML |

---

## SET 1 — UNIVERSAL EXIT CONDITIONS:
```text
( PNL ( 'strategy_id' , 'run_counter' ) >= Number ( '2500' ) * Multiplier ( 'strategy_id' ) )
OR ( PNL ( 'strategy_id' , 'run_counter' ) <= Number ( '-2500' ) * Multiplier ( 'strategy_id' ) )
OR ( Time ( 'NSE' ) >= Number ( '1510' ) )
```

---

## ADVANCED SETTINGS:
- Price Execution: Market Price
- Execution Timeout: 60 Seconds
- Exit At Market Price: YES
- Exit Shorts First: YES
- Check Conditions Every: Continuously
- Reactivate on exit after: Never
- Capital Required: ₹1,80,000
- Strategy Visibility: Private
