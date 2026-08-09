from dataclasses import dataclass


@dataclass(frozen=True)
class PingResult:
    message: str
    server_version: str


@dataclass(frozen=True)
class YieldCurvePoint:
    maturity: float
    zero_rate: float


@dataclass(frozen=True)
class BondDefinition:
    id: str
    face_value: float
    coupon_rate: float
    time_to_maturity: float
    coupon_frequency: int
    time_to_next_coupon: float
    quantity: float


@dataclass(frozen=True)
class DiscountedCashFlow:
    payment_time: float
    amount: float
    discount_factor: float
    present_value: float


@dataclass(frozen=True)
class BondValuation:
    id: str
    quantity: float
    unit_value: float
    position_value: float
    cash_flows: list[DiscountedCashFlow]


@dataclass(frozen=True)
class PortfolioValuation:
    total_value: float
    positions: list[BondValuation]


@dataclass(frozen=True)
class LossSample:
    shock: list[float]
    loss: float
