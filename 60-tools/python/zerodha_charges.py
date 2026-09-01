# =============================================================================
# File: 60-tools/python/zerodha_charges.py
# Runtime: C:\kite-agent\.venv\Scripts\python.exe  (Python 3.14.7)
#
# ZERODHA-EXACT statutory charge calculator.
# Reconciled to the paisa against 5 zerodha.com/brokerage-calculator panels
# captured by the operator on 2026-09-01.
#
# ALGORITHM (empirically derived, NOT assumed):
#   Each component is rounded FIRST, then the rounded parts are summed.
#     STT          -> nearest whole rupee   (23.91->24, 8.4->8, 7.6->8)
#     Stamp duty   -> nearest whole rupee   (0.3534->0, 12.0->12)
#     Brokerage / exch / SEBI / GST -> 2 dp
#   GST = 18% of (brokerage + exch + SEBI), computed on UNROUNDED inputs.
#
# SUPERSEDES the round-once-at-total design in cost_engine.py, which was
# wrong and produced a permanent ~Rs0.28 mismatch per 4-leg cycle.
# =============================================================================
from decimal import Decimal, ROUND_HALF_UP, getcontext
from pathlib import Path
import datetime

getcontext().prec = 34
P2 = Decimal("0.01")
R1 = Decimal("1")

D = lambda v: Decimal(str(v))

CONFIG_PATH = Path(__file__).resolve().parents[2] / "70-ops/config/cost-config.yaml"

def _load_config(path):
    """Load this deliberately small config subset without a runtime dependency."""
    result = {}
    stack = [(-1, result)]
    for raw in path.read_text(encoding="utf-8-sig").splitlines():
        if not raw.strip() or raw.lstrip().startswith("#"):
            continue
        body = raw.split(" #", 1)[0].rstrip()
        indent = len(body) - len(body.lstrip(" "))
        key, sep, value = body.strip().partition(":")
        if not sep:
            continue
        while stack[-1][0] >= indent:
            stack.pop()
        parent = stack[-1][1]
        value = value.strip()
        if value == "":
            parent[key] = {}; stack.append((indent, parent[key])); continue
        if value == "null": parsed = None
        elif value.startswith('"') and value.endswith('"'): parsed = value[1:-1]
        else: parsed = value
        parent[key] = parsed
    return result

CFG = _load_config(CONFIG_PATH)

def _required(*keys):
    value = CFG
    for key in keys:
        value = value[key]
    if value is None:
        raise RuntimeError("CONFIG_UNSET: " + ".".join(keys))
    return value

def _rate(*keys):
    return D(_required("rates", *keys))

def _p(x): return D(x).quantize(P2, rounding=ROUND_HALF_UP)
def _r1(x): return D(x).quantize(R1, rounding=ROUND_HALF_UP)

STT_REGIME_CHANGE = datetime.date.fromisoformat(_required("regime", "stt_change_date"))
SEBI_RATE = _rate("sebi_rate")
GST_RATE = _rate("gst_rate")
SEGMENTS = {
    "options": {
        "brokerage": _required("rates", "options", "brokerage_mode"),
        "brokerage_per_order": _rate("options", "brokerage_per_order"),
        "stt_basis": _required("rates", "options", "stt_basis"),
        "stt_post": _rate("options", "stt_post"), "stt_pre": _rate("options", "stt_pre"),
        "exch": {"NSE": _rate("options", "exch_nse"), "BSE": _rate("options", "exch_bse")},
        "stamp": _rate("options", "stamp"),
    },
    "futures": {
        "brokerage": _required("rates", "futures", "brokerage_mode"),
        "brokerage_rate": _rate("futures", "brokerage_rate"), "brokerage_cap": _rate("futures", "brokerage_cap_per_order"),
        "stt_basis": _required("rates", "futures", "stt_basis"),
        "stt_post": _rate("futures", "stt_post"), "stt_pre": _rate("futures", "stt_pre"),
        "exch": {"NSE": _rate("futures", "exch_nse"), "BSE": _rate("futures", "exch_bse")},
        "stamp": _rate("futures", "stamp"),
    },
    "intraday_equity": {
        "brokerage": _required("rates", "intraday_equity", "brokerage_mode"),
        "brokerage_rate": _rate("intraday_equity", "brokerage_rate"), "brokerage_cap": _rate("intraday_equity", "brokerage_cap_per_order"),
        "stt_basis": _required("rates", "intraday_equity", "stt_basis"),
        "stt_post": _rate("intraday_equity", "stt_post"), "stt_pre": _rate("intraday_equity", "stt_pre"),
        "exch": {"NSE": _rate("intraday_equity", "exch_nse"), "BSE": _rate("intraday_equity", "exch_bse")},
        "stamp": _rate("intraday_equity", "stamp"),
    },
    "delivery_equity": {
        "brokerage": _required("rates", "delivery_equity", "brokerage_mode"),
        "stt_basis": _required("rates", "delivery_equity", "stt_basis"),
        "stt_post": _rate("delivery_equity", "stt_post"), "stt_pre": _rate("delivery_equity", "stt_pre"),
        "exch": {"NSE": _rate("delivery_equity", "exch_nse"), "BSE": _rate("delivery_equity", "exch_bse")},
        "stamp": _rate("delivery_equity", "stamp"),
    },
}
STT_EXERCISE_POST = D(_required("stt_exercise", "post"))
STT_EXERCISE_PRE = D(_required("stt_exercise", "pre"))
SLIPPAGE_PCT = CFG.get("slippage_pct")

