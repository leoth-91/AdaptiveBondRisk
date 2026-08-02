#pragma once

#include <vector>

namespace adaptive_bond_risk
{

struct YieldCurvePoint
{
    double maturity;
    double zero_rate;
};

class YieldCurve
{
  public:
    explicit YieldCurve(std::vector<YieldCurvePoint> points);

    [[nodiscard]] double zero_rate(double maturity) const;
    [[nodiscard]] double discount_factor(double maturity) const;

  private:
    std::vector<YieldCurvePoint> points_;
};

}    // namespace adaptive_bond_risk
