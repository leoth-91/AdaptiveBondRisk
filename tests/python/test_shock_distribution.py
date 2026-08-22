import pytest

from models import YieldCurvePoint
from shock_distribution import build_shock_distribution


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
