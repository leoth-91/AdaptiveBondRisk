import os
import socket
import subprocess
import time
from pathlib import Path

from abr_client import AdaptiveBondRiskClient


def find_available_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def test_python_client_can_ping_cpp_server() -> None:
    server_path = Path(os.environ["ADAPTIVE_BOND_RISK_SERVER"])
    port = find_available_port()
    address = f"tcp://127.0.0.1:{port}"

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
        result = None

        while time.monotonic() < deadline:
            if server.poll() is not None:
                output = server.stdout.read() if server.stdout else ""
                raise RuntimeError(
                    f"Server exited before handling the request:\n{output}"
                )

            try:
                client = AdaptiveBondRiskClient(address, timeout_ms=200)
                result = client.ping("integration test", request_id=123)
                break
            except TimeoutError:
                time.sleep(0.05)

        assert result is not None, "Server did not become ready within 5 seconds."
        assert result.message == "pong: integration test"
        assert result.server_version == "0.1.0"

        return_code = server.wait(timeout=5)
        output = server.stdout.read() if server.stdout else ""
        assert return_code == 0, output
        assert "Handled request 1" in output
    finally:
        if server.poll() is None:
            server.terminate()
            server.wait(timeout=5)
