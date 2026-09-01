# [SUPERSEDED 2026-09-01 by 60-tools/python/zerodha_charges.py]
# Rounding model was WRONG (round-once-at-total). See ledger V17.
# Retained for the exercise-STT / expiry-leg logic ONLY. Do not cite
# its totals.
# =============================================================================
# File: 60-tools/python/cost_engine.py
# Runtime: C:\kite-agent\.venv\Scripts\python.exe   (Python 3.14.7)
# Purpose: Statutory F&O friction calculator. CALCULATION ONLY. No policy gates.
#
# All rates verified 2026-09-01 against https://zerodha.com/charges/
# STT regime change verified against Budget 2026 (effective 2026-04-01).
#
# REJECTED BY DESIGN: repo's hidden min_net=150 and Gemini's hidden 200/cycle
# gate. A verdict threshold is operator policy and lives in
# 70-ops/policies/verdict-policy.yaml, never in a calculator.
# =============================================================================
from decimal import Decimal, ROUND_HALF_UP, getcontext
import datetime

getcontext().prec = 34
P2 = Decimal("0.01")

STT_REGIME_CHANGE = datetime.date(2026, 4, 1)

# --- Rate constants, each with its verified source -------------------------
BROKERAGE_PER_ORDER   = Decimal("20.00")        # [V] flat Rs20/executed order, options
STT_PREMIUM_PRE       = Decimal("0.0010")       # [V] 0.10% sale premium, to 2026-03-31
STT_PREMIUM_POST      = Decimal("0.0015")       # [V] 0.15% sale premium, from 2026-04-01
STT_EXERCISE_PRE      = Decimal("0.00125")      # [V] 0.125% intrinsic, to 2026-03-31
STT_EXERCISE_POST     = Decimal("0.0015")       # [V] 0.15% intrinsic, from 2026-04-01
TXN_NSE               = Decimal("0.0003553")    # [V] 0.03553% on premium
TXN_BSE               = Decimal("0.000325")     # [V] 0.0325%  on premium
SEBI_FEE              = Decimal("0.000001")     # [V] Rs10 per crore
IPFT_NSE              = Decimal("0.000000001")  # [V] Rs0.01 per crore of premium
IPFT_BSE              = Decimal("0")            # [V] no separate BSE IPFT line
STAMP_DUTY_BUY        = Decimal("0.00003")      # [V] 0.003% / Rs300 per crore, buy side
GST_RATE              = Decimal("0.18")         # [V] 18% on brokerage+SEBI+txn charges


