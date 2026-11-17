# Native Julia M0 documents, FIR compilation, execution and results

Provisional package/module name `Fenix` and version `0.0.0` remain subject to
ADR-P06. The package implements immutable M0 content and committed documents under ratified
ADR-P01. It runs independently of Python and uses direct SciML solver packages for ODE execution, without Catalyst.

```julia
using Fenix.BioIR

cell = Compartment(id="cell", volume=Quantity(value=1e-15, unit="L"))
x = Species(id="x", compartment="cell", ports=[Port(id="amount")])
target = PortReference(species="x", port="amount")
design = DesignContent(
    id="design", revision=1,
    compartments=[cell], species=[x],
    parameters=[Parameter(id="alpha", unit="molecule/s"),
                Parameter(id="beta", unit="1/s")],
    functions=[BioIRFunction(id="production", kind="constitutive_production",
                            target=target, parameter="alpha"),
               BioIRFunction(id="decay", kind="first_order_decay",
                            target=target, parameter="beta")])
experiment = ExperimentContent(
    id="experiment", revision=1, source_design=design,
    design=DesignReference(id="design", revision=1, digest=repeat("0", 64)),
    parameters=[ParameterAssignment(parameter="alpha",
                    quantity=Quantity(value=10.0, unit="molecule/s")),
                ParameterAssignment(parameter="beta",
                    quantity=Quantity(value=0.1, unit="1/s"))],
    initial_counts=[InitialCount(species="x",
                    quantity=Quantity(value=0.5, unit="molecule"))],
    observables=[Observable(id="amount_x", target=target)], interventions=())
json = to_json(experiment)
content = to_dict(design)
```

The zero digest above is an unverified claim, accepted only as uncommitted data.
`source_design` checks ID/revision and local biological references; it is not
stored or serialized. Use the committed document APIs below to establish content
integrity and exact Design correspondence.
FIR compilation, native ODE execution and source-linked portable results are available below.

Constructors accept vectors or tuples and snapshot them into typed immutable
tuples. Nested values must use the native constructors. Exported dictionaries
and arrays are fresh copies. Declaration order is preserved. Fixed M0 kind and
schema tokens have defaults; IDs, revisions, quantities and interventions are
explicit. No unit conversion or scientific repair occurs.

Quantities accept finite `Float64` and built-in fixed-width integers within
`[-(2^53-1), 2^53-1]`, normalized to `Int64`; quantities must be nonnegative and
volumes positive. `Bool`, `Float32`, arbitrary precision and other numeric types
are rejected. Fractional expected counts, subnormals and negative zero are
supported. Strict document parsing additionally checks raw lexical underflow, integer-token
limits, duplicate decoded keys and invalid Unicode.

`BioIRValidationError` exposes `category`, constructor-relative JSON Pointer
`path` (zero-based array indices), and a readable message. Categories follow
approved P01 expectations; prose and precedence for multiple faults are not
portable contracts. Unknown/missing constructor keywords use Julia's native
argument errors. `BioIRFunction` avoids collision with Julia's `Function`.

## Development checks

CI uses Julia 1.10.13. From the repository root:

```sh
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=conformance/julia -e 'push!(LOAD_PATH, abspath("packages/julia")); include("packages/julia/test_native_content/runtests.jl")'
```

Package unit tests need no repository fixtures. The separate projection suite
checks 29 approved P01 content cases (6 accepts, 23 rejects), with 63 explicitly
deferred cases in that original builder-only registry. The separate document
suite now checks all 92 original P01 and the overlapping 97 P01 rejection cases. JSONSchema remains
in the pinned reference environment. The library uses JSON.jl for ordinary JSON
serialization and keeps its generated Manifest untracked.

## Committed documents

```julia
committed_design = DesignDocument(content=design, metadata=Metadata(name="Example"))
verified = from_json(DesignDocument, to_json(committed_design);
                     expected_digest=committed_design.digest)
exact_reference = reference(verified)
```

Construct `ExperimentContent` with `design=exact_reference` and
`source_design=verified.content`, then commit it with
`ExperimentDocument(content=content, source_design=verified)`. Read a committed
Experiment with `from_json(ExperimentDocument, raw; designs=[verified])`.
Only supplied verified immutable Designs are eligible; no network lookup,
newer-revision substitution or repair occurs. The Experiment envelope is verified
before reference resolution, and all three reference fields must match.

`canonical_content_bytes(document)` returns fresh direct RFC 8785/JCS bytes of
scientific content, excluding metadata and envelope digest. BioIR arrays retain
declaration order; FIR normalization is not applied. `to_json(document)` emits
transport JSON, retaining floating-point spellings needed by P01's raw integer
range rule. Canonical bytes are for identity and are not a transport envelope.

`with_metadata(document, Metadata(...))` creates a fresh envelope with the same
scientific identity. `replace_content(document, new_content)` requires the same
logical ID and a strictly increased revision when content changes. Deserialization
accepts an optional verified `previous` document for the same predecessor check.
No storage/history service is provided; callers retain historical revisions.

