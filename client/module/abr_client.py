import messages_pb2 as messages
import zmq

from models import (
    BondDefinition,
    BondValuation,
    DiscountedCashFlow,
    PingResult,
    PortfolioValuation,
    YieldCurvePoint,
)


class AdaptiveBondRiskClient:
    def __init__(self, address: str, timeout_ms: int = 5_000) -> None:
        if not address:
            raise ValueError("The server address must not be empty.")
        if timeout_ms < 0:
            raise ValueError("The timeout must not be negative.")

        self.address = address
        self.timeout_ms = timeout_ms

    def _exchange(self, request: messages.Request) -> messages.Response:
        context = zmq.Context()
        socket = context.socket(zmq.REQ)
        socket.setsockopt(zmq.LINGER, 0)
        socket.setsockopt(zmq.SNDTIMEO, self.timeout_ms)
        socket.setsockopt(zmq.RCVTIMEO, self.timeout_ms)

        try:
            socket.connect(self.address)

            socket.send(request.SerializeToString())

            response = messages.Response()
            response.ParseFromString(socket.recv())

            if response.request_id != request.request_id:
                raise RuntimeError(
                    "Response request ID does not match the request."
                )
            if not response.success:
                raise RuntimeError(f"Server error: {response.error}")
            return response
        except zmq.Again as error:
            raise TimeoutError(
                f"No response received within {self.timeout_ms} ms."
            ) from error
        finally:
            socket.close()
            context.term()

    def ping(self, message: str, request_id: int = 1) -> PingResult:
        request = messages.Request(
            request_id=request_id,
            ping=messages.PingRequest(message=message),
        )
        response = self._exchange(request)

        if not response.HasField("ping"):
            raise RuntimeError("Response does not contain a ping result.")

        return PingResult(
            message=response.ping.message,
            server_version=response.ping.server_version,
        )

    def value_portfolio(
        self,
        curve: list[YieldCurvePoint],
        positions: list[BondDefinition],
        request_id: int = 1,
    ) -> PortfolioValuation:
        request = messages.Request(request_id=request_id)

        for point in curve:
            curve_point = request.portfolio_value.yield_curve.add()
            curve_point.maturity = point.maturity
            curve_point.zero_rate = point.zero_rate

        for definition in positions:
            position = request.portfolio_value.positions.add()
            position.id = definition.id
            position.face_value = definition.face_value
            position.coupon_rate = definition.coupon_rate
            position.time_to_maturity = definition.time_to_maturity
            position.coupon_frequency = definition.coupon_frequency
            position.time_to_next_coupon = definition.time_to_next_coupon
            position.quantity = definition.quantity

        response = self._exchange(request)
        if not response.HasField("portfolio_value"):
            raise RuntimeError(
                "Response does not contain a portfolio valuation."
            )

        valuations = []
        for position in response.portfolio_value.positions:
            cash_flows = [
                DiscountedCashFlow(
                    payment_time=cash_flow.payment_time,
                    amount=cash_flow.amount,
                    discount_factor=cash_flow.discount_factor,
                    present_value=cash_flow.present_value,
                )
                for cash_flow in position.cash_flows
            ]
            valuations.append(
                BondValuation(
                    id=position.id,
                    quantity=position.quantity,
                    unit_value=position.unit_value,
                    position_value=position.position_value,
                    cash_flows=cash_flows,
                )
            )

        return PortfolioValuation(
            total_value=response.portfolio_value.total_value,
            positions=valuations,
        )
