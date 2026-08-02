#include "fixed_rate_bond.hh"
#include "portfolio.hh"
#include "yield_curve.hh"

#include <cmath>
#include <vector>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

using Catch::Approx;

TEST_CASE("Yield-curve rates are linearly interpolated")
{
    const adaptive_bond_risk::YieldCurve curve(
        {{1.0, 0.02}, {3.0, 0.04}});

    REQUIRE(curve.zero_rate(1.0) == Approx(0.02));
    REQUIRE(curve.zero_rate(2.0) == Approx(0.03));
    REQUIRE(curve.discount_factor(2.0) == Approx(std::exp(-0.06)));
}

TEST_CASE("A fixed-rate bond is the sum of its discounted cash flows")
{
    const adaptive_bond_risk::YieldCurve curve(
        {{0.5, 0.05}, {1.0, 0.05}});
    const adaptive_bond_risk::FixedRateBond bond(1000.0, 0.10, 1.0, 2, 0.5);

    const std::vector<adaptive_bond_risk::DiscountedCashFlow> cash_flows =
        bond.discounted_cash_flows(curve);
    const double expected =
        50.0 * std::exp(-0.05 * 0.5) + 1050.0 * std::exp(-0.05);

    REQUIRE(cash_flows.size() == 2);
    REQUIRE(cash_flows[0].amount == Approx(50.0));
    REQUIRE(cash_flows[1].amount == Approx(1050.0));
    REQUIRE(bond.value(curve) == Approx(expected));
}

TEST_CASE("Portfolio value includes signed position quantities")
{
    const adaptive_bond_risk::YieldCurve curve(
        {{0.5, 0.03}, {1.0, 0.03}});
    const adaptive_bond_risk::FixedRateBond bond(1000.0, 0.04, 1.0, 2, 0.5);
    const double unit_value = bond.value(curve);

    const adaptive_bond_risk::Portfolio portfolio(
        {{"LONG", bond, 3.0}, {"SHORT", bond, -1.0}});

    REQUIRE(portfolio.value(curve) == Approx(2.0 * unit_value));
}
