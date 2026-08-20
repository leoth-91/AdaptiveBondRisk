#!/usr/bin/env python3

import argparse
import math
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GENERATED_MESSAGES_DIR = PROJECT_DIR / "build" / "generated" / "python"
MODULE_DIR = PROJECT_DIR / "client" / "module"


def positive_int(value: str) -> int:
    """Parses a positive integer, accepting scientific notation (e.g. 1e6)."""
    parsed = float(value)
    if not parsed.is_integer() or parsed <= 0:
        raise argparse.ArgumentTypeError(
            f"{value!r} is not a positive integer"
        )
    return int(parsed)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Simulate yield-curve shocks and estimate portfolio VaR."
    )
    parser.add_argument(
        "--address",
        default="tcp://127.0.0.1:5555",
        help="ZeroMQ server endpoint (default: tcp://127.0.0.1:5555)",
    )
    parser.add_argument(
        "--portfolio",
        type=Path,
        default=PROJECT_DIR / "data" / "demo_portfolio.csv",
        help="Portfolio CSV file",
    )
    parser.add_argument(
        "--curve",
        type=Path,
        default=PROJECT_DIR / "data" / "base_yield_curve.csv",
        help="Zero-rate curve CSV file",
    )
    parser.add_argument(
        "--num-samples",
        type=positive_int,
        default=10_000,
        help="Number of Monte Carlo shock draws, e.g. 1e6 (default: 10000)",
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.99,
        help="VaR confidence level (default: 0.99)",
    )
    parser.add_argument(
        "--base-vol",
        type=float,
        default=0.010,
        help="Short-end zero-rate shock volatility (default: 0.010, i.e. 100bp)",
    )
    parser.add_argument(
        "--vol-decay",
        type=float,
        default=0.05,
        help="Rate at which shock volatility decays with maturity (default: 0.05)",
    )
    parser.add_argument(
        "--corr-length",
        type=float,
        default=5.0,
        help="Correlation decay length in years (default: 5.0)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=0,
        help="Random seed for reproducibility (default: 0)",
    )
    return parser.parse_args()


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


def main() -> int:
    args = parse_arguments()

    if not GENERATED_MESSAGES_DIR.exists():
        print("Error: build the project before running the client.", file=sys.stderr)
        return 1

    sys.path.insert(0, str(GENERATED_MESSAGES_DIR))
    sys.path.insert(0, str(MODULE_DIR))

    try:
        from abr_client import AdaptiveBondRiskClient
        from financial_metrics import expected_shortfall, value_at_risk
        from portfolio_loader import load_portfolio, load_yield_curve

        portfolio = load_portfolio(args.portfolio)
        curve = load_yield_curve(args.curve)
        mean, covariance = build_shock_distribution(
            curve, args.base_vol, args.vol_decay, args.corr_length
        )

        client = AdaptiveBondRiskClient(args.address)

        print(f"Connecting to {args.address}")
        print(f"Simulating {args.num_samples:,} yield-curve shocks...")
        samples = client.simulate_losses(
            curve, portfolio, mean, covariance, args.num_samples, args.seed
        )

        losses = [sample.loss for sample in samples]
        mean_loss = sum(losses) / len(losses)
        var_estimate = value_at_risk(losses, args.alpha)
        es_estimate = expected_shortfall(losses, args.alpha)

        print(f"\nSamples:      {len(losses):,}")
        print(f"Mean loss:    {mean_loss:,.2f}")
        print(f"Max loss:     {max(losses):,.2f}")
        print(f"VaR({args.alpha:.2%}):    {var_estimate:,.2f}")
        print(f"ES({args.alpha:.2%}):     {es_estimate:,.2f}")
        return 0
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
