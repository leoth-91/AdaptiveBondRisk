#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GENERATED_MESSAGES_DIR = PROJECT_DIR / "build" / "generated" / "python"
MODULE_DIR = PROJECT_DIR / "client" / "module"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ask the C++ server to value a fixed-rate bond portfolio."
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
        "--show-cash-flows",
        action="store_true",
        help="Print each discounted bond cash flow",
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
        from portfolio_loader import load_portfolio, load_yield_curve

        portfolio = load_portfolio(args.portfolio)
        curve = load_yield_curve(args.curve)
        client = AdaptiveBondRiskClient(args.address)

        print(f"Connecting to {args.address}")
        valuation = client.value_portfolio(curve, portfolio)

        print("\nBond portfolio valuation")
        print(f"{'Position':<14}{'Quantity':>12}{'Unit value':>16}{'Position value':>20}")
        for position in valuation.positions:
            print(
                f"{position.id:<14}"
                f"{position.quantity:>12,.2f}"
                f"{position.unit_value:>16,.2f}"
                f"{position.position_value:>20,.2f}"
            )

            if args.show_cash_flows:
                for cash_flow in position.cash_flows:
                    print(
                        f"  t={cash_flow.payment_time:>5.2f} years  "
                        f"cash flow={cash_flow.amount:>9,.2f}  "
                        f"discount factor={cash_flow.discount_factor:.6f}  "
                        f"present value={cash_flow.present_value:>9,.2f}"
                    )

        print(f"\nTotal portfolio value: {valuation.total_value:,.2f}")
        return 0
    except (OSError, RuntimeError, TimeoutError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