def compute_fo_statutory_friction(
    trade_date,
    exchange,
    buy_premium_turnover,
    sell_premium_turnover,
    num_executed_orders,
    num_expiry_settled_legs=0,
    exercised_intrinsic_value=None,
    charge_brokerage_on_expiry_legs=True,
):
    """
    Pure calculator. Fails closed. No defaults that hide a decision.

    exercised_intrinsic_value: Decimal or None.
        MUST be supplied if any leg is exercised. Exercise STT is levied on
        INTRINSIC VALUE, not on premium. Passing None means "nothing exercised".

    charge_brokerage_on_expiry_legs: default True (conservative).
        [O - CONTRADICTION] zerodha.com/charges disclaimer states verbatim:
        "Brokerage is also charged on expired, exercised, and assigned options
        contracts." But the Zerodha support FAQ states brokerage is NOT charged
        when an option expires worthless. Unresolved. Default to the expensive
        reading. Resolve with a real expired contract note from Console.
    """
    if exchange is None:
        raise ValueError("exchange is required - no silent default permitted")
    exch = str(exchange).strip().upper()
    if exch not in ("NSE", "BSE"):
        raise ValueError("Unsupported exchange %r - expected NSE or BSE" % exchange)

    if isinstance(trade_date, str):
        trade_date = datetime.date.fromisoformat(trade_date)
    if not isinstance(trade_date, datetime.date):
        raise TypeError("trade_date must be datetime.date or ISO-8601 string")

    buy_t  = Decimal(str(buy_premium_turnover))
    sell_t = Decimal(str(sell_premium_turnover))
    if buy_t < 0 or sell_t < 0:
        raise ValueError("turnover cannot be negative")
    total_t = buy_t + sell_t

    if total_t == 0 and num_executed_orders == 0:
        raise ValueError("FIXTURE_IS_EMPTY: zero turnover and zero orders is not "
                         "a testable case - supply real premiums from a backtest row")

    post = trade_date >= STT_REGIME_CHANGE

    # 1. Brokerage
    billable_orders = int(num_executed_orders)
    if charge_brokerage_on_expiry_legs:
        billable_orders += int(num_expiry_settled_legs)
    brokerage = Decimal(billable_orders) * BROKERAGE_PER_ORDER

    # 2. STT - two independent bases, never conflated
    stt_premium_rate = STT_PREMIUM_POST if post else STT_PREMIUM_PRE
    stt_premium = sell_t * stt_premium_rate

    stt_exercise_rate = STT_EXERCISE_POST if post else STT_EXERCISE_PRE
    if exercised_intrinsic_value is None:
        stt_exercise = Decimal("0")
    else:
        iv = Decimal(str(exercised_intrinsic_value))
        if iv < 0:
            raise ValueError("exercised_intrinsic_value cannot be negative")
        stt_exercise = iv * stt_exercise_rate
    stt = stt_premium + stt_exercise

    # 3. Exchange transaction charge + IPFT, on total premium turnover
    if exch == "NSE":
        exchange_fee = total_t * TXN_NSE
        ipft = total_t * IPFT_NSE
    else:
        exchange_fee = total_t * TXN_BSE
        ipft = total_t * IPFT_BSE

    # 4. SEBI turnover fee
    sebi_fee = total_t * SEBI_FEE

    # 5. Stamp duty - buy side only
    stamp_duty = buy_t * STAMP_DUTY_BUY

    # 6. GST - 18% on brokerage + SEBI + transaction charges (IPFT is reported
    #    inside exchange transaction charges on the NSE contract note).
    gst = (brokerage + exchange_fee + sebi_fee + ipft) * GST_RATE

    # 7. Round ONCE, at the total. Component rounding destroys sub-paise items
    #    (IPFT, SEBI) and prevents reconciliation against a real contract note.
    exact_total = brokerage + stt + exchange_fee + sebi_fee + stamp_duty + gst + ipft
    total = exact_total.quantize(P2, rounding=ROUND_HALF_UP)

    return {
        "trade_date": trade_date.isoformat(),
        "exchange": exch,
        "stt_regime": "post-2026-04-01" if post else "pre-2026-04-01",
        "billable_orders": billable_orders,
        "buy_premium_turnover": str(buy_t),
        "sell_premium_turnover": str(sell_t),
        "total_premium_turnover": str(total_t),
        "exercised_intrinsic_value": None if exercised_intrinsic_value is None
                                     else str(Decimal(str(exercised_intrinsic_value))),
        "components_exact": {
            "brokerage":     str(brokerage),
            "stt_premium":   str(stt_premium),
            "stt_exercise":  str(stt_exercise),
            "exchange_fee":  str(exchange_fee),
            "sebi_fee":      str(sebi_fee),
            "stamp_duty":    str(stamp_duty),
            "ipft":          str(ipft),
            "gst":           str(gst),
        },
        "rates_applied": {
            "stt_premium_rate":  str(stt_premium_rate),
            "stt_exercise_rate": str(stt_exercise_rate),
            "txn_rate":          str(TXN_NSE if exch == "NSE" else TXN_BSE),
        },
        "total_friction_exact":   str(exact_total),
        "total_friction_rounded": str(total),
        "open_flags": [
            "[O-CONTRADICTION] brokerage on worthless-expiry legs: charges-page "
            "disclaimer says charged, support FAQ says not. Conservative default used.",
            "[O] stamp duty is state-dependent in law; Zerodha applies a flat "
            "0.003% buy-side. Not independently verified against a contract note.",
            "[O] IPFT: Zerodha states Rs0.01/crore; other brokers publish Rs50/crore "
            "for equity options. Immaterial either way. Zerodha figure used.",
            "[U] NOT EXTERNALLY ANCHORED. No output of this module may be called "
            "'golden' until reconciled to +/-Rs0.05 against zerodha.com/brokerage-calculator.",
        ],
    }


def _show(label, res):
    print("=" * 78)
    print(label)
    print("=" * 78)
    print("  regime         :", res["stt_regime"])
    print("  exchange       :", res["exchange"])
    print("  billable orders:", res["billable_orders"])
    print("  turnover buy   :", res["buy_premium_turnover"])
    print("  turnover sell  :", res["sell_premium_turnover"])
    for k, v in res["components_exact"].items():
        print("  %-14s : %s" % (k, v))
    print("  TOTAL (exact)  :", res["total_friction_exact"])
    print("  TOTAL (rounded):", res["total_friction_rounded"])
    print()


