#include "portfolio.hh"

#include <numeric>
#include <stdexcept>
#include <unordered_set>
#include <utility>

namespace adaptive_bond_risk
{

Portfolio::Portfolio(std::vector<BondPosition> positions)
    : positions_(std::move(positions))
{
    if ( positions_.empty() ) {
        throw std::invalid_argument("The portfolio must not be empty");
    }

    std::unordered_set<std::string> identifiers;
    for ( const BondPosition& position : positions_ ) {
        if ( position.id.empty() ) {
            throw std::invalid_argument("Bond identifiers must not be empty");
        }
        if ( position.quantity == 0.0 ) {
            throw std::invalid_argument("Bond quantities must not be zero");
        }
        if ( !identifiers.insert(position.id).second ) {
            throw std::invalid_argument("Bond identifiers must be unique");
        }
    }
}

std::vector<PositionValuation>
Portfolio::position_valuations(const YieldCurve& curve) const
{
    std::vector<PositionValuation> valuations;
    valuations.reserve(positions_.size());

    for ( const BondPosition& position : positions_ ) {
        std::vector<DiscountedCashFlow> cash_flows =
            position.bond.discounted_cash_flows(curve);
        const double unit_value = std::accumulate(
            cash_flows.begin(), cash_flows.end(), 0.0,
            [](const double total, const DiscountedCashFlow& cash_flow) {
                return total + cash_flow.present_value;
            });
        valuations.push_back({position.id, position.quantity, unit_value,
                              position.quantity * unit_value,
                              std::move(cash_flows)});
    }

    return valuations;
}

double Portfolio::value(const YieldCurve& curve) const
{
    const std::vector<PositionValuation> valuations =
        position_valuations(curve);
    return std::accumulate(
        valuations.begin(), valuations.end(), 0.0,
        [](const double total, const PositionValuation& valuation) {
            return total + valuation.position_value;
        });
}

}    // namespace adaptive_bond_risk
