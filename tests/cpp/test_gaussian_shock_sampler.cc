#include "gaussian_shock_sampler.hh"

#include <cmath>
#include <stdexcept>
#include <vector>

#include <catch2/catch_approx.hpp>
#include <catch2/catch_test_macros.hpp>

using Catch::Approx;
using adaptive_bond_risk::GaussianShockSampler;

TEST_CASE("A Gaussian shock sampler is reproducible for a fixed seed")
{
    GaussianShockSampler first({0.0, 0.0}, {1.0, 0.0, 0.0, 1.0}, 7);
    GaussianShockSampler second({0.0, 0.0}, {1.0, 0.0, 0.0, 1.0}, 7);

    for ( int i = 0; i < 5; ++i ) {
        REQUIRE(first.draw() == second.draw());
    }
}

TEST_CASE("Different seeds produce different draws")
{
    GaussianShockSampler first({0.0, 0.0}, {1.0, 0.0, 0.0, 1.0}, 1);
    GaussianShockSampler second({0.0, 0.0}, {1.0, 0.0, 0.0, 1.0}, 2);

    REQUIRE(first.draw() != second.draw());
}

TEST_CASE("An empty shock distribution is rejected")
{
    REQUIRE_THROWS_AS(GaussianShockSampler({}, {}, 1), std::invalid_argument);
}

TEST_CASE("A mismatched covariance size is rejected")
{
    REQUIRE_THROWS_AS(GaussianShockSampler({0.0, 0.0}, {1.0}, 1),
                      std::invalid_argument);
}

TEST_CASE("A non-positive-definite covariance is rejected")
{
    REQUIRE_THROWS_AS(
        GaussianShockSampler({0.0, 0.0}, {1.0, 2.0, 2.0, 1.0}, 1),
        std::invalid_argument);
}

TEST_CASE("Draws converge to the requested mean and variance")
{
    const double mean = 3.0;
    const double variance = 4.0;
    GaussianShockSampler sampler({mean}, {variance}, 42);

    constexpr int sample_count = 200'000;
    double sum = 0.0;
    double sum_sq = 0.0;
    for ( int i = 0; i < sample_count; ++i ) {
        const double value = sampler.draw()[0];
        sum += value;
        sum_sq += value * value;
    }

    const double sample_mean = sum / sample_count;
    const double sample_variance = (sum_sq / sample_count) - (sample_mean * sample_mean);

    REQUIRE(sample_mean == Approx(mean).margin(0.05));
    REQUIRE(sample_variance == Approx(variance).margin(0.1));
}

TEST_CASE("Draws respect the requested correlation structure")
{
    const double correlation = 0.8;
    GaussianShockSampler sampler({0.0, 0.0}, {1.0, correlation, correlation, 1.0}, 99);

    constexpr int sample_count = 200'000;
    double sum_x = 0.0;
    double sum_y = 0.0;
    double sum_xx = 0.0;
    double sum_yy = 0.0;
    double sum_xy = 0.0;
    for ( int i = 0; i < sample_count; ++i ) {
        const std::vector<double> shock = sampler.draw();
        sum_x += shock[0];
        sum_y += shock[1];
        sum_xx += shock[0] * shock[0];
        sum_yy += shock[1] * shock[1];
        sum_xy += shock[0] * shock[1];
    }

    const double mean_x = sum_x / sample_count;
    const double mean_y = sum_y / sample_count;
    const double cov_xy = (sum_xy / sample_count) - (mean_x * mean_y);
    const double var_x = (sum_xx / sample_count) - (mean_x * mean_x);
    const double var_y = (sum_yy / sample_count) - (mean_y * mean_y);
    const double sample_correlation = cov_xy / std::sqrt(var_x * var_y);

    REQUIRE(sample_correlation == Approx(correlation).margin(0.02));
}
