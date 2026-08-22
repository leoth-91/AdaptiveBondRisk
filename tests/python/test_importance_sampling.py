import pytest

from importance_sampling import log_importance_weights, normalize_weights


def test_identical_base_and_proposal_give_zero_log_weights() -> None:
    mean = [0.0, 0.0]
    covariance = [1.0, 0.2, 0.2, 1.0]
    shocks = [[0.1, -0.2], [1.5, 0.3], [-0.4, -0.9]]

    log_weights = log_importance_weights(shocks, mean, covariance, mean, covariance)

    assert log_weights == [0.0, 0.0, 0.0]


def test_normalize_weights_of_equal_log_weights_is_uniform() -> None:
    weights = normalize_weights([0.0, 0.0, 0.0, 0.0])

    assert weights == pytest.approx([0.25, 0.25, 0.25, 0.25])
    assert sum(weights) == pytest.approx(1.0)


def test_normalize_weights_sums_to_one_and_favors_larger_log_weights() -> None:
    weights = normalize_weights([-1.0, 0.0, 2.0])

    assert sum(weights) == pytest.approx(1.0)
    assert weights[2] > weights[1] > weights[0]


def test_a_mean_shifted_proposal_downweights_shocks_far_from_the_base_mean() -> None:
    mean_p = [0.0]
    mean_q = [1.0]
    covariance = [1.0]
    shocks = [[0.0], [1.0], [2.0]]

    log_weights = log_importance_weights(shocks, mean_p, covariance, mean_q, covariance)

    # Shocks near mean_q (where the proposal draws from) get downweighted
    # relative to the base density, since they are more likely under q than
    # under p; log-weights should therefore decrease as shocks approach
    # mean_q from mean_p's side and then move past it.
    assert log_weights[0] > log_weights[1] > log_weights[2]
