import csv
from pathlib import Path

from models import BondDefinition, YieldCurvePoint


PORTFOLIO_COLUMNS = [
    "id",
    "face_value",
    "coupon_rate",
    "time_to_maturity",
    "coupon_frequency",
    "time_to_next_coupon",
    "quantity",
]

CURVE_COLUMNS = ["maturity", "zero_rate"]


def load_portfolio(path: Path) -> list[BondDefinition]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != PORTFOLIO_COLUMNS:
            raise ValueError(
                f"Portfolio columns must be: {', '.join(PORTFOLIO_COLUMNS)}"
            )

        return [
            BondDefinition(
                id=row["id"],
                face_value=float(row["face_value"]),
                coupon_rate=float(row["coupon_rate"]),
                time_to_maturity=float(row["time_to_maturity"]),
                coupon_frequency=int(row["coupon_frequency"]),
                time_to_next_coupon=float(row["time_to_next_coupon"]),
                quantity=float(row["quantity"]),
            )
            for row in reader
        ]


def load_yield_curve(path: Path) -> list[YieldCurvePoint]:
    with path.open(newline="", encoding="utf-8") as source:
        reader = csv.DictReader(source)
        if reader.fieldnames != CURVE_COLUMNS:
            raise ValueError(
                f"Yield-curve columns must be: {', '.join(CURVE_COLUMNS)}"
            )

        return [
            YieldCurvePoint(
                maturity=float(row["maturity"]),
                zero_rate=float(row["zero_rate"]),
            )
            for row in reader
        ]
