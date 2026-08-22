import math

import pytest

from gaussian_distribution import GaussianDistribution


def test_standard_normal_log_density_matches_closed_form() -> None:
    standard_normal = GaussianDistribution(mean=[0.0], covariance=[1.0])

    assert standard_normal.log_density([0.0]) == pytest.approx(
        -0.5 * math.log(2.0 * math.pi)
    )
    assert standard_normal.log_density([1.0]) == pytest.approx(
        -0.5 * math.log(2.0 * math.pi) - 0.5
    )


def test_independent_dimensions_factor_into_a_sum_of_marginals() -> None:
    joint = GaussianDistribution(mean=[0.0, 0.0], covariance=[1.0, 0.0, 0.0, 4.0])
    marginal_x = GaussianDistribution(mean=[0.0], covariance=[1.0])
    marginal_y = GaussianDistribution(mean=[0.0], covariance=[4.0])

    point = [1.5, -2.0]
    assert joint.log_density(point) == pytest.approx(
        marginal_x.log_density([point[0]]) + marginal_y.log_density([point[1]])
    )


def test_density_is_maximized_at_the_mean() -> None:
    distribution = GaussianDistribution(mean=[1.0, -1.0], covariance=[2.0, 0.5, 0.5, 1.0])

    at_mean = distribution.log_density([1.0, -1.0])
    for offset in ([0.5, 0.0], [-0.3, 0.7], [0.0, 2.0]):
        shifted = [1.0 + offset[0], -1.0 + offset[1]]
        assert distribution.log_density(shifted) < at_mean


def test_empty_distribution_is_rejected() -> None:
    with pytest.raises(ValueError, match="empty"):
        GaussianDistribution(mean=[], covariance=[])


def test_mismatched_covariance_size_is_rejected() -> None:
    with pytest.raises(ValueError, match="covariance"):
        GaussianDistribution(mean=[0.0, 0.0], covariance=[1.0])


def test_non_positive_definite_covariance_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive definite"):
        GaussianDistribution(mean=[0.0, 0.0], covariance=[1.0, 2.0, 2.0, 1.0])
