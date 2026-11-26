# Candidate independent ADR-P09 analytical references

These **PI-ACCEPTED component references** support [issue #84](https://github.com/DRAGGON-Lab/FENIX/issues/84)
under the [ratified P09 mathematical scope](../../../spec/oscillators/ADR-P09.md).
The PI accepted the exact 11 cases/33 samples at reviewed commit `6ab3dd4`;
see the [bounded acceptance record](../../../docs/verification/p09-component-reference-acceptance.md).
They supply no new wire formats or native execution evidence. They complement the long-horizon feasibility study with independently
derived laws, separately written Python Decimal and Julia BigFloat evaluators,
and explicit failure controls. Neither analytical evaluator imports FENIX,
SciPy, NumPy or the study evaluator.

## Complete inputs and laws

`cases.json` fixes every initial state, rate, volume, population, unit, basis,
state position and sample time. All 11 cases are evaluated at 0, 1 and 4 seconds.
Intracellular states are expected counts per representative cell; medium states
are total counts. The large illustrative volumes and disabled reactions isolate
algebraic behavior; these are abstract tests, not calibrated biological examples.

Both readers require the fixed SHA-256 of the **complete raw catalog bytes**
before reading its definitions or trusting a report's fingerprint. This policy
deliberately rejects formatting changes too. A candidate catalog change requires
explicit review of both independent pins, not a freshly computed report hash.
This protects populations at equilibrium, paired rate changes and disconnected
volumes even when all reported trajectories would remain identical.

### Driven repression (eight cases)

There are single-cell and three-strain cases for each Hill exponent n=1..4.
Only gate 1 has induced transcription. Its previous input is a decaying protein
(single cell) or its own intracellular signal 3 (community), with count
`8 exp(-t/2)`, volume 2 L and K=2 molecule/L. The community medium signal 3 is
instead a constant 999 molecules, exposing accidental sensing of the medium.
All translation and signal synthesis are disabled in these isolated cases.

Let `lambda=n/2`, `A=2^n` and `z=exp(-lambda*t)`. Integrating

    m' + lambda*m = 1 + 4/(1 + A*exp(-lambda*t)),  m(0)=2

gives

    m = 2*z + (1-z)/lambda
        + (4/lambda)*[1-z - A*z*log((exp(lambda*t)+A)/(1+A))].

Python uses the growing exponential and logarithmic ratio. Julia independently
uses `lambda*t + log1p(A*z) - log1p(A)` and `expm1` for the same integral.
These cases cross the repression threshold between t=1 and t=4. Sensing consumes
no protein or signal. All unmentioned expression states remain zero.

### Catalytic translation (one six-state case)

For gate i, with a_i=i, b_i=i+1, translation c_i=i+2,
initial transcript M_i=i+1 and initial protein P_i=i+4 (i=1..3),

    m_i = M_i exp(-a_i*t)
    p_i = P_i exp(-b_i*t)
          + c_i*M_i*[exp(-a_i*t)-exp(-b_i*t)]/(b_i-a_i).

This checks all three translation roles and distinct first-order losses without
consuming transcripts. Julia factors the homogeneous decay and uses `expm1`.

### Community equilibrium (one 18-state case)

All transcripts/proteins are one. For each signal the intracellular counts equal
cell volumes [2,3,5], and the medium total is 12 in 12 L. Every signal has density
one, equal to K. Basal/induced/loss rates balance each gate at G=1/2; translation
balances protein loss. Signal synthesis in its owner balances only that owner's
intracellular signal loss. Bidirectional unit exchange has zero net flux.
The explicit populations [3,5,7] still belong to the fully pinned definition.

### Closed community transport (one 18-state case)

Expression, synthesis and losses are zero. Export/import constants are all one.
Cell volumes [2,3,5] and populations [3,5,7] give intracellular capacity S=56 L;
medium volume V=12 L. For signal k=1..3, initial intracellular density q_k=k+1
and medium density e_k=k+5. Let

    M_k = S*q_k + V*e_k
    d_k = M_k/(S+V)
    z = exp(-(1+S/V)*t) = exp(-17*t/3).

The intracellular density is `d_k+(q_k-d_k)*z`; multiply by each cell's volume
to obtain its per-cell count. Medium total is `V*[d_k+(e_k-d_k)*z]`.
Julia derives medium totals first and recovers intracellular density from exact
weighted mass. All three signals have nonzero transient exchange. Weighted mass
is conserved for all sample times; an unweighted sum is not the governing law.

## Run and inspect

From repository root, following the existing locked environment setup:

```sh
uv sync --project conformance/oscillators --locked
uv run --project conformance/oscillators --locked --offline python -m unittest discover -s conformance/oscillators/references -v
uv run --project conformance/oscillators --locked --offline python conformance/oscillators/references/reference.py > /tmp/p09-analytical-reference.json
julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
julia --project=conformance/julia conformance/oscillators/references/reference.jl /tmp/p09-analytical-reference.json
julia --project=conformance/julia conformance/oscillators/references/test_reference.jl /tmp/p09-analytical-reference.json
uv run --project conformance/oscillators --locked --offline python conformance/oscillators/references/compare_study.py --output /tmp/p09-study-comparison.json
```

The comparison output must be new. Python computes analytical values at 80 and
160 decimal digits; Julia independently repeats at 512 and 1024 bits. Candidate
precision limits are 1e-70 (Python), 1e-140 (Julia and cross-evaluator agreement),
scaled by max(1, |reference|). At high precision, central differences independently
connect every closed form to the component P09 RHS, with h=1e-35 / residual 1e-65
for Python and h=1e-40 / residual 1e-75 for Julia. Exact initial states are checked.
These thresholds concern reference calculations, not native ODE acceptance.

The candidate study comparison uses both DOP853/Radau at rtol=1e-12, atol=1e-13 and maximum
step 0.05 s. It checks 828 state/time samples against the candidate bound
`1e-9 + 1e-8*abs(analytical)`. The report retains source/catalog hashes, versions,
settings, work and maximum error/bound per run. It reports only candidate-study
agreement; it executes no native FENIX profile.

Python tests cover every scalar catalog input and structural mutations, exact
weighted balances, incorrect Hill/translation/transport rules, read-only sensing,
plausible sample corruption and wrong-source rate comparisons. Julia checks the
complete ordered sample set, state dimensions, nonfinite/negative values, invalid
times, refinement metadata and catalog mutations with recomputed fingerprints.
CI uploads the analytical report and candidate comparison separately. The raw
catalog retains its historical PROPOSED status to preserve the reviewed byte
pin; the subsequent human decision accepts only the component-reference scope.

These analytical cases deliberately isolate components. They do not prove
long-horizon nonlinear oscillation accuracy, full profile support or empirical
biological validity. Independently accepted nonlinear-cycle references,
wire/identity/rejection catalogs and native Python/Julia evidence remain separate
work. No original M0 or M1 fixture or threshold is replaced.
