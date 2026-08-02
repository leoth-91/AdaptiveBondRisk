#pragma once

#include <vector>

#include "yield_curve.hh"

namespace adaptive_bond_risk
{

struct CashFlow
{
    double payment_time;
    double amount;
};

struct DiscountedCashFlow
{
    double payment_time;
    double amount;
    double discount_factor;
    double present_value;
};

class FixedRateBond
{
  public:
    FixedRateBond(double face_value, double coupon_rate, double time_to_maturity,
                  unsigned int coupon_frequency,
                  double time_to_next_coupon);

    [[nodiscard]] std::vector<CashFlow> cash_flows() const;
    [[nodiscard]] std::vector<DiscountedCashFlow>
    discounted_cash_flows(const YieldCurve& curve) const;
    [[nodiscard]] double value(const YieldCurve& curve) const;

  private:
    double face_value_;
    double coupon_rate_;
    double time_to_maturity_;
    unsigned int coupon_frequency_;
    double time_to_next_coupon_;
};

}    // namespace adaptive_bond_risk
