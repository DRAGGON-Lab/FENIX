# EP-03 / #26 — native Julia direct SciML ODE execution

Refs [#26](https://github.com/DRAGGON-Lab/FENIX/issues/26). Base: merged #25,
`ab6930cad7a7`, branch `feat/26-julia-ode`. Human implementation acceptance
remains pending. Authority is ratified [P04](../../spec/execution/proposals/ADR-P04.md),
[P02](../../spec/fir/proposals/ADR-P02.md) and the approved independent
[production-decay references](../../conformance/production_decay/README.md).
No scientific contract, golden fixture, Python implementation or package version
changes. Native cross-language acceptance (#29), results/manifests (#27), SSA,
parent EP-03 acceptance and release authorization remain separate gates.

## Implemented boundary

`Fenix.Execution` exposes immutable `ODEExecutionSpec`/`ODETrajectory`, typed
configuration/execution diagnostics and `solve_ode(FIRModel, spec)`. The adapter
resolves IDs, then solves `dx/dt = alpha - beta*x` from t=0, in expected molecules
per representative cell and seconds. There is no volume multiplier. It uses
SciMLBase's ODEProblem/ODEFunction and explicit Tsit5 or Rodas5P, with exact
Jacobian `[-beta]` and autonomous time derivative `[0]`. No Catalyst, symbolic
model rewriting, serialized callbacks or Python runtime is required.

The configuration snapshots declaration order and requires finite nonnegative
strictly increasing Float64 times, explicit method, positive finite Float64 local
tolerances/maximum step and positive native Int RHS budget. Zero-only sampling
still validates capability/settings, then preserves the initial state without
integration. A late first sample still integrates from zero. Automatic initial
step is explicitly selected with `dt=nothing`; adaptive stepping is enabled,
maximum iterations is typemax(Int), callbacks are disabled and saveat is exactly
the requested grid, without internal-step output or dense trajectory retention.
SciML's automatic minimum-step/step-control rules may fail on extreme settings;
no hidden tolerance adjustment or arbitrary count floor is introduced.

RHS calls are counted before every evaluation, including initialization and
sampling interpolation; the next call fails at the requested budget. Nonfinite
RHS arithmetic, failed integration, incomplete/misaligned/nonbinary64 samples,
nonfinite output and every negative sampled count fail explicitly. There is no
clipping, loose retry, automatic method switch or analytical replacement.
Ordinary underflow is permitted. Expected numerical linear-solver exceptions
retain their cause and execution diagnostics; programming errors are rethrown.

Trajectories retain tuple-backed sample-major state/observable rows, IDs/units,
FIR digest, settings, work counts and direct backend versions. FIR values and
source identities are unchanged. This is in-memory numerical output, not P07
serialization, execution authentication or a bitwise-repeatability guarantee.

## Numerical evidence

Julia 1.10.13, SciMLBase 3.58.0, OrdinaryDiffEqTsit5 2.1.5 and
OrdinaryDiffEqRosenbrock 2.7.5. Direct compatibility bounds allow these patch
series; the separate Pkg-generated [native test environment](../../conformance/julia_ode/README.md)
pins the complete tested dependency graph. The library Manifest stays ignored;
the independent reference environment remains unchanged. The native ODE runner
uses that active pinned environment directly, without prepending the library
environment, and checks that the loaded Fenix source is the repository package.

The native runner decodes exact approved binary64 parameter/time bits, authors
and compiles sources, then executes both methods on all 40 fixed samples at
three predeclared settings. Binary64 outputs convert exactly to 512-bit BigFloat,
and fixed 50-digit decimal references are compared with P04's unchanged global
bound `1e-9 + 1e-8*abs(reference)` molecules. The comparison precision exceeds
100 decimal digits and is distinct from binary64 integration. No expectation is
generated from numerical output.

| Method | Study | Maximum absolute error (molecule) | Maximum fraction of P04 bound | Total RHS calls over ten cases |
|---|---|---:|---:|---:|
| Tsit5 | coarse | 7.281018e-10 | 2.192627e-3 | 3078 |
| Tsit5 | baseline | 5.839512e-11 | 2.715112e-4 | 4788 |
| Tsit5 | refined | 2.363820e-11 | 3.931062e-5 | 7806 |
| Rodas5P | coarse | 1.815783e-9 | 2.867990e-3 | 3476 |
| Rodas5P | baseline | 2.595301e-10 | 3.983489e-4 | 5476 |
| Rodas5P | refined | 2.971762e-11 | 4.561313e-5 | 9060 |

Coarse settings: rtol=1e-9, atol=1e-11, max_step=2s; baseline: 1e-10, 1e-12,
1s; refined: 1e-11, 1e-13, 0.5s; each budget=100000. All **240** sample/method/
setting comparisons pass (**603** matrix assertions). The study reports joint
refinement, not a method-order estimate or guaranteed monotonic individual error.
A separate stiff exploratory control under the same analytical law passes for
Rodas5P; Tsit5 exhausts exactly its declared 2000-call budget (**seven** assertions).
This control is not a newly approved golden fixture.

The report records actual sample bits, individual absolute/scaled errors,
settings/work counts, platform/runtime and source/catalog/contract/evaluator/lock
fingerprints. Output-path protection reuses the existing native FIR guard for
sources, fixtures, symlinks and hardlink aliases. CI uploads a separate native
ODE artifact. All historical reference receipts retain their original observations.

## Verification and review limits

The [machine receipt](ep03-julia-ode.json) records exact commands, source/lock
fingerprints, outcomes and log hashes. Executed checks include:

- Native package tests, including **212** execution assertions for configuration,
  immutable snapshots, units/interfaces, zero-only/late sampling, limiting cases,
  bounded repeatability, budget/nonfinite/negative/failed/malformed output,
  unsupported capability and unchanged FIR identity.
- Standalone copied package with `PATH=/nonexistent` and assertions that neither
  Python nor Python3 is discoverable.
- Native FIR/compiler catalog regressions, existing native content/document
  suites, Python package/native FIR regressions, repository checker/harness,
  independent Python/Julia mathematical oracles, report comparison and exact
  rational audit.

The initial regression failed because Execution was absent. The first integrated
implementation run exposed an incorrect explicit `dt=0.0`, which SciML treated
as a zero step; changing it to the documented automatic `nothing` fixed the
matrix. A malformed-output test initially homogenized an integer row into
Float64 through Julia array construction; its explicit mixed-type test input was
corrected. No scientific reference or acceptance threshold was weakened.

Code and dependency-source review checked sampling, budget placement, tolerance
forwarding, exact autonomous derivatives, strict negative rejection, immutable
output and exception handling. This is agent implementation/review evidence;
it is not independent human implementation acceptance. Finite mathematical inputs
can still fail numerically; bounded sampled agreement establishes no empirical
biological validity or complete M0/release acceptance.

Backend API sources: [SciML solver options](https://docs.sciml.ai/DiffEqDocs/stable/basics/common_solver_opts/)
and [SciML solution/return-code interface](https://docs.sciml.ai/SciMLBase/stable/interfaces/Solutions/).