def _p2(x): return D(x).quantize(P2, rounding=ROUND_HALF_UP)
def _r1(x): return D(x).quantize(R1, rounding=ROUND_HALF_UP)


def charges_from_turnover(
    segment,
    exchange,
    buy_turnover,
    sell_turnover,
    num_executed_orders=2,
    trade_date="2026-09-01",
    num_expiry_settled_legs=0,
    exercised_intrinsic_value=None,
    charge_brokerage_on_expiry_legs=True,
):
    """Fails closed. One contract note = one call."""
    seg = str(segment).strip().lower()
    if seg not in SEGMENTS:
        raise ValueError("Unknown segment %r - expected one of %s"
                         % (segment, sorted(SEGMENTS)))
    S = SEGMENTS[seg]

    exch = str(exchange).strip().upper()
    if exch not in ("NSE", "BSE"):
        raise ValueError("Unsupported exchange %r - expected NSE or BSE" % exchange)

    if isinstance(trade_date, str):
        trade_date = datetime.date.fromisoformat(trade_date)
    if not isinstance(trade_date, datetime.date):
        raise TypeError("trade_date must be datetime.date or ISO-8601 string")

    buy_t, sell_t = D(buy_turnover), D(sell_turnover)
    if buy_t < 0 or sell_t < 0:
        raise ValueError("turnover cannot be negative")
    total_t = buy_t + sell_t

    n_orders = int(num_executed_orders)
    if n_orders < 0:
        raise ValueError("num_executed_orders cannot be negative")
    if total_t == 0 and n_orders == 0:
        raise ValueError("FIXTURE_IS_EMPTY: zero turnover and zero orders is "
                         "not a testable case")

    post = trade_date >= STT_REGIME_CHANGE

    # --- brokerage ---------------------------------------------------------
    billable = n_orders
    if charge_brokerage_on_expiry_legs:
        billable += int(num_expiry_settled_legs)

    if S["brokerage"] == "zero":
        brokerage_raw = D(0)
    elif S["brokerage"] == "flat20":
        brokerage_raw = D(billable) * S["brokerage_per_order"]
    else:  # pct_capped: 0.03% or Rs20 per executed order, whichever is lower
        # [O] assumes exactly one buy order and one sell order
        if billable != 2:
            raise ValueError("pct_capped brokerage currently modelled only for "
                             "the 2-order (1 buy + 1 sell) case; got %d" % billable)
        brokerage_raw = (min(buy_t * S["brokerage_rate"], S["brokerage_cap"])
                         + min(sell_t * S["brokerage_rate"], S["brokerage_cap"]))
    brokerage = _p2(brokerage_raw)

    # --- STT (rounded to whole rupee) --------------------------------------
    rate = S["stt_post"] if post else S["stt_pre"]
    base = total_t if S["stt_basis"] == "both" else sell_t
    stt_premium_raw = base * rate

    ex_rate = STT_EXERCISE_POST if post else STT_EXERCISE_PRE
    if exercised_intrinsic_value is None:
        stt_exercise_raw = D(0)
    else:
        iv = D(exercised_intrinsic_value)
        if iv < 0:
            raise ValueError("exercised_intrinsic_value cannot be negative")
        stt_exercise_raw = iv * ex_rate
    stt = _r1(stt_premium_raw + stt_exercise_raw)

    # --- exchange, SEBI, stamp, GST ---------------------------------------
    exch_raw  = total_t * S["exch"][exch]
    sebi_raw  = total_t * SEBI_RATE
    stamp_raw = buy_t * S["stamp"]
    gst_raw   = (brokerage_raw + exch_raw + sebi_raw) * GST_RATE

    exchange_fee = _p2(exch_raw)
    sebi_fee     = _p2(sebi_raw)
    stamp_duty   = _r1(stamp_raw)
    gst          = _p2(gst_raw)

    total = brokerage + stt + exchange_fee + sebi_fee + stamp_duty + gst
    gross = sell_t - buy_t

    return {
        "segment": seg, "exchange": exch,
        "trade_date": trade_date.isoformat(),
        "stt_regime": "post-2026-04-01" if post else "pre-2026-04-01",
        "billable_orders": billable,
        "buy_turnover": str(buy_t), "sell_turnover": str(sell_t),
        "total_turnover": str(total_t),
        "brokerage": str(brokerage), "stt": str(stt),
        "exchange_fee": str(exchange_fee), "sebi_fee": str(sebi_fee),
        "stamp_duty": str(stamp_duty), "gst": str(gst),
        "stt_unrounded": str(stt_premium_raw + stt_exercise_raw),
        "stamp_unrounded": str(stamp_raw),
        "slippage_pct": SLIPPAGE_PCT,
        "net_pnl_is_upper_bound": SLIPPAGE_PCT is None,
        "total_charges": str(_p2(total)),
        "gross_pnl": str(_p2(gross)),
        "net_pnl": str(_p2(gross - total)),
    }


