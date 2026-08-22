import math

from gaussian_distribution import GaussianDistribution


def log_importance_weights(
    shocks: list[list[float]],
    mean_p: list[float],
    covariance_p: list[float],
    mean_q: list[float],
    covariance_q: list[float],
) -> list[float]:
    """log w(s) = log p(s) - log q(s) for a batch of shocks drawn from the
    importance distribution q, where p is the base (real-world) shock
    distribution the risk quantity is defined under.
    """
    base = GaussianDistribution(mean_p, covariance_p)
    proposal = GaussianDistribution(mean_q, covariance_q)

    return [base.log_density(shock) - proposal.log_density(shock) for shock in shocks]


def normalize_weights(log_weights: list[float]) -> list[float]:
    """Converts log-weights into weights summing to 1, via a numerically
    stable softmax (self-normalized importance sampling).
    """
    max_log_weight = max(log_weights)
    unnormalized = [math.exp(value - max_log_weight) for value in log_weights]
    total = sum(unnormalized)
    return [value / total for value in unnormalized]
