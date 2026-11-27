# Proposed P08 stage-domain investigation

Refs #31 and #34. This is a pre-implementation numerical investigation, **not a
native FENIX conformance gate or an accepted executable contract**. It imports
no FENIX package and changes no existing reference, schema or scientific rule.

[settings.json](settings.json) freezes the candidate controls before comparison:
SciPy DOP853 and Radau, baseline `rtol=1e-9, atol=1e-11`, refined
`rtol=1e-11, atol=1e-13`, maximum step 1 second, and 200,000 RHS calls per run.
Radau receives the full analytical state-dependent Jacobian. DOP853 receives no
Jacobian. Each run attempts only its named method; there is no clipping, retry,
method substitution or analytical substitution. Negative extracellular sensing
stages fail immediately under P08. Other signed linear internal stage values
are not silently converted to physical output counts.

The unchanged ten-case catalog supplies 30 reference times. Forty integrations
(ten cases × two methods × two settings) supply 120 four-state comparisons.
The existing 160-digit Decimal laws provide the expectations. The study retains
reference strings, sample-major numerical values, explicit reference state IDs,
component error ratios and runtime/work information. It does not construct FIR,
portable results or run manifests. Exact file hashes identify candidate inputs
and the probe alongside the declared repository base. Settings and reference
hashes should be reviewed before any native comparison uses them.

The proposed state bound is `b_i(t) = 1e-9 + 1e-8 |x_ref,i(t)|`.
For closed transport with weights `w=(N_s,N_r,1,0)`, the triangle inequality gives

```text
|M_num(t) - M_num(0)| <= sum_i w_i b_i(t)
                         + |M_num(0) - M_ref(0)|.
```

The final term accounts for initial representation error; it must not be dropped
just because these integer initial states are represented exactly. The comparator
uses exact Decimal conversion of binary64 samples and reports both terms. The
closed-mass check is additional to every component comparison. Open-system
balance has existing independent exact-arithmetic evidence; this study does not
claim numerical integration of a general open-system balance observable.

The long-tail control reuses **the exact driven-n1 parameters and initial
counts**, extending the grid to `[0,1000]` and choosing a permitted maximum step
of 10 seconds. Its analytical extracellular count is `48 exp(-t/2) > 0` at every
finite real time. This grid extension is proposed investigative evidence; it
does not expand the existing 30-sample golden catalog. On the recorded SciPy
version, both methods at both settings attempt a negative sensing stage and
stop. Failed attempts emit no successful trajectory. The prediction is not a
claim that these methods are intrinsically incapable of solving this ODE.

Regression tests compare RHS values and the analytical Jacobian against the
independent Decimal balance equations, differentiating at 100 digits for Hill
exponents 1–4, asymmetric rates/populations/volumes, zero density, threshold and
both sides of threshold. They check incorrect population weighting/signs,
corrupted samples, work exhaustion, negative/nonfinite stages and outputs,
incomplete output and backend failure. Negative mathematical probes used to
differentiate at zero are never treated as valid solver stages.

Run from the repository root:

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/community/feasibility -v
uv run --project packages/python --locked --offline python conformance/community/feasibility/study.py --base-revision <reviewed-base-sha> --report artifacts/community-stage-feasibility.json
```

The command exits unsuccessfully if a bounded comparison fails or the pinned
tail predictions change. A changed prediction requires inspection; do not weaken
it simply to make CI pass. A passing investigative job preserves the observed
domain failures; it does not certify universal integration success.

See the [PI decision proposal](../../../spec/community/execution-feasibility-proposal.md)
and [local verification record](../../../docs/verification/m1-stage-feasibility.md).
Julia Tsit5/Rodas5P stage feasibility remains **NOT RUN**. Existing independent
BigFloat references remain separate evidence. Complete M1 wire/result schemas,
literal identity/rejection catalogs and exact reference acceptance remain open.
Native #32/#33, integration #35 and subsequent oscillator delivery remain gated.
