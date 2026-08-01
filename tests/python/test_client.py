import pytest

from abr_client import AdaptiveBondRiskClient


def test_empty_address_is_rejected() -> None:
    with pytest.raises(ValueError, match="address"):
        AdaptiveBondRiskClient("")


def test_negative_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="timeout"):
        AdaptiveBondRiskClient("tcp://127.0.0.1:5555", timeout_ms=-1)
