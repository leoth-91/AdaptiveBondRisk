import pytest

from financial_metrics import expected_shortfall, value_at_risk


def test_value_at_risk_selects_the_correct_order_statistic() -> None:
    losses = [float(i) for i in range(1, 101)]

    assert value_at_risk(losses, alpha=0.95) == 95.0
    assert value_at_risk(losses, alpha=1.0) == 100.0


def test_expected_shortfall_averages_the_tail_beyond_var() -> None:
    losses = [float(i) for i in range(1, 101)]

    assert expected_shortfall(losses, alpha=0.95) == pytest.approx(97.5)
    assert expected_shortfall(losses, alpha=1.0) == 100.0


def test_expected_shortfall_is_at_least_value_at_risk() -> None:
    losses = [float(i) for i in range(1, 101)]

    for alpha in (0.5, 0.9, 0.95, 0.99):
        assert expected_shortfall(losses, alpha) >= value_at_risk(losses, alpha)