Digest self-consistency is separate from trust: `expected_digest` can check a
caller-supplied trusted expectation. Hashes establish no authorship, origin,
authenticated execution or biological validity. Metadata amendments are new
envelopes, not an authenticated archival record.

Native conformance command (pinned reference environment, no Python needed):

```sh
JULIA_PKG_OFFLINE=true julia --project=conformance/julia packages/julia/test_native_documents/runtests.jl --report artifacts/julia-native-documents.json
```

The document adapter only dispatches operations and labels supplied inputs.
Schema/canonical/numeric expectations come from unchanged approved references.
The 110 remaining rejection cases concern FIR/P03 and are outside this suite.

## Native FIR compilation

```julia
using Fenix
const FIR = Fenix.FIR
fir = compile_experiment(committed_experiment)
FIR.require_capability(fir, "ode")
model_bytes = FIR.canonical_model_bytes(fir)
identity_bytes = FIR.identity_bytes(fir)
digest = fir.digest
FIR.validate_sources(fir; design=committed_design, experiment=committed_experiment)
```

`compile_experiment` accepts a native committed `ExperimentDocument`, reverifies
both P01 sources and resolves the exact M0 production/decay roles. It preserves
represented parameter/initial values and observable IDs, including an empty
observable collection. Fixed volume contributes no multiplier in count space.
Compiler provenance records provisional `Fenix` and the installed package version.

`FIRModel(raw)` and `FIRDocument(model=..., provenance=...)` validate and snapshot
recursively immutable values. `FIR.from_dict(FIRModel, raw)` and
`FIR.from_json(FIRDocument, raw)` provide explicit factories; `FIR.to_dict` and
`FIR.to_json` return fresh exports. Standalone mathematical FIR may omit
provenance. Source-aware factories accept both `design` and `experiment` keyword
arguments and require complete producer correspondence.

Programmatic FIR numeric fields require finite `Float64`, including signed
stoichiometry. `BioIR.parse_json(raw; numeric_policy=:p03)` parses every numeric
token to binary64 under P03; its default `:p01` policy and all BioIR document
readers retain P01's integer restrictions. No implicit units or algebraic repair
are supported. `FIRValidationError` exposes `category`, `path` and `message`.

`FIR.normalized` returns a copy with only the six P03 declaration collections
sorted by UTF-16 keys. Canonical model bytes encode the normalized model;
identity bytes include the ratified domain/version wrapper. The digest hashes
identity bytes and excludes provenance. The original declaration order remains
available. Capability checking accepts `"ode"` and rejects unsupported requests,
including `"ssa"`; it provides no execution API.

Run the separate native conformance suite with the pinned reference environment:

```sh
julia --project=conformance/julia packages/julia/test_native_fir/runtests.jl --report artifacts/julia-native-fir.json
```

