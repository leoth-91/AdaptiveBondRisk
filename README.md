# AdaptiveBondRisk

> **Work in progress:** the repository currently implements fixed-rate bond
> portfolio valuation, Monte Carlo loss simulation under Gaussian
> yield-curve shocks, empirical Value at Risk and Expected Shortfall, and
> importance sampling from a fixed, mean-shifted proposal distribution.
> Adaptively refining that proposal from prior simulation batches is planned
> but not yet implemented.

AdaptiveBondRisk is a C++/Python project exploring adaptive Monte Carlo methods
for financial tail-risk estimation. Its long-term goal is to estimate rare
losses in bond portfolios efficiently by learning where additional simulation
effort is most valuable.

The project is a finance-oriented continuation of a simulation-optimization
framework I developed during my PhD in numerical radiation dosimetry. In that work,
Python optimization code controlled a compiled C++ radiation-transport
simulation through a dedicated TCP interface and learned an efficient
importance-sampling distribution from simulation results. The method is
described in:

> Leo Thomas, Miriam Schwarze, and Hans Rabus (2026)
> [“Active learning-based optimization of variance reduction of Monte Carlo
> simulations: a feasibility study for the case of nanodosimetry around a gold
> nanoparticle”](https://doi.org/10.1088/1402-4896/ae6206),
> *Physica Scripta* **101** 175008.

AdaptiveBondRisk preserves that separation of responsibilities: C++ performs
the numerical finance and Monte Carlo simulation, while Python supplies
inputs, chooses the shock distribution, and will later perform the adaptive
statistical modelling. The two processes communicate using Protocol Buffers
and ZeroMQ request/reply messaging over TCP.

## Problem statement

Let $\mathbf{z}_0$ denote the current yield curve and $V(\mathbf{z})$ the
portfolio's value under a curve $\mathbf{z}$. A **shock**
$\mathbf{s} \in \mathbb{R}^K$ perturbs the curve,
$\mathbf{z} = \mathbf{z}_0 + \mathbf{s}$, producing a **loss**

$$
L(\mathbf{s}) := V(\mathbf{z}_0) - V(\mathbf{z}_0 + \mathbf{s}).
$$

Shocks are drawn from a distribution $p$ over $\mathbb{R}^K$. Every risk
quantity this project cares about — a loss-exceedance probability, Value at
Risk, Expected Shortfall — is an expectation of some function $g$ of the
loss:

$$
\theta = \mathbb{E}_{\mathbf{s} \sim p}\big[g(L(\mathbf{s}))\big].
$$

Monte Carlo estimates $\theta$ by averaging $g(L(\mathbf{s}_i))$ over draws
$\mathbf{s}_1, \dots, \mathbf{s}_N \sim p$. The optimization this project is
building toward does not change what is being estimated — it changes *how*
those draws are chosen, aiming to reduce the estimator's variance for a
fixed sampling budget. The full derivation — Value at Risk and Expected
Shortfall, the importance-sampling identity, and the reweighting this relies
on — is in [`docs/methodology.tex`](docs/methodology.tex).

## Current functionality

The repository can currently:

- Read a synthetic fixed-rate bond portfolio from CSV in Python.
- Read a continuously compounded zero-rate curve from CSV.
- Send both datasets to the C++ server using Protocol Buffers.
- Generate each bond's future coupon and principal cash flows in C++.
- Interpolate zero rates and calculate discount factors.
- Return unit bond values, signed position values, discounted cash flows, and
  the total portfolio value to Python.
- Simulate a batch of correlated yield-curve shocks in C++, drawn from a
  multivariate Gaussian distribution (a mean vector and covariance matrix
  over the curve's maturities) supplied by Python, reprice the portfolio
  under every shocked curve, and return each scenario's shock and loss in a
  single exchange.
- Estimate empirical Value at Risk and Expected Shortfall in Python from
  the returned losses.
- Draw from a mean-shifted importance (proposal) distribution instead of
  the base one, reweight each scenario by the likelihood ratio between the
  two, and report importance-weighted Value at Risk and Expected Shortfall
  that remain estimates of risk under the original (base) distribution.
- Test the C++ finance and sampling code, Python input code, and the
  complete TCP exchange (valuation and Monte Carlo simulation) through one
  CTest command.

The example inputs are in:

```text
data/base_yield_curve.csv
data/demo_portfolio.csv
```

The portfolio is synthetic and intended only to make the implementation easy
to run and inspect.

## Build and run

Create the common C++/Python environment:

```bash
conda env create -f environment.yml
conda activate abr
```

Configure and build the server and generated Protobuf bindings:

```bash
cmake -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build
```

Start the server:

```bash
./build/adaptive_bond_risk_server
```

In a second terminal, activate the same environment and request the example
portfolio valuation:

```bash
conda activate abr
python client/value_portfolio.py
```

To display every discounted cash flow as well:

```bash
python client/value_portfolio.py --show-cash-flows
```

Simulate yield-curve shocks and estimate Value at Risk and Expected
Shortfall:

```bash
python client/simulate_var.py
```

Shocks are drawn from an illustrative Gaussian distribution (volatility
decaying with maturity, correlation decaying with maturity distance) — not
calibrated to market data. Run `python client/simulate_var.py --help` for
the available parameters, including the sample count and confidence level.

To draw from a mean-shifted importance distribution instead, and report
importance-weighted risk measures:

```bash
python client/simulate_var.py --importance-mean-shift 0.01
```

The existing connection test remains available:

```bash
python client/test_client.py
```

Run all automated tests with:

```bash
ctest --test-dir build --output-on-failure
```

## Present modelling assumptions

The current valuation is deliberately small in scope:

- Times are expressed as year fractions from the valuation date.
- Coupon schedules contain regular periods without calendar or holiday rules.
- The time until the next coupon is supplied explicitly for every bond.
- Zero rates are continuously compounded and linearly interpolated.
- Values are dirty prices: the present value of all remaining cash flows.
- No credit risk, transaction costs, accrued-interest quotation convention, or
  market-data calibration is included yet.

These assumptions keep the first implementation transparent. The code and
tests make them explicit so that more realistic conventions can be introduced
incrementally.

## Intended direction

Yield-curve shocks are currently drawn from a multivariate Gaussian
distribution over the curve's maturities, with Value at Risk and Expected
Shortfall estimated empirically from the resulting losses. Importance
sampling from a fixed, mean-shifted proposal distribution is implemented
and reweights back to the original distribution correctly, but the shift is
currently chosen by hand rather than derived from the portfolio or prior
results, and its efficiency (variance reduction relative to plain Monte
Carlo, at the same sample budget) has not yet been measured.

The remaining steps are: quantifying that efficiency gain; a heavier-tailed
multivariate Student's *t* shock distribution and calibrating the shock
covariance against real yield-curve history, rather than the illustrative
one used today; and — the central research contribution — adaptively
refining the proposal distribution from prior simulation batches instead of
fixing it by hand. That adaptive refinement is the direct analogue of the
importance-sampling method from the PhD work, and will be compared with
plain Monte Carlo and classical stratified allocation to measure whether the
approach provides a genuine improvement for financial tail-risk estimation.

## Development approach

Alongside the project's primary aim of developing part of my PhD work into a
financial application, I am using it to explore agentic AI-assisted software
development workflows. AI agents support implementation, testing,
documentation, and code review. I remain responsible for the architecture,
financial-modelling assumptions, validation, and final technical decisions.
