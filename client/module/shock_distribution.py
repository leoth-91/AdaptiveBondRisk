import math


def build_shock_distribution(
    curve, base_vol: float, vol_decay: float, corr_length: float
) -> tuple[list[float], list[float]]:
    """A simple illustrative Gaussian shock distribution over the curve's
    maturities: volatility decaying with maturity, correlation decaying with
    maturity distance. Not calibrated to historical data.
    """
    maturities = [point.maturity for point in curve]
    volatilities = [base_vol * math.exp(-vol_decay * m) for m in maturities]

    dimension = len(maturities)
    mean = [0.0] * dimension
    covariance = []
    for i in range(dimension):
        for j in range(dimension):
            correlation = math.exp(-abs(maturities[i] - maturities[j]) / corr_length)
            covariance.append(volatilities[i] * volatilities[j] * correlation)

    return mean, covariance