This exercises 207 rejection cases, 84 canonicalization cases, nine producer
controls and ten compiled binary64 triples linked to 40 fixed mathematical
samples at 512/1024-bit precision. Cases overlap across catalogs. Package tests
remain independent of repository fixtures and Python. The report fingerprints
actual runtime, sources and catalogs; historical reference reports remain intact.
The human PI accepted the bounded issue #25 implementation at `da13860`; see the
[acceptance record](../../docs/verification/ep03-julia-compiler.md#human-pi-implementation-acceptance--2026-11-17).
Later numerical/cross-language and release gates remain separate.


## Native ODE execution

```julia
using Fenix.Execution
spec = ODEExecutionSpec(time_grid=(0.0, 1.0, 10.0), method="Tsit5",
    rtol=1e-10, atol=1e-12, max_step=1.0, max_nfev=100000)
trajectory = solve_ode(fir.model, spec)
trajectory.state_values       # sample-major immutable tuples
trajectory.observable_values  # direct counts, aligned with observable_ids
trajectory.backend_versions
```

Explicit methods are `"Tsit5"` and `"Rodas5P"`. The direct SciML adapter solves
`x′ = alpha - beta*x` from t=0 with exact analytic Jacobian/time derivative for
the stiff method, requested-time `saveat`, automatic initial step, adaptive
stepping and no method switching or callbacks. `max_step` is seconds, `atol` is
molecules per representative cell and `rtol` is dimensionless. Every numerical
setting is required. There is no implicit volume/concentration conversion.

Times must be a nonempty tuple/vector of finite nonnegative `Float64` values,
strictly increasing numerically; vectors are snapshotted. All tolerance/step
fields require positive finite `Float64`; the RHS budget requires positive
native `Int`. Booleans, integers in float fields and arbitrary-precision values
are rejected. Local tolerances have no hidden floor or silent adjustment; extreme
settings can fail numerically. A late first sample still integrates from zero;
a zero-only grid returns the initial count after configuration/capability checks.

RHS evaluations include initialization and interpolation. The next evaluation is
rejected once `max_nfev` calls have been used. Failed/partial/misaligned/nonfinite
output and every negative sampled state produce `ODEExecutionError` with category,
settings, call count, reason and an optional underlying numerical exception. No clipping, analytical replacement or relaxed
retry occurs; intermediate stages may be negative. Ordinary underflow is allowed.
Unsupported profiles fail before execution, including on zero-only grids.

`ODETrajectory` retains immutable state/observable IDs, units, aligned rows,
FIR digest, execution settings, RHS/Jacobian/W-matrix counts and backend versions.
It promises bounded numerical agreement, not identical sample bits across runs,
versions or platforms. Execution settings never change FIR/source identity.
Portable results/manifests, native cross-language acceptance and release approval
remain separate gates; no solver success implies empirical biological validity.

The library has Pkg compatibility bounds for SciMLBase 3.58.x,
OrdinaryDiffEqTsit5 2.1.x and OrdinaryDiffEqRosenbrock 2.7.x. The generated library
Manifest stays ignored. A separate pinned native execution environment captures
the tested transitive graph; independent reference tooling remains unchanged:

```sh
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode packages/julia/test_native_ode/runtests.jl --report artifacts/julia-native-ode.json
```

The matrix checks 40 unchanged approved samples with both methods at coarse,
baseline and refined settings under P04's fixed `1e-9 + 1e-8*abs(reference)`
sampled-output bound. The report records individual errors/work and runtime,
source, contract and catalog identities. Refinement is an observation, not a
claim of method order or monotonic individual error reduction. Package tests use
local exact limiting cases and explicit failure controls, without repository
fixtures or Python.

Executed results and limits are recorded in the [issue #26 verification record](../../docs/verification/ep03-julia-ode.md).

The human PI approved the bounded issue #26 implementation at `34a092e` on
17 November 2026; see the [approval record](../../docs/verification/ep03-julia-ode.md#human-pi-implementation-approval--2026-11-17).
Results/manifests, independent cross-language acceptance and release gates remain
separate.

## Source-linked ODE results

```julia
using Fenix.Results: RunRecord, run_experiment
record = run_experiment(committed_experiment, spec)
manifest_text = Fenix.Results.to_json(record.manifest)
result_bytes = record.result_bytes
loaded = Fenix.Results.from_json(RunRecord, manifest_text, result_bytes;
    experiment=committed_experiment)
Fenix.Results.to_dict(loaded.result)
```

Capture reverifies the exact committed source pair, compiles and executes a
normalized FIR copy once, then records the actual SciML settings, versions,
RHS/Jacobian/W-matrix counts, timing and exact result-byte SHA-256. `build_id`
is null because no reliable installed build identifier is available. Wall-clock
observations have millisecond precision, padded to six fractional digits;
elapsed seconds use the monotonic clock and remain valid when wall time moves
backward. Compiler and solver failures propagate without a successful record.

Verified loading accepts the ratified `python-scipy-ode/0.1.0` and
`julia-sciml-ode/0.1.0` profiles. It recompiles only the supplied local source pair
and checks full source references, FIR identity, settings, counters, dimensions,
units, normalized observable order, zero-time values, bit-identical grids and
direct observable copies. It never executes an ODE, queries Git or resolves a
source over the network. The SciPy tolerance floor applies only to Python records.

Records are immutable and constructed only through validated capture/readback.
There is no public API for attaching arbitrary caller trajectories. `to_dict`
returns fresh nested values and fresh BigInts, `to_json(record.manifest)` retains
original manifest text, and each `record.result_bytes` access returns a fresh
vector of the original result bytes. Loading snapshots input byte vectors.
Integer-form budgets/counters preserve exact values beyond the reader's native
Int; native capture keeps the existing Int budget constraint. Binary64 decoding
preserves signed zero/subnormals and rejects overflow or lexical nonzero
underflow. P01/P03 public parsing policies remain unchanged.

Pass `expected_manifest_sha256=trusted_hash` to verify an independently trusted
manifest byte checksum. The result hash always covers the original bytes,
including formatting and final newlines. Neither checksum authenticates an
execution; plausible positive-time samples with recomputed untrusted hashes
can pass. Readback does not certify solver accuracy or biological validity.
`ResultValidationError` exposes `category`, artifact-prefixed JSON Pointer `path`
and a readable message. Use qualified Results serialization names alongside
BioIR/FIR, which expose their own serialization functions.

Package tests remain independent of repository fixtures. Run the separate native
results suite in the pinned SciML environment, without changing LOAD_PATH:

```sh
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode packages/julia/test_native_results/runtests.jl --report artifacts/julia-native-results.json
```

It checks all eight approved profile/example pairs, isolated solver traps during
readback and 160 analytical sample/method/setting comparisons against the 40
unchanged approved samples at P04 baseline/refined settings. Capture's own sample
bits must survive transport; separate solver reruns need not be bit-identical.
See the [implementation evidence](../../docs/verification/ep03-julia-results.md).
Human implementation acceptance, #29, parent epic acceptance and release
authorization remain separate gates.
