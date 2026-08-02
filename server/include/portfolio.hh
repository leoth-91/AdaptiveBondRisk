#pragma once

#include <string>
#include <vector>

#include "fixed_rate_bond.hh"

namespace adaptive_bond_risk
{

struct BondPosition
{
    std::string id;
    FixedRateBond bond;
    double quantity;
};

struct PositionValuation
{
    std::string id;
    double quantity;
    double unit_value;
    double position_value;
    std::vector<DiscountedCashFlow> cash_flows;
};

class Portfolio
{
  public:
    explicit Portfolio(std::vector<BondPosition> positions);

    [[nodiscard]] std::vector<PositionValuation>
    position_valuations(const YieldCurve& curve) const;
    [[nodiscard]] double value(const YieldCurve& curve) const;

  private:
    std::vector<BondPosition> positions_;
};

}    // namespace adaptive_bond_risk