def charges_from_prices(segment, exchange, buy_price, sell_price, quantity,
                        num_executed_orders=2, trade_date="2026-09-01"):
    """Mirrors the 4 inputs the Zerodha calculator UI accepts.
    quantity = position size on ONE side (a SENSEX lot is 20, NOT 40)."""
    q = D(quantity)
    return charges_from_turnover(segment, exchange, D(buy_price) * q,
                                 D(sell_price) * q, num_executed_orders,
                                 trade_date)


def _line(r):
    print("  turnover %-10s brokerage %-8s STT %-6s exch %-8s SEBI %-6s "
          "stamp %-4s GST %-8s TOTAL %s"
          % (r["total_turnover"], r["brokerage"], r["stt"], r["exchange_fee"],
             r["sebi_fee"], r["stamp_duty"], r["gst"], r["total_charges"]))


PANELS = [
    ("P1 options NSE 589/797/20",  dict(segment="options", exchange="NSE",
        buy_price=589, sell_price=797, quantity=20), "82.86"),
    ("P2 options BSE 476/280/20",  dict(segment="options", exchange="BSE",
        buy_price=476, sell_price=280, quantity=20), "61.02"),
    ("P3 intraday NSE 1000/1100/400", dict(segment="intraday_equity",
        exchange="NSE", buy_price=1000, sell_price=1100, quantity=400), "200.62"),
    ("P4 delivery BSE 1000/1100/400", dict(segment="delivery_equity",
        exchange="BSE", buy_price=1000, sell_price=1100, quantity=400), "938.16"),
    ("P5 futures BSE 500/760/20",  dict(segment="futures", exchange="BSE",
        buy_price=500, sell_price=760, quantity=20), "16.96"),
]


