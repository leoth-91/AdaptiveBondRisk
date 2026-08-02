# AdaptiveBondRisk

> **Work in progress:** the repository currently implements fixed-rate bond
> portfolio valuation. Monte Carlo risk simulation and adaptive allocation are
> planned but not yet implemented.

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
the numerical finance calculations, while Python supplies inputs and will later
perform statistical modelling and optimization. The two processes communicate
using Protocol Buffers and ZeroMQ request/reply messaging over TCP.

## Current functionality

The repository can currently:

- Read a synthetic fixed-rate bond portfolio from CSV in Python.
- Read a continuously compounded zero-rate curve from CSV.
- Send both datasets to the C++ server using Protocol Buffers.
- Generate each bond's future coupon and principal cash flows in C++.
- Interpolate zero rates and calculate discount factors.
- Return unit bond values, signed position values, discounted cash flows, and
  the total portfolio value to Python.
- Test the C++ finance code, Python input code, and the complete TCP exchange
  through one CTest command.

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

The next major stage is to generate level, slope, and curvature shocks to the
yield curve, fully reprice the portfolio, and estimate its loss distribution.
This will introduce Value at Risk, Expected Shortfall, and reproducible Monte
Carlo benchmarks.

The central research stage will then divide market shocks into severity strata
and adaptively allocate simulation batches across them. The resulting method
will be compared with ordinary Monte Carlo and classical stratified allocation
to measure whether the PhD framework provides a genuine improvement for
multi-output financial tail-risk estimation.

## Development approach

Alongside the project's primary aim of developing part of my PhD work into a
financial application, I am using it to explore agentic AI-assisted software
development workflows. AI agents support implementation, testing,
documentation, and code review. I remain responsible for the architecture,
financial-modelling assumptions, validation, and final technical decisions.
