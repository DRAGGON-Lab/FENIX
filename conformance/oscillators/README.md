# Proposed repressilator feasibility studies

This separate development environment studies [issue #84](https://github.com/DRAGGON-Lab/FENIX/issues/84)
and [PROPOSED ADR-P09](../../spec/oscillators/ADR-P09.md). It does **not** import
FENIX, execute a native FENIX profile, or supply accepted golden fixtures.
The requested architecture is selected; equations, illustrative parameters,
numerical policy and acceptance thresholds still require scientific review.

`cases.json` specifies every parameter, initial count, unit, quantity basis and
study setting. The single-cell example has three transcript/repressor pairs
(six states). The distributed example has one transcript/synthase pair per
strain, all nine intracellular signal pools and three shared-medium totals
(18 states). Signal k is produced only in strain k; each gate senses the previous
signal. Export and import connect each strain to the medium with explicit volume
conversion and population-weighted extracellular fluxes.

## Run

From the repository root, with uv 0.11.29 and Python 3.12:

```sh
uv sync --project conformance/oscillators --locked
uv run --project conformance/oscillators --locked --offline python -m unittest discover -s conformance/oscillators -v
uv run --project conformance/oscillators --locked --offline python conformance/oscillators/study.py --output-dir artifacts/repressilator-study
```

The output directory must be new; checkout outputs must be under `artifacts/`.
The study fails explicitly on incomplete integration, exhausted work budgets,
invalid samples, failed oscillation criteria or an unexpectedly oscillatory
control. It does not clip counts or retry with different methods. Its separate
uv-generated lock adds no runtime dependency to either FENIX package.

## Evidence and limitations

Eight primary integrations compare DOP853 and Radau at baseline and refined
tolerances over 80,000 seconds. After discarding transients, two disjoint windows
measure complete cycles, period/amplitude variation, phase spacing and drift in
period, amplitude and cycle midpoint. Method/refinement comparisons check period,
amplitude and phase and report pointwise errors for every state. All thresholds
are explicit candidate choices in the catalog, not approved native tolerances.

Three negative integrations use Hill exponent one in each model and remove an
entire signal channel in the community. The latter sets its synthesis and every
initial pool to zero, preventing residual medium signal from masking the break.
Unit tests independently check exact rational weighted-balance expressions,
closed transport, analytical Jacobians against central differences, stable Hill
limits, sensing dependencies, domain failures and classifier counterexamples.

`report.json` contains all case/control definitions, the protocol, environment
versions, input/evaluator/lock hashes, solver work and measured outcomes.
Compressed CSVs retain every primary trajectory. Overview and detail PNG/SVG
figures show intracellular proteins and extracellular signal densities.
Reports and plots are generated observations, never checked-in golden values.

These two methods share SciPy and the same proposed RHS. Their agreement tests
numerical feasibility, not independent implementation correctness or biological
validity. No empirical calibration, stochastic simulation, growth, spatial
transport or native Python/Julia parity is claimed. Native examples remain
**NOT RUN — unsupported profile** until the ADR, wire formats, identity/rejection
catalogs and independent references pass the gates recorded in ADR-P09.