def main():
    print()
    print("=" * 78)
    print("GATE G2 - RECONCILIATION vs zerodha.com/brokerage-calculator panels")
    print("=" * 78)
    failed = 0
    for label, kw, expected in PANELS:
        r = charges_from_prices(**kw)
        got = r["total_charges"]
        ok = (got == expected)
        failed += (not ok)
        print("%s %-32s expected %-8s got %-8s" %
              ("PASS" if ok else "FAIL", label, expected, got))
        _line(r)
    print()
    print("G2 VERDICT:", "PASS - 5/5 panels reconcile exactly" if failed == 0
          else "FAIL - %d panel(s) mismatched" % failed)
    print()

    print("=" * 78)
    print("PREDICTION (NOT YET VERIFIED) - Trade leg A priced on the CORRECT")
    print("exchange. Operator screenshot used NSE; SENSEX trades on BSE.")
    print("=" * 78)
    p = charges_from_prices(segment="options", exchange="BSE",
                            buy_price=589, sell_price=797, quantity=20)
    print("  BSE total = %s   (NSE screenshot showed 82.86)" % p["total_charges"])
    print("  CONFIRM THIS IN THE CALCULATOR WITH THE BSE RADIO SELECTED.")
    print()

    print("=" * 78)
    print("LIVE TRADE AUDIT - 2026-09-01 SENSEX 03SEP2026 BEAR PUT SPREAD")
    print("=" * 78)
    print("  Leg A LONG  77700 PE: buy  20 @ 589.75 = 11795 | sell 20 @ 797.65 = 15953")
    print("  Leg B SHORT 77200 PE: sell 20 @ 280.80 =  5616 | buy  20 @ 476.75 =  9535")
    print("  ONE strategy, 2 legs, 4 executed orders, ONE BSE contract note.")
    print()
    r = charges_from_turnover(
        segment="options", exchange="BSE",
        buy_turnover=D("11795") + D("9535"),
        sell_turnover=D("15953") + D("5616"),
        num_executed_orders=4, trade_date="2026-09-01",
    )
    for k in ("buy_turnover", "sell_turnover", "total_turnover", "gross_pnl",
              "brokerage", "stt", "exchange_fee", "sebi_fee", "stamp_duty",
              "gst", "total_charges", "net_pnl"):
        print("  %-16s : %s" % (k, r[k]))
    friction_pct = (D(r["total_charges"]) / D(r["gross_pnl"]) * 100)
    print("  %-16s : %s%%" % ("friction/gross", _p2(friction_pct)))
    print("  slippage_pct    : %s (UNMEASURED; net is an upper bound)" % SLIPPAGE_PCT)
    print()
    print("  [O] stamp duty raw = %s -> rounded to %s. If Zerodha TRUNCATES"
          % (r["stamp_unrounded"], r["stamp_duty"]))
    print("      rather than rounds, total is Rs1 lower. All observed panels")
    print("      had stamp < 0.50 so the two rules are indistinguishable.")
    print("  [O] Assumes ONE contract note. Two notes would round STT/stamp twice.")
    print()

    print("=" * 78)
    print("NEGATIVE TESTS (all must raise)")
    print("=" * 78)
    cases = [
        ("bad segment",    dict(segment="crypto", exchange="BSE",
                                buy_turnover=1, sell_turnover=1)),
        ("bad exchange",   dict(segment="options", exchange="MCX",
                                buy_turnover=1, sell_turnover=1)),
        ("empty fixture",  dict(segment="options", exchange="BSE",
                                buy_turnover=0, sell_turnover=0,
                                num_executed_orders=0)),
        ("negative t/o",   dict(segment="options", exchange="BSE",
                                buy_turnover=-1, sell_turnover=1)),
        ("bad date type",  dict(segment="options", exchange="BSE",
                                buy_turnover=1, sell_turnover=1,
                                trade_date=20260901)),
        ("neg intrinsic",  dict(segment="options", exchange="BSE",
                                buy_turnover=1, sell_turnover=1,
                                exercised_intrinsic_value=-5)),
        ("4-leg futures",  dict(segment="futures", exchange="BSE",
                                buy_turnover=1, sell_turnover=1,
                                num_executed_orders=4)),
    ]
    for name, kw in cases:
        try:
            charges_from_turnover(**kw)
            print("  FAIL - %-15s did NOT raise" % name)
        except (ValueError, TypeError) as e:
            print("  OK   - %-15s %s" % (name, type(e).__name__))
    print()


if __name__ == "__main__":
    main()
