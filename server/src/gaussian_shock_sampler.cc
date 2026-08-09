#include "gaussian_shock_sampler.hh"

#include <cmath>
#include <stdexcept>
#include <utility>

namespace adaptive_bond_risk
{
namespace
{

// Lower-triangular Cholesky factor C of a symmetric positive definite matrix
// (stored row-major, dimension x dimension), such that covariance = C * C^T.
// Only the lower triangle of `covariance` is read.
std::vector<double> cholesky_decompose(const std::vector<double>& covariance,
                                       std::size_t dimension)
{
    std::vector<double> factor(dimension * dimension, 0.0);

    for ( std::size_t row = 0; row < dimension; ++row ) {
        for ( std::size_t col = 0; col <= row; ++col ) {
            double sum = covariance[(row * dimension) + col];
            for ( std::size_t k = 0; k < col; ++k ) {
                sum -= factor[(row * dimension) + k] * factor[(col * dimension) + k];
            }

            if ( row == col ) {
                if ( sum <= 0.0 ) {
                    throw std::invalid_argument(
                        "The covariance matrix must be symmetric positive definite");
                }
                factor[(row * dimension) + col] = std::sqrt(sum);
            } else {
                factor[(row * dimension) + col] =
                    sum / factor[(col * dimension) + col];
            }
        }
    }

    return factor;
}

}    // namespace

GaussianShockSampler::GaussianShockSampler(std::vector<double> mean,
                                           const std::vector<double>& covariance,
                                           std::uint64_t seed)
    : mean_(std::move(mean)),
      dimension_(mean_.size()),
      generator_(seed),
      standard_normal_(0.0, 1.0)
{
    if ( dimension_ == 0 ) {
        throw std::invalid_argument("The shock distribution must not be empty");
    }
    if ( covariance.size() != dimension_ * dimension_ ) {
        throw std::invalid_argument(
            "The covariance matrix size must be the mean length squared");
    }

    cholesky_factor_ = cholesky_decompose(covariance, dimension_);
}

std::vector<double> GaussianShockSampler::draw()
{
    std::vector<double> standard_normals(dimension_);
    for ( double& value : standard_normals ) {
        value = standard_normal_(generator_);
    }

    std::vector<double> shock(mean_);
    for ( std::size_t row = 0; row < dimension_; ++row ) {
        double sum = 0.0;
        for ( std::size_t col = 0; col <= row; ++col ) {
            sum += cholesky_factor_[(row * dimension_) + col] * standard_normals[col];
        }
        shock[row] += sum;
    }

    return shock;
}

}    // namespace adaptive_bond_risk
