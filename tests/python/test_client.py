import pytest

from abr_client import AdaptiveBondRiskClient
from portfolio_loader import load_portfolio, load_yield_curve


def test_empty_address_is_rejected() -> None:
    with pytest.raises(ValueError, match="address"):
        AdaptiveBondRiskClient("")


def test_negative_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="timeout"):
        AdaptiveBondRiskClient("tcp://127.0.0.1:5555", timeout_ms=-1)


def test_demo_files_can_be_loaded(tmp_path) -> None:
    portfolio_file = tmp_path / "portfolio.csv"
    portfolio_file.write_text(
        "id,face_value,coupon_rate,time_to_maturity,coupon_frequency,"
        "time_to_next_coupon,quantity\n"
        "TEST,1000,0.04,2.0,2,0.5,3\n",
        encoding="utf-8",
    )
    curve_file = tmp_path / "curve.csv"
    curve_file.write_text(
        "maturity,zero_rate\n0.5,0.02\n2.0,0.03\n",
        encoding="utf-8",
    )

    portfolio = load_portfolio(portfolio_file)
    curve = load_yield_curve(curve_file)

    assert portfolio[0].id == "TEST"
    assert portfolio[0].quantity == 3.0
    assert curve[1].zero_rate == 0.03
