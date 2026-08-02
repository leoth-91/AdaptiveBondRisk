#!/usr/bin/env python3

import argparse
import sys
from pathlib import Path


PROJECT_DIR = Path(__file__).resolve().parents[1]
GENERATED_MESSAGES_DIR = PROJECT_DIR / "build" / "generated" / "python"


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Send a test message to the AdaptiveBondRisk server."
    )
    parser.add_argument(
        "--address",
        default="tcp://127.0.0.1:5555",
        help="ZeroMQ server endpoint (default: tcp://127.0.0.1:5555)",
    )
    parser.add_argument(
        "--message",
        default="hello from Python",
        help="Text included in the ping request",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=5_000,
        help="Send and receive timeout in milliseconds (default: 5000)",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    if not GENERATED_MESSAGES_DIR.exists():
        print(
            "Error: generated Protocol Buffer files were not found.\n"
            "Build the project first with:\n"
            "  cmake -B build -DCMAKE_BUILD_TYPE=Release\n"
            "  cmake --build build",
            file=sys.stderr,
        )
        return 1

    sys.path.insert(0, str(GENERATED_MESSAGES_DIR))
    sys.path.insert(0, str(PROJECT_DIR / "client" / "module"))

    try:
        from abr_client import AdaptiveBondRiskClient
    except ModuleNotFoundError as error:
        print(
            f"Error: a Python dependency could not be loaded: {error}\n"
            "Create and activate the project environment from environment.yml.",
            file=sys.stderr,
        )
        return 1

    try:
        client = AdaptiveBondRiskClient(
            address=args.address,
            timeout_ms=args.timeout_ms,
        )
        print(f"Connecting to {args.address}")
        result = client.ping(args.message)
        print(f"Response: {result.message}")
        print(f"Server version: {result.server_version}")
        return 0
    except (RuntimeError, TimeoutError, ValueError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
