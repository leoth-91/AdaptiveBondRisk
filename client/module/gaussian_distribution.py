import math


def _cholesky_decompose(covariance: list[float], dimension: int) -> list[float]:
    """Lower-triangular Cholesky factor C (row-major, dimension x dimension)
    of a symmetric positive definite matrix, such that covariance = C @ C.T.
    Only the lower triangle of `covariance` is read.
    """
    factor = [0.0] * (dimension * dimension)
    for row in range(dimension):
        for col in range(row + 1):
            total = covariance[(row * dimension) + col]
            for k in range(col):
                total -= factor[(row * dimension) + k] * factor[(col * dimension) + k]

            if row == col:
                if total <= 0.0:
                    raise ValueError(
                        "The covariance matrix must be symmetric positive definite"
                    )
                factor[(row * dimension) + col] = math.sqrt(total)
            else:
                factor[(row * dimension) + col] = (
                    total / factor[(col * dimension) + col]
                )
    return factor


def _forward_substitute(
    lower_triangular: list[float], dimension: int, rhs: list[float]
) -> list[float]:
    """Solves lower_triangular @ x = rhs for x."""
    solution = [0.0] * dimension
    for row in range(dimension):
        total = rhs[row]
        for col in range(row):
            total -= lower_triangular[(row * dimension) + col] * solution[col]
        solution[row] = total / lower_triangular[(row * dimension) + row]
    return solution


class GaussianDistribution:
    """A multivariate Gaussian with a fixed mean and covariance.

    The covariance is Cholesky-factored once at construction and reused for
    every subsequent log-density evaluation.
    """

    def __init__(self, mean: list[float], covariance: list[float]) -> None:
        self.mean = mean
        self.dimension = len(mean)
        if self.dimension == 0:
            raise ValueError("The distribution must not be empty")
        if len(covariance) != self.dimension * self.dimension:
            raise ValueError(
                "The covariance matrix size must be the mean length squared"
            )

        self._cholesky = _cholesky_decompose(covariance, self.dimension)
        self._log_det = 2.0 * sum(
            math.log(self._cholesky[(i * self.dimension) + i])
            for i in range(self.dimension)
        )

    def log_density(self, point: list[float]) -> float:
        centered = [point[i] - self.mean[i] for i in range(self.dimension)]
        z = _forward_substitute(self._cholesky, self.dimension, centered)
        mahalanobis_sq = sum(value * value for value in z)

        return -0.5 * (
            (self.dimension * math.log(2.0 * math.pi))
            + self._log_det
            + mahalanobis_sq
        )
