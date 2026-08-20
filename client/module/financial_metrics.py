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
