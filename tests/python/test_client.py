import argparse

import pytest

from abr_client import AdaptiveBondRiskClient
from models import YieldCurvePoint
from portfolio_loader import load_portfolio, load_yield_curve
from simulate_var import build_shock_distribution, positive_int, value_at_risk


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


def test_positive_int_accepts_scientific_notation() -> None:
    assert positive_int("1e6") == 1_000_000
    assert positive_int("100") == 100
    assert positive_int("2.5e2") == 250


def test_positive_int_rejects_non_positive_and_fractional_values() -> None:
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("0")
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("-1e6")
    with pytest.raises(argparse.ArgumentTypeError):
        positive_int("1.5")


def test_value_at_risk_selects_the_correct_order_statistic() -> None:
    losses = [float(i) for i in range(1, 101)]

    assert value_at_risk(losses, alpha=0.95) == 95.0
    assert value_at_risk(losses, alpha=1.0) == 100.0


def test_build_shock_distribution_has_zero_mean_and_symmetric_covariance() -> None:
    curve = [YieldCurvePoint(maturity=m, zero_rate=0.02) for m in (1.0, 2.0, 5.0)]

    mean, covariance = build_shock_distribution(
        curve, base_vol=0.01, vol_decay=0.05, corr_length=5.0
    )

    dimension = len(curve)
    assert mean == [0.0] * dimension
    assert len(covariance) == dimension * dimension

    def at(i: int, j: int) -> float:
        return covariance[i * dimension + j]

    for i in range(dimension):
        for j in range(dimension):
            assert at(i, j) == pytest.approx(at(j, i))
        assert at(i, i) > 0.0

    # Volatility decays with maturity and correlation decays with maturity
    # distance, so nearer/shorter maturities are more volatile and more
    # correlated with each other than with the far end of the curve.
    assert at(0, 0) > at(2, 2)
    assert at(0, 1) > at(0, 2)
