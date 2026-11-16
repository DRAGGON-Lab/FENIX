# ADR-P04 — proposed M0 ODE sampling, accuracy and failure contract

**Status: PROPOSED. Human PI ratification: PENDING.**

Issue [#21](https://github.com/DRAGGON-Lab/FENIX/issues/21); prerequisites #15
(approved analytical oracle) and #20 (merged native compiler). Architectural
basis: D06/D08/D09/D15/D23/D26–D29 in the
[approved decisions](../../../docs/approved-decisions.md).
The user approved preparing this proposal before implementation, selected SciPy
in the standard Python installation, both DOP853 and Radau, and rejection of
negative sampled counts. Those choices are proposal inputs, not ratification
of this complete contract. A generic instruction to implement the staged plan
is not recorded as scientific ratification.

## Scope and mathematical authority

The language-neutral rules below cover only the ratified
[P02](../../fir/proposals/ADR-P02.md) M0 problem
`dx/dt = alpha - beta*x`, `x(0) = x0`, with finite nonnegative represented
binary64 constants. Time is seconds; state is expected molecules per
representative cell, alpha is molecule/s and beta is 1/s. Fractional expected
counts remain valid. There is no volume multiplier or implicit conversion.

The [approved oracle](../../../conformance/production_decay/README.md) governs
mathematics and its fixed 40 samples. This proposal changes no BioIR/FIR field,
capability, source mapping, canonical byte, digest, fixture or reference value.
Execution settings remain outside FIR identity. SSA, events, communities,
empirical prediction, results serialization and RunManifest/P07 remain excluded.
The independent dual-language ODE gate stays under #29; this Python proposal
and its two SciPy methods do not substitute for that gate.

## Proposed language-neutral decision

### Sampling and settings

- Start at t=0 with the FIR initial count, even when the first requested sample
  is later. Require a nonempty strictly increasing sequence of finite
  nonnegative binary64 times. Compare times numerically: -0 and +0 are equal,
  so both together are duplicates. Reject negative, repeated, descending or
  nonfinite times; do not sort, deduplicate or invent samples.
- A grid containing only zero returns the initial state without integration,
  after the same configuration/capability validation as a nontrivial run.
- Require explicit method, positive finite absolute tolerance, positive finite
  relative tolerance, positive finite maximum step (seconds) and positive
  integer RHS-evaluation budget. No hidden numerical defaults or silent
  tolerance changes. Absolute tolerance is molecule per representative cell;
  relative tolerance is dimensionless. Backend-specific admissibility limits
  must be explicit; they do not change the mathematical FIR input domain.
- Return one sample for every requested time, with exact time/value alignment,
  state IDs, named observable IDs and their declared units. Empty observables
  remain empty; direct observables read their mapped state without conversion.
  Do not mutate the FIR, its source/provenance or mathematical identity.
- Repeatability means explicit settings with recorded backend versions and
  bounded numerical agreement. Bit-identical output across versions, platforms,
  integration steps or different methods is not promised.

### Accuracy and error budget

For each published acceptance sample require

`abs(x_num - x_ref) <= A + R*abs(x_ref)`

with **A = 1e-9 molecule per representative cell** and **R = 1e-8**.
These are proposed global sampled-output acceptance thresholds, separate from
backend-local `atol` and `rtol`. They apply to the declared reference matrix,
not as a certified bound for arbitrary valid inputs or arbitrary settings.
Near zero the absolute term governs. Pointwise acceptance measures integration
and interpolation together, including requested times between internal steps.
No separate upper bound on either contribution is claimed.

Decode the exact catalog parameter/time bits. Compare Decimal.from_float of
numerical output to the fixed 50-significant-digit decimal expectations with
100-digit arithmetic. The approved publication rounding bound is negligible
relative to A on this finite matrix; reference preparation is independently
supported by the retained rational audit and Python/Julia evaluators.
Do not replace represented binary64 0.1 with decimal-real 0.1.

Use both methods on all 40 approved samples with `rtol=1e-10`, `atol=1e-12`,
`max_step=1s`, budget 100000; repeat at `1e-11`, `1e-13`, `0.5s`.
Both configurations must pass the same predeclared acceptance thresholds.
Also report a coarser `1e-9`, `1e-11`, `2s` study. This is an observed joint
refinement study, not an estimate of method order or proof that individual
errors decrease monotonically. Local solver tolerances cannot certify global
error; no universal multiplication factor between them is assumed. The chosen
acceptance target and stricter local settings are a reviewable accuracy/cost
proposal, not a biological measurement-precision claim. Failed checks must be
reported; never loosen the thresholds merely to admit a solver result.

### Numerical failures and boundaries

- Require successful completion and finite, correctly shaped output for the
  complete requested grid. Failed/partial integration is not a successful
  trajectory. Diagnostics identify method, settings, evaluation count and reason.
- Reject every negative sampled count, however small. Signed zero is not
  negative. Do not clip, floor, take absolute values or silently change settings.
  Intermediate solver stages can be negative; this rule concerns returned
  samples, not internal Runge–Kutta or Newton stage admissibility.
- Detect nonfinite RHS arithmetic/output and report a numerical failure.
  A valid finite model can still fail because binary64 intermediate arithmetic
  overflows. Do not declare every finite FIR numerically executable.
- Ordinary binary64 underflow, including rounding to zero, is permitted without
  an artificial state/parameter floor. Preserve admissible finite subnormals.
  Underflow permission is not a guarantee of relative accuracy near zero.
- Count RHS calls from solver initialization, steps and requested-time
  interpolation. Check the limit before evaluating the next RHS: evaluate at
  most the requested budget. Exhaustion fails explicitly without a partial
  success result. This is a work-count bound, not a wall-clock or memory bound.
- Reject unsupported profiles/methods before solving. Never switch method,
  retry with looser tolerances, repair a model or substitute the analytical
  answer for failed numerical execution.

These conservative rules may reject mathematically admissible simulations,
including tiny negative interpolation excursions within a solver's local error
estimate. That explicit failure is preferred to silently repairing counts.

## Python backend appendix (proposed for #21)

Use [SciPy solve_ivp](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.solve_ivp.html)
with explicit DOP853 or Radau, `t_span=(0, last_requested_time)`, `t_eval` equal
to the requested grid, `vectorized=False`, `dense_output=False`, no events and
`first_step=None` (explicitly recorded automatic initial-step selection).
`t_eval` can use local interpolation even with dense_output=False; the sampled
accuracy tests include that error. Do not expose user callbacks or arbitrary
solver keyword forwarding. Resolve parameters/state by ID, never array position.
Radau receives the exact constant Jacobian `[[-beta]]`, as recommended by
[its documentation](https://docs.scipy.org/doc/scipy/reference/generated/scipy.integrate.Radau.html).
The language-neutral contract does not require Julia to use these algorithms.

Reject rtol below `100 * 2^-52` (approximately 2.220446049250313e-14), preventing
SciPy's silent upward adjustment. Use finite built-in floats in Python execution
numeric fields; exclude booleans, implicit strings and alternative numeric
classes. Require an immutable tuple of times and a positive non-boolean built-in
integer budget. Missing native arguments retain Python argument errors.

Use NumPy binary64 arithmetic with overflow/invalid/divide errors detected;
allow ordinary underflow. Convert expected numerical backend failures to
execution diagnostics while preserving their cause; do not hide programming
errors with a catch-all exception handler. Future tests must distinguish invalid
configuration, unsupported capability, failed solver status, exhausted budget,
nonfinite output, negative samples and malformed/incomplete results.

After ratification, add frozen keyword-only ODEExecutionSpec and solve_ode in
fenix.execution, accepting validated FIRModel only. The tuple-backed in-memory
ODETrajectory carries samples/units, FIR digest, settings and evaluation counts;
no portable result wire format, checksum or authenticated provenance is defined
here. #22/P07 retains Design/Experiment result provenance and serialization.

Proposed standard-install dependencies: `scipy>=1.18.1,<1.19` and
`numpy>=2.0,<2.8`; development-only `scipy-stubs>=1.18.1.1,<1.19`, uv-generated
lock. Verify independently installed wheels without development dependencies.
No dependency manifest or runtime package changes occur in this proposal.

## Alternatives, evidence and approval gate

Alternatives: DOP853 alone is smaller but less suitable for stiff decay; Radau
adds an independently tested stiff path. Allowing negatives within atol would
avoid some failures but weakens the chosen nonnegative-output rule. Silent
clipping or method fallback would obscure what computation was performed.
SciPy defaults alone do not establish FENIX's numerical accuracy requirements.

The [isolated trial](review_p04.py) exercises both methods directly, without a
FENIX package. Its additional stiff example uses alpha=2000000, beta=1000000,
x0=5 and requested times `(0, 1e-6, 1e-4, 1)` seconds, with independently
computed `2 + 3*exp(-1000000*t)` from the approved analytical law. These are
exploratory controls, not newly approved golden fixtures. Radau must satisfy
the same output bound with budget 100000; DOP853 is deliberately stopped at a
2000-evaluation budget. Mocked/production diagnostic paths are separate future
adapter tests, not implied by this experiment.

See the [execution/review record](../../../docs/verification/ep02-p04-proposal.md).
Human PI ratification must identify the reviewed revision and explicitly approve
P04's sampling, thresholds, failure/underflow/negative policies and scope.
Until that decision, production implementation and implementation approval are
PENDING. Ratification does not itself approve #21's implementation, complete #29,
merge a PR, close an epic or start #22.