def run_fixtures():
    print()
    print("### These are UNIT-TEST FIXTURES, not golden values. ###")
    print("### Anchor against zerodha.com/brokerage-calculator before citing. ###")
    print()

    # Fixture B - Gemini's 2-leg BSE spread, pre-April regime. Real numbers.
    _show(
        "FIXTURE B - SENSEX 2-leg bull call spread, pre-2026-04-01, 4 orders",
        compute_fo_statutory_friction(
            trade_date="2026-03-16",
            exchange="BSE",
            buy_premium_turnover=Decimal("9600"),
            sell_premium_turnover=Decimal("11400"),
            num_executed_orders=4,
        ),
    )

    # Fixture C - SENSEX 4-leg iron fly, post-April, squared off (8 orders).
    # Lot 20. Sell 79000CE @ 210, 79000PE @ 205; buy 79600CE @ 90, 78400PE @ 85.
    # Entry: sell turnover 20*(210+205) = 8300 ; buy turnover 20*(90+85) = 3500
    # Exit assumed at half value: sell-side buyback 20*(105+102) = 4140 (a BUY)
    #                             long-leg sale     20*(45+42)  = 1740 (a SELL)
    _show(
        "FIXTURE C - SENSEX 4-leg iron fly, post-2026-04-01, squared off, 8 orders",
        compute_fo_statutory_friction(
            trade_date="2026-04-16",
            exchange="BSE",
            buy_premium_turnover=Decimal("3500") + Decimal("4140"),
            sell_premium_turnover=Decimal("8300") + Decimal("1740"),
            num_executed_orders=8,
        ),
    )

    # Fixture D - same iron fly HELD TO EXPIRY, short call finishes 120 pts ITM.
    # 4 entry orders + 4 expiry-settled legs. Intrinsic = 20 * 120 = 2400.
    _show(
        "FIXTURE D - SENSEX 4-leg iron fly held to expiry, short CE 120pts ITM",
        compute_fo_statutory_friction(
            trade_date="2026-04-16",
            exchange="BSE",
            buy_premium_turnover=Decimal("3500"),
            sell_premium_turnover=Decimal("8300"),
            num_executed_orders=4,
            num_expiry_settled_legs=4,
            exercised_intrinsic_value=Decimal("2400"),
        ),
    )

    # Fixture E - NIFTY equivalent on NSE, post-April, to exercise the NSE branch
    # incl. IPFT. Lot 65.
    _show(
        "FIXTURE E - NIFTY 4-leg iron fly, NSE, post-2026-04-01, squared off",
        compute_fo_statutory_friction(
            trade_date="2026-04-14",
            exchange="NSE",
            buy_premium_turnover=Decimal("65") * Decimal("175"),
            sell_premium_turnover=Decimal("65") * Decimal("415"),
            num_executed_orders=8,
        ),
    )

    # Negative tests - MUST raise. A calculator that cannot fail is not a test.
    print("=" * 78)
    print("NEGATIVE TESTS (all four MUST raise)")
    print("=" * 78)
    cases = [
        ("unknown exchange", dict(trade_date="2026-04-16", exchange="MCX",
                                  buy_premium_turnover=1, sell_premium_turnover=1,
                                  num_executed_orders=2)),
        ("empty fixture",    dict(trade_date="2026-04-16", exchange="BSE",
                                  buy_premium_turnover=0, sell_premium_turnover=0,
                                  num_executed_orders=0)),
        ("negative turnover",dict(trade_date="2026-04-16", exchange="BSE",
                                  buy_premium_turnover=-1, sell_premium_turnover=1,
                                  num_executed_orders=2)),
        ("bad date type",    dict(trade_date=20260416, exchange="BSE",
                                  buy_premium_turnover=1, sell_premium_turnover=1,
                                  num_executed_orders=2)),
    ]
    for name, kw in cases:
        try:
            compute_fo_statutory_friction(**kw)
            print("  FAIL - %-18s did NOT raise" % name)
        except (ValueError, TypeError) as e:
            print("  OK   - %-18s raised %s: %s" % (name, type(e).__name__, e))
    print()


if __name__ == "__main__":
    run_fixtures()

