#pragma once

#include <cstdint>
#include <random>
#include <vector>

namespace adaptive_bond_risk
{

class GaussianShockSampler
{
  public:
    GaussianShockSampler(std::vector<double> mean, const std::vector<double>& covariance,
                         std::uint64_t seed);

    [[nodiscard]] std::vector<double> draw();

  private:
    std::vector<double> mean_;
    std::vector<double> cholesky_factor_;
    std::size_t dimension_;
    std::mt19937_64 generator_;
    std::normal_distribution<double> standard_normal_;
};

}    // namespace adaptive_bond_risk
