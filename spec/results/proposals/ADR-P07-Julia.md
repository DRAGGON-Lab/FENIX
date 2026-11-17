# ADR-P07 supplement — Julia/SciML ODE manifests

**Status: PROPOSED. Human PI ratification and bounded expectation acceptance
PENDING. No native result implementation is authorized by this supplement.**

Refs [#27](https://github.com/DRAGGON-Lab/FENIX/issues/27). Baseline `56ad188`
contains merged #25/#26. Ratified [P07](ADR-P07.md) covers the language-neutral
core and Python/SciPy profile only. This additive proposal requires independent
engineering/scientific review and explicit PI approval of the exact reviewed
revision, schema and bounded expectations before Julia results implementation.
It does not amend the historical P07 approval or its approved artifact bytes.

## Scope and compatibility

Propose closed profile `julia-sciml-ode/0.1.0`, sharing P07 core schema version
`0.1.0` and the unchanged [ODEResult schema](ode-result-m0.schema.json).
The additive [Julia manifest schema](run-manifest-julia-sciml-m0.schema.json)
references the unchanged [Python manifest schema](run-manifest-m0.schema.json)
for every core property. Resolve those references locally; validation must not
fetch resources. The Python schema still rejects Julia payloads. A future Julia
reader supports both explicit profiles with their own schemas and semantics;
an existing Python reader is not silently extended. Unknown versions/profiles
reject. New backend support does not imply method equivalence or identical
result checksums. Source, normalized FIR, units and all P01–P04 meanings remain
unchanged. No new numerical oracle or acceptance threshold is proposed.

One contract owner controls additions under `spec/results/` and their proposal
evidence. Non-goals: solver API changes, package/version changes, archives,
signatures, SSA, #29 cross-language acceptance, P06 governance, #42 provenance,
release authorization and parent epic closure. Subsequent implementation and
human implementation acceptance require a separate PR after ratification.

## Closed Julia/SciML payload

`backend` contains exactly `profile`, `solver`, `environment`, `evaluations`.
`solver.name` is `SciMLBase.solve`; `method` is `Tsit5` or `Rodas5P`.
These select `OrdinaryDiffEqTsit5.Tsit5()` or
`OrdinaryDiffEqRosenbrock.Rodas5P()` with no constructor keywords, as in #26.
`solver.options` contains every field below; no arbitrary keyword forwarding:

| Field | Required value and meaning |
|---|---|
| `dt` | null: automatic initial step (`dt=nothing`) |
| `adaptive` | true |
| `saveat` | `requested_grid`: use core `execution.time_grid` exactly |
| `save_start` | true iff first requested time is numerically zero |
| `save_end` | true |
| `save_everystep` | false |
| `dense` | false: no retained dense trajectory |
| `callback` | null: no callback |
| `force_dtmin` | false: no forced continuation at minimum step |
| `dtmin` | `backend_default`: omit the keyword; SciML's versioned minimum-step policy applies |
| `maxiters` | actual positive integer passed to solve; native #26 uses `typemax(Int)` |
| `jacobian` | `exact_inplace`: supplied `jac!` writes the one-state matrix entry `-beta` |
| `time_derivative` | `autonomous_zero_inplace`: supplied `tgrad!` writes `[0.0]` |

Both exact derivative functions are supplied through `ODEFunction{true}` to
**both** algorithms, including Tsit5 even if it does not use them. These labels
describe supplied functions, not observed invocation counts. No claim about
SciML's internal default linear solver or differentiation machinery is added.
Core `rtol`, `atol`, `max_step` map to `reltol`, `abstol`, `dtmax`; the problem
starts at zero and ends at the last requested time. All are positive finite
binary64; **the SciPy rtol floor applies only to Python-profile readback**.
Julia may fail numerically at small admissible tolerances under unchanged P04.

Core `evaluations.nfev` is the actual wrapper RHS-call count, including
initialization/interpolation, bounded by `execution.max_nfev`. Backend
`evaluations.njev` records `result.stats.njacs`; `evaluations.nw` records
`result.stats.nw`, **W-matrix constructions**, not SciPy LU decompositions.
Never relabel `nw` as `nlu`. Counters are observations, never inferred from method
names. `integration=skipped_zero_grid` iff the single grid time is zero; all
three counters then equal zero and no solver is called after ordinary validation.
Otherwise `integration=performed` and `nfev>0`. Solver/compiler failure propagates
without a successful record or partial substitute. Method options still describe
the selected configuration for a skipped integration.

Environment fields are nonempty strings: `julia_version`, `scimlbase_version`,
`ordinarydiffeqtsit5_version`, `ordinarydiffeqrosenbrock_version`, `json_version`.
Capture obtains actual runtime/module versions, including both solver packages
regardless of selected method. Producer name is provisionally `Fenix`, with its
actual installed version; capture emits `build_id:null` because no reliable
installed build identifier exists. Do not inspect Git, query a checkout or
network. Readback retains all recorded environment/producer observations,
including a non-null valid P07 opaque build ID, without substituting reader
versions or requiring matches. Such observations are not execution attestation.

## Numeric and transport rules

All P07 raw JSON, binary64, exact-byte checksums, timestamp, source correspondence
and cross-artifact relations apply unchanged. Extend integer-form decoding to
Julia's `njev`, `nw` and `maxiters`: exact integers only, excluding booleans,
fractional/exponent spellings and strings; counters nonnegative, limits positive.
Portable readback has **no native Int cap**, including for `maxiters` and
`max_nfev`; native capture preserves #26's existing Int constraints and records
its actual host-dependent `typemax(Int)`. Do not instantiate `ODEExecutionSpec`
while validating a portable record. Revisions retain P01's safe-integer range.
Signed zero, subnormals and rounding boundaries follow P07, with no JCS
normalization for these transport artifacts. Schema validation alone is
insufficient for lexical numeric rules or semantic relations.

Capture observes wall and monotonic clocks before source verification and after
result serialization/checksum, before manifest assembly. Use monotonic elapsed
seconds. Julia wall observations have millisecond precision, serialized with
zero padding to P07's six fractional digits; do not imply microsecond resolution.
Backward wall-clock adjustments remain valid.

## Proposed native boundary after approval

Add `Fenix.Results` with immutable `RunRecord`, `RunManifest`, `ODEResult` and
`ResultValidationError` (category and JSON Pointer path), exposing:

```julia
run_experiment(experiment, spec)::RunRecord
from_json(RunRecord, manifest_json, result_bytes;
          experiment, expected_manifest_sha256=nothing)
```

Only validated capture/readback factories construct records. No public arbitrary
trajectory attachment API. Nested storage is immutable, including exact integer
storage without embedded mutable BigInt objects. `to_dict` exports fresh values
and fresh BigInts; `to_json(manifest)` preserves original text;
`record.result_bytes` returns a fresh vector of original bytes. Snapshot caller
bytes before parsing/hash use. A private token-preserving PortableJSON path must
leave P01/P03's public behavior unchanged. Decode binary64 directly from tokens.

Capture revalidates the exact source pair, compiles it, normalizes a FIR copy,
executes once and preserves its own sample bits. Verified loading supports both
approved profiles after this supplement's ratification, recompiles supplied local
sources but never solves or resolves sources over a network. Check every source
reference even for same-FIR sources, exact result checksum, optional trusted
manifest checksum, FIR identity, settings/counters, bit-identical grids, zero-time
initial state, complete normalized interfaces, dimensions, units and direct
observable copies. P07's limits on authenticity and numerical claims still apply.

## Independent evidence and gate

The [synthetic examples](julia-examples/README.md) pair new Julia manifests with
**unchanged approved result bytes** for late, zero-only, empty and reordered
multi-observable cases. All counters, environments and timings are illustrations,
not execution receipts. The large-integer zero-only example deliberately exceeds
native Int and cannot be emitted by current native capture.

Read-only [Python](review_p07_julia.py) and [Julia](review_p07_julia.jl) audits
must independently check local schema references, fixed hashes, numeric fidelity
and bounded cross-artifact expectations without importing either production
results implementation or invoking a solver. Their receipts and review limits
are recorded in the [proposal evidence](../../../docs/verification/ep03-julia-results-profile.md).

Required later implementation evidence includes both algorithms through capture
and verified readback, all approved Python/newly accepted Julia examples, solver
entry-point traps during loading, malformed JSON, integer/sign/rounding boundaries,
mutation isolation, source/counter/unit/mapping/checksum failures and backward
wall-clock observations. Check all 40 approved analytical samples using both
methods at P04 baseline/refined settings; preserve capture sample bits through
transport without demanding identical independent reruns. Keep package tests
fixture-independent; use a separate pinned native results suite without load-path
overrides. Add only required standard libraries; refresh only the native test
lock through Pkg and preserve the independent reference lock/historical receipts.

**Gate: independent engineering/scientific review → explicit human PI ratification
of the exact proposal/schema/bounded expectations → separate native implementation
PR → separate human implementation acceptance.** Both PRs use `Refs #27`; neither
auto-merges nor closes the parent epic. This document records no approval.
