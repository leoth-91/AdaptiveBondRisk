import math


def _tail_index(sample_count: int, alpha: float) -> int:
    return min(math.ceil(alpha * sample_count) - 1, sample_count - 1)


def value_at_risk(losses: list[float], alpha: float) -> float:
    ordered = sorted(losses)
    return ordered[_tail_index(len(ordered), alpha)]


def expected_shortfall(losses: list[float], alpha: float) -> float:
    ordered = sorted(losses)
    tail = ordered[_tail_index(len(ordered), alpha):]
    return sum(tail) / len(tail)


def _weighted_tail_start(
    order: list[int], weights: list[float], alpha: float
) -> int:
    cumulative = 0.0
    for position, index in enumerate(order):
        cumulative += weights[index]
        if cumulative >= alpha:
            return position
    return len(order) - 1


def value_at_risk_weighted(
    losses: list[float], weights: list[float], alpha: float
) -> float:
    """VaR from a weighted sample, e.g. importance-sampled losses reweighted
    to the base distribution. `weights` must sum to 1 (see
    `importance_sampling.normalize_weights`); with uniform weights this
    matches `value_at_risk` exactly.
    """
    order = sorted(range(len(losses)), key=lambda i: losses[i])
    return losses[order[_weighted_tail_start(order, weights, alpha)]]


def expected_shortfall_weighted(
    losses: list[float], weights: list[float], alpha: float
) -> float:
    """ES from a weighted sample; see `value_at_risk_weighted`."""
    order = sorted(range(len(losses)), key=lambda i: losses[i])
    tail = order[_weighted_tail_start(order, weights, alpha):]
    tail_weight = sum(weights[i] for i in tail)
    return sum(weights[i] * losses[i] for i in tail) / tail_weight
