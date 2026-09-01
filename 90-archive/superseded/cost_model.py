# SUPERSEDED 2026-09-01: rejected legacy cost model; use 60-tools/python/zerodha_charges.py.
"""Zerodha F&O options cost model. Rates verified 31-Aug-2026 from zerodha.com/charges.
DO NOT edit rates without updating RATE_SOURCE_DATE and 00_CORRECTIONS_LEDGER.md."""
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP

RATE_SOURCE = "https://zerodha.com/charges/"
RATE_SOURCE_DATE = "2026-08-31"

BROKERAGE_PER_ORDER = Decimal("20")
BROKERAGE_DEBIT_BALANCE = Decimal("40")
STT_SELL_PREMIUM = Decimal("0.0015")
SEBI_RATE = Decimal("0.000001")
STAMP_BUY_RATE = Decimal("0.00003")
GST_RATE = Decimal("0.18")
TXN_RATE = {"NSE": Decimal("0.0003553"), "BSE": Decimal("0.000325")}

def _p(x): return Decimal(str(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

@dataclass
class Leg:
    side: str          # "SELL" or "BUY" at ENTRY
    entry_price: float
    exit_price: float
    qty: int
    def __post_init__(self):
        if self.side not in ("SELL", "BUY"):
            raise ValueError(f"side must be SELL or BUY, got {self.side!r}")
        if self.qty <= 0:
            raise ValueError("qty must be positive")

def compute_costs(legs, exchange="NSE", debit_balance=False):
    if exchange not in TXN_RATE:
        raise ValueError(f"exchange must be NSE or BSE, got {exchange!r}")
    if not legs:
        raise ValueError("at least one leg required")

    buy_turnover = sell_turnover = Decimal("0")
    for lg in legs:
        e = Decimal(str(lg.entry_price)) * lg.qty
        x = Decimal(str(lg.exit_price)) * lg.qty
        if lg.side == "SELL":
            sell_turnover += e; buy_turnover += x
        else:
            buy_turnover += e; sell_turnover += x
    total_turnover = buy_turnover + sell_turnover

    n_orders = len(legs) * 2   # entry + exit per leg
    rate = BROKERAGE_DEBIT_BALANCE if debit_balance else BROKERAGE_PER_ORDER
    brokerage = rate * n_orders
    stt   = sell_turnover * STT_SELL_PREMIUM
    txn   = total_turnover * TXN_RATE[exchange]
    sebi  = total_turnover * SEBI_RATE
    stamp = buy_turnover * STAMP_BUY_RATE
    gst   = (brokerage + sebi + txn) * GST_RATE   # NOT on STT or stamp

    total = brokerage + stt + txn + sebi + stamp + gst
    return {
        "orders": n_orders, "exchange": exchange,
        "buy_turnover": _p(buy_turnover), "sell_turnover": _p(sell_turnover),
        "brokerage": _p(brokerage), "stt": _p(stt), "txn_charge": _p(txn),
        "sebi": _p(sebi), "stamp_duty": _p(stamp), "gst": _p(gst),
        "total_cost": _p(total),
        "rate_source_date": RATE_SOURCE_DATE,
    }

def gross_pnl(legs):
    t = Decimal("0")
    for lg in legs:
        d = Decimal(str(lg.entry_price)) - Decimal(str(lg.exit_price))
        t += (d if lg.side == "SELL" else -d) * lg.qty
    return _p(t)

def net_verdict(legs, exchange="NSE", min_net=Decimal("150")):
    c = compute_costs(legs, exchange)
    g = gross_pnl(legs)
    net = _p(g - c["total_cost"])
    return {"gross": g, "cost": c["total_cost"], "net": net,
            "verdict": "PASS" if net >= min_net else "REJECT",
            "min_net_required": min_net, "breakdown": c}