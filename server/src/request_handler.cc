#include "request_handler.hh"

#include <cstdint>
#include <exception>
#include <stdexcept>
#include <string>
#include <utility>
#include <vector>

#include "fixed_rate_bond.hh"
#include "gaussian_shock_sampler.hh"
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

std::vector<YieldCurvePoint> parse_curve_points(
    const google::protobuf::RepeatedPtrField<protocol::YieldCurvePoint>& points)
{
    std::vector<YieldCurvePoint> curve_points;
    curve_points.reserve(points.size());
    for ( const protocol::YieldCurvePoint& point : points ) {
        curve_points.push_back({point.maturity(), point.zero_rate()});
    }
    return curve_points;
}

Portfolio parse_portfolio(
    const google::protobuf::RepeatedPtrField<protocol::BondPosition>& positions)
{
    std::vector<BondPosition> parsed_positions;
    parsed_positions.reserve(positions.size());
    for ( const protocol::BondPosition& position : positions ) {
        parsed_positions.push_back(
            {position.id(),
             FixedRateBond(position.face_value(), position.coupon_rate(),
                           position.time_to_maturity(),
                           position.coupon_frequency(),
                           position.time_to_next_coupon()),
             position.quantity()});
    }
    return Portfolio(std::move(parsed_positions));
}

void value_portfolio(const protocol::PortfolioValueRequest& request,
                     protocol::PortfolioValueResponse& response)
{
    const YieldCurve curve(parse_curve_points(request.yield_curve()));
    const Portfolio portfolio = parse_portfolio(request.positions());

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

void simulate_losses(const protocol::SimulateLossesRequest& request,
                     protocol::SimulateLossesResponse& response)
{
    const std::vector<YieldCurvePoint> base_points =
        parse_curve_points(request.base_yield_curve());
    const YieldCurve base_curve(base_points);
    const Portfolio portfolio = parse_portfolio(request.positions());
    const double base_value = portfolio.value(base_curve);

    const std::vector<double> mean(request.mean().begin(), request.mean().end());
    if ( mean.size() != base_points.size() ) {
        throw std::invalid_argument(
            "The shock mean length must match the number of yield-curve points");
    }
    const std::vector<double> covariance(request.covariance().begin(),
                                         request.covariance().end());

    GaussianShockSampler sampler(mean, covariance, request.seed());

    for ( std::uint32_t i = 0; i < request.num_samples(); ++i ) {
        const std::vector<double> shock = sampler.draw();

        std::vector<YieldCurvePoint> shocked_points = base_points;
        for ( std::size_t j = 0; j < shocked_points.size(); ++j ) {
            shocked_points[j].zero_rate += shock[j];
        }
        const YieldCurve shocked_curve(std::move(shocked_points));

        protocol::LossSample* sample = response.add_samples();
        for ( double component : shock ) {
            sample->add_shock(component);
        }
        sample->set_loss(base_value - portfolio.value(shocked_curve));
    }
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
        case protocol::Request::kSimulateLosses:
            simulate_losses(request.simulate_losses(),
                            *response.mutable_simulate_losses());
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
