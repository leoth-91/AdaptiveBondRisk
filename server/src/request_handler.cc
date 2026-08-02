#include "request_handler.hh"

#include <exception>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "fixed_rate_bond.hh"
#include "messages.pb.h"
#include "portfolio.hh"
#include "yield_curve.hh"

namespace adaptive_bond_risk
{
namespace
{

namespace protocol = adaptive_bond_risk::protocol;

std::string serialize_response(const protocol::Response& response)
{
    std::string serialized;
    if ( !response.SerializeToString(&serialized) ) {
        throw std::runtime_error("Failed to serialize the response");
    }
    return serialized;
}

void value_portfolio(const protocol::PortfolioValueRequest& request,
                     protocol::PortfolioValueResponse& response)
{
    std::vector<YieldCurvePoint> curve_points;
    curve_points.reserve(request.yield_curve_size());
    for ( const protocol::YieldCurvePoint& point : request.yield_curve() ) {
        curve_points.push_back({point.maturity(), point.zero_rate()});
    }
    const YieldCurve curve(std::move(curve_points));

    std::vector<BondPosition> positions;
    positions.reserve(request.positions_size());
    for ( const protocol::BondPosition& position : request.positions() ) {
        positions.push_back(
            {position.id(),
             FixedRateBond(position.face_value(), position.coupon_rate(),
                           position.time_to_maturity(),
                           position.coupon_frequency(),
                           position.time_to_next_coupon()),
             position.quantity()});
    }
    const Portfolio portfolio(std::move(positions));

    const std::vector<PositionValuation> valuations =
        portfolio.position_valuations(curve);
    double total_value = 0.0;

    for ( const PositionValuation& valuation : valuations ) {
        protocol::BondValuation* result = response.add_positions();
        result->set_id(valuation.id);
        result->set_quantity(valuation.quantity);
        result->set_unit_value(valuation.unit_value);
        result->set_position_value(valuation.position_value);
        total_value += valuation.position_value;

        for ( const DiscountedCashFlow& cash_flow : valuation.cash_flows ) {
            protocol::DiscountedCashFlow* discounted = result->add_cash_flows();
            discounted->set_payment_time(cash_flow.payment_time);
            discounted->set_amount(cash_flow.amount);
            discounted->set_discount_factor(cash_flow.discount_factor);
            discounted->set_present_value(cash_flow.present_value);
        }
    }

    response.set_total_value(total_value);
}

}    // namespace

std::string RequestHandler::handle(const std::string& serialized_request) const
{
    protocol::Request request;
    protocol::Response response;

    if ( !request.ParseFromString(serialized_request) ) {
        response.set_success(false);
        response.set_error("The request is not a valid Protocol Buffer message");
        return serialize_response(response);
    }

    response.set_request_id(request.request_id());

    try {
        switch ( request.payload_case() ) {
        case protocol::Request::kPing: {
            response.set_success(true);
            auto* ping = response.mutable_ping();
            ping->set_message(request.ping().message().empty()
                                  ? "pong"
                                  : "pong: " + request.ping().message());
            ping->set_server_version(ADAPTIVE_BOND_RISK_VERSION);
            break;
        }
        case protocol::Request::kPortfolioValue:
            value_portfolio(request.portfolio_value(),
                            *response.mutable_portfolio_value());
            response.set_success(true);
            break;
        case protocol::Request::PAYLOAD_NOT_SET:
            response.set_success(false);
            response.set_error("The request does not contain an operation");
            break;
        }
    } catch ( const std::exception& error ) {
        response.Clear();
        response.set_request_id(request.request_id());
        response.set_success(false);
        response.set_error(error.what());
    }

    return serialize_response(response);
}

}    // namespace adaptive_bond_risk
