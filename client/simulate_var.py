#!/usr/bin/env python3

import argparse
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
    parser.add_argument(
        "--importance-mean-shift",
        type=float,
        default=None,
        help="If set, draw from a mean-shifted importance distribution "
             "(shock mean shifted by this amount, uniformly across "
             "maturities) and report importance-weighted VaR/ES instead of "
             "plain Monte Carlo.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    if not GENERATED_MESSAGES_DIR.exists():
        print("Error: build the project before running the client.", file=sys.stderr)
        return 1

    sys.path.insert(0, str(GENERATED_MESSAGES_DIR))
    sys.path.insert(0, str(MODULE_DIR))

    try:
        from abr_client import AdaptiveBondRiskClient
        from financial_metrics import (
            expected_shortfall,
            expected_shortfall_weighted,
            value_at_risk,
            value_at_risk_weighted,
        )
        from importance_sampling import log_importance_weights, normalize_weights
        from portfolio_loader import load_portfolio, load_yield_curve
        from shock_distribution import build_shock_distribution

        portfolio = load_portfolio(args.portfolio)
        curve = load_yield_curve(args.curve)
        mean, covariance = build_shock_distribution(
            curve, args.base_vol, args.vol_decay, args.corr_length
        )

        client = AdaptiveBondRiskClient(args.address)
        print(f"Connecting to {args.address}")

        if args.importance_mean_shift is None:
            method = "plain Monte Carlo"
            print(f"Simulating {args.num_samples:,} yield-curve shocks...")
            samples = client.simulate_losses(
                curve, portfolio, mean, covariance, args.num_samples, args.seed
            )

            losses = [sample.loss for sample in samples]
            mean_loss = sum(losses) / len(losses)
            var_estimate = value_at_risk(losses, args.alpha)
            es_estimate = expected_shortfall(losses, args.alpha)
        else:
            method = "importance-sampled"
            importance_mean = [m + args.importance_mean_shift for m in mean]
            print(
                f"Simulating {args.num_samples:,} yield-curve shocks from a "
                f"mean-shifted importance distribution (shift="
                f"{args.importance_mean_shift:+.4f})..."
            )
            samples = client.simulate_losses(
                curve, portfolio, importance_mean, covariance,
                args.num_samples, args.seed,
            )

            shocks = [sample.shock for sample in samples]
            losses = [sample.loss for sample in samples]
            log_weights = log_importance_weights(
                shocks, mean, covariance, importance_mean, covariance
            )
            weights = normalize_weights(log_weights)
            mean_loss = sum(w * loss for w, loss in zip(weights, losses))
            var_estimate = value_at_risk_weighted(losses, weights, args.alpha)
            es_estimate = expected_shortfall_weighted(losses, weights, args.alpha)

        print(f"\nMethod:       {method}")
        print(f"Samples:      {len(losses):,}")
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
