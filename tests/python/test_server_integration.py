import os
import socket
import subprocess
import time
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

import pytest

from abr_client import AdaptiveBondRiskClient
from models import LossSample, PingResult, PortfolioValuation
from portfolio_loader import load_portfolio, load_yield_curve


Result = TypeVar("Result")


def find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def run_against_server(
    operation: Callable[[AdaptiveBondRiskClient], Result],
) -> Result:
    server_path = Path(os.environ["ADAPTIVE_BOND_RISK_SERVER"])
    address = f"tcp://127.0.0.1:{find_available_port()}"

    server = subprocess.Popen(
        [
            str(server_path),
            "--address",
            address,
            "--receive-timeout-ms",
            "50",
            "--max-requests",
            "1",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )

    try:
        deadline = time.monotonic() + 5

        while time.monotonic() < deadline:
            if server.poll() is not None:
                output = server.stdout.read() if server.stdout else ""
                raise RuntimeError(
                    f"Server exited before handling the request:\n{output}"
                )

            try:
                result = operation(
                    AdaptiveBondRiskClient(address, timeout_ms=200)
                )
                break
            except TimeoutError:
                time.sleep(0.05)
        else:
            pytest.fail("Server did not become ready within 5 seconds.")

        return_code = server.wait(timeout=5)
        output = server.stdout.read() if server.stdout else ""
        assert return_code == 0, output
        assert "Handled request 1" in output
        return result
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=5)


def test_python_client_can_ping_cpp_server() -> None:
    result = run_against_server(
        lambda client: client.ping("integration test", request_id=123)
    )

    assert isinstance(result, PingResult)
    assert result.message == "pong: integration test"
    assert result.server_version == "0.1.0"


def test_python_client_can_request_a_portfolio_valuation() -> None:
    data_dir = Path(os.environ["ADAPTIVE_BOND_RISK_DATA_DIR"])
    curve = load_yield_curve(data_dir / "base_yield_curve.csv")
    portfolio = load_portfolio(data_dir / "demo_portfolio.csv")

    result = run_against_server(
        lambda client: client.value_portfolio(curve, portfolio, request_id=456)
    )

    assert isinstance(result, PortfolioValuation)
    assert len(result.positions) == len(portfolio)
    assert result.total_value != 0.0
    assert all(position.cash_flows for position in result.positions)


def test_python_client_can_simulate_losses() -> None:
    data_dir = Path(os.environ["ADAPTIVE_BOND_RISK_DATA_DIR"])
    curve = load_yield_curve(data_dir / "base_yield_curve.csv")
    portfolio = load_portfolio(data_dir / "demo_portfolio.csv")

    dimension = len(curve)
    mean = [0.0] * dimension
    covariance = [
        0.0001 if i == j else 0.0
        for i in range(dimension)
        for j in range(dimension)
    ]

    result = run_against_server(
        lambda client: client.simulate_losses(
            curve, portfolio, mean, covariance,
            num_samples=5, seed=1, request_id=789,
        )
    )

    assert len(result) == 5
    assert all(isinstance(sample, LossSample) for sample in result)
    assert all(len(sample.shock) == dimension for sample in result)
