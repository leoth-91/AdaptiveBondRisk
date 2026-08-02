#include "fixed_rate_bond.hh"

#include <cmath>
#include <numeric>
#include <stdexcept>

namespace adaptive_bond_risk
{
namespace
{

constexpr double schedule_tolerance = 1.0e-9;

}    // namespace

FixedRateBond::FixedRateBond(const double face_value, const double coupon_rate,
                             const double time_to_maturity,
                             const unsigned int coupon_frequency,
                             const double time_to_next_coupon)
    : face_value_(face_value), coupon_rate_(coupon_rate),
      time_to_maturity_(time_to_maturity),
      coupon_frequency_(coupon_frequency),
      time_to_next_coupon_(time_to_next_coupon)
{
    if ( face_value_ <= 0.0 ) {
        throw std::invalid_argument("Bond face value must be positive");
    }
    if ( coupon_rate_ < 0.0 ) {
        throw std::invalid_argument("Bond coupon rate must not be negative");
    }
    if ( time_to_maturity_ <= 0.0 ) {
        throw std::invalid_argument("Bond maturity must be positive");
    }
    if ( coupon_frequency_ == 0 ) {
        throw std::invalid_argument("Bond coupon frequency must be positive");
    }
    if ( time_to_next_coupon_ <= 0.0
         || time_to_next_coupon_ > time_to_maturity_ ) {
        throw std::invalid_argument(
            "Time to next coupon must lie within the bond maturity");
    }

    const double remaining_periods =
        (time_to_maturity_ - time_to_next_coupon_) * coupon_frequency_;
    if ( std::abs(remaining_periods - std::round(remaining_periods))
         > schedule_tolerance ) {
        throw std::invalid_argument(
            "Bond maturity and next coupon do not form a regular schedule");
    }
}

std::vector<CashFlow> FixedRateBond::cash_flows() const
{
    const double interval      = 1.0 / coupon_frequency_;
    const double coupon_amount = face_value_ * coupon_rate_ / coupon_frequency_;
    const auto number_of_payments = static_cast<unsigned int>(
        std::llround((time_to_maturity_ - time_to_next_coupon_)
                     * coupon_frequency_))
                                    + 1;

    std::vector<CashFlow> cash_flows;
    cash_flows.reserve(number_of_payments);

    for ( unsigned int index = 0; index < number_of_payments; ++index ) {
        const double payment_time = time_to_next_coupon_ + index * interval;
        double amount             = coupon_amount;
        if ( index + 1 == number_of_payments ) {
            amount += face_value_;
        }
        cash_flows.push_back({payment_time, amount});
    }

    return cash_flows;
}

std::vector<DiscountedCashFlow>
FixedRateBond::discounted_cash_flows(const YieldCurve& curve) const
{
    std::vector<DiscountedCashFlow> discounted;

    for ( const CashFlow& cash_flow : cash_flows() ) {
        const double discount_factor =
            curve.discount_factor(cash_flow.payment_time);
        discounted.push_back({cash_flow.payment_time, cash_flow.amount,
                              discount_factor,
                              cash_flow.amount * discount_factor});
    }

    return discounted;
}

double FixedRateBond::value(const YieldCurve& curve) const
{
    const std::vector<DiscountedCashFlow> discounted =
        discounted_cash_flows(curve);
    return std::accumulate(
        discounted.begin(), discounted.end(), 0.0,
        [](const double total, const DiscountedCashFlow& cash_flow) {
            return total + cash_flow.present_value;
        });
}

}    // namespace adaptive_bond_risk
