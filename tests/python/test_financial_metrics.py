import pytest

from financial_metrics import (
    expected_shortfall,
    expected_shortfall_weighted,
    value_at_risk,
    value_at_risk_weighted,
)


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


def test_weighted_metrics_match_unweighted_ones_under_uniform_weights() -> None:
    losses = [float(i) for i in range(1, 101)]
    weights = [1.0 / len(losses)] * len(losses)

    for alpha in (0.5, 0.9, 0.95, 0.99, 1.0):
        assert value_at_risk_weighted(losses, weights, alpha) == value_at_risk(
            losses, alpha
        )
        assert expected_shortfall_weighted(
            losses, weights, alpha
        ) == pytest.approx(expected_shortfall(losses, alpha))


def test_weighted_metrics_shift_toward_the_heavily_weighted_region() -> None:
    losses = [float(i) for i in range(1, 101)]
    # Concentrate all weight on the ten largest losses, evenly: cumulative
    # weight reaches 0.5 at the 6th of those ten (95.0), and the resulting
    # tail is the top six losses (95..100), averaging to 97.5.
    weights = [0.0] * 90 + [0.1] * 10

    assert value_at_risk_weighted(losses, weights, alpha=0.5) == 95.0
    assert expected_shortfall_weighted(
        losses, weights, alpha=0.5
    ) == pytest.approx(97.5)


def test_weighted_expected_shortfall_is_at_least_weighted_value_at_risk() -> None:
    losses = [float(i) for i in range(1, 101)]
    weights = [(i + 1) / 5050 for i in range(100)]  # sums to 1, increasing

    for alpha in (0.5, 0.9, 0.95, 0.99):
        assert expected_shortfall_weighted(
            losses, weights, alpha
        ) >= value_at_risk_weighted(losses, weights, alpha)
