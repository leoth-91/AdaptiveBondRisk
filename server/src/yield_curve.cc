#include "yield_curve.hh"

#include <algorithm>
#include <cmath>
#include <stdexcept>
#include <utility>

namespace adaptive_bond_risk
{

YieldCurve::YieldCurve(std::vector<YieldCurvePoint> points)
    : points_(std::move(points))
{
    if ( points_.empty() ) {
        throw std::invalid_argument("The yield curve must not be empty");
    }

    for ( const YieldCurvePoint& point : points_ ) {
        if ( point.maturity <= 0.0 ) {
            throw std::invalid_argument("Yield-curve maturities must be positive");
        }
    }

    for ( std::size_t index = 1; index < points_.size(); ++index ) {
        if ( points_[index].maturity <= points_[index - 1].maturity ) {
            throw std::invalid_argument(
                "Yield-curve maturities must be strictly increasing");
        }
    }
}

double YieldCurve::zero_rate(const double maturity) const
{
    if ( maturity <= 0.0 ) {
        throw std::invalid_argument("Cash-flow maturity must be positive");
    }
    if ( maturity < points_.front().maturity
         || maturity > points_.back().maturity ) {
        throw std::out_of_range("Cash flow lies outside the yield curve");
    }

    const auto upper = std::lower_bound(
        points_.begin(), points_.end(), maturity,
        [](const YieldCurvePoint& point, const double value) {
            return point.maturity < value;
        });

    if ( upper == points_.begin() || upper->maturity == maturity ) {
        return upper->zero_rate;
    }

    const YieldCurvePoint& right = *upper;
    const YieldCurvePoint& left  = *(upper - 1);
    const double weight =
        (maturity - left.maturity) / (right.maturity - left.maturity);

    return left.zero_rate + weight * (right.zero_rate - left.zero_rate);
}

double YieldCurve::discount_factor(const double maturity) const
{
    return std::exp(-zero_rate(maturity) * maturity);
}

}    // namespace adaptive_bond_risk
