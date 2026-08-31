from decimal import Decimal
from cost_model import Leg, compute_costs, gross_pnl, net_verdict

def test_nifty_2leg():
    legs = [Leg("SELL", 100, 70, 65), Leg("BUY", 60, 40, 65)]
    c = compute_costs(legs, "NSE")
    assert c["orders"] == 4
    assert c["brokerage"] == Decimal("80.00")
    assert c["sell_turnover"] == Decimal("9100.00")
    assert c["buy_turnover"] == Decimal("8450.00")
    assert c["stt"] == Decimal("13.65")
    print("NIFTY 2-leg total:", c["total_cost"])
    assert Decimal("110") < c["total_cost"] < Decimal("120")

def test_gross_and_verdict():
    legs = [Leg("SELL", 100, 70, 65), Leg("BUY", 60, 40, 65)]
    assert gross_pnl(legs) == Decimal("650.00")   # +1950 -1300
    v = net_verdict(legs, "NSE")
    print("verdict:", v["verdict"], "net:", v["net"])

def test_bse_cheaper_txn():
    legs = [Leg("SELL", 100, 70, 20), Leg("BUY", 60, 40, 20)]
    assert compute_costs(legs, "BSE")["txn_charge"] < compute_costs(legs, "NSE")["txn_charge"]

def test_validation():
    for bad in (lambda: Leg("HOLD", 1, 1, 1), lambda: Leg("BUY", 1, 1, 0)):
        try: bad(); raise AssertionError("should have raised")
        except ValueError: pass
    try: compute_costs([Leg("BUY",1,1,1)], "MCX"); raise AssertionError("should have raised")
    except ValueError: pass

if __name__ == "__main__":
    test_nifty_2leg(); test_gross_and_verdict()
    test_bse_cheaper_txn(); test_validation()
    print("ALL TESTS PASSED")