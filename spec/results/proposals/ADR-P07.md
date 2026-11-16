# ADR-P07 — M0 source-linked ODE results and run manifests

**Status: PROPOSED. Not ratified; native implementation is blocked on explicit
human-PI acceptance of a reviewed revision.**

Issue [#22](https://github.com/DRAGGON-Lab/FENIX/issues/22); prerequisites #20
([merged #61](https://github.com/DRAGGON-Lab/FENIX/pull/61)) and #21
([merged #63](https://github.com/DRAGGON-Lab/FENIX/pull/63)). Baseline:
`b6beb5e`, merged main. Authority: D15/D16/D23/D24/D26/D28/D29 in the
[approved decisions](../../../docs/approved-decisions.md), ratified
[P01](../../bioir/proposals/ADR-P01.md),
[P02](../../fir/proposals/ADR-P02.md),
[P03](../../canonicalization/proposals/ADR-P03.md) and
[P04](../../execution/proposals/ADR-P04.md).

## Task contract and dependencies

One implementation owner controls `fenix.results` and its native tests after
ratification. This proposal owns only `spec/results/`, the specification index
and new proposal evidence under `docs/verification/`, plus a narrow `.gitignore`
exception to track `spec/results/`. Independent engineering
and scientific reviewers assess the proposal and later implementation; their
reviews cannot substitute for human approval.

Dependency graph: **P07 proposal and independent evidence → explicit PI
ratification → failing native tests → implementation → native/editable/wheel
verification → human implementation PR review**. #22 stays open until that
implementation is reviewed. #29 (independent ODE evidence) and #42 (broader
provenance) retain separate gates.

Non-goals: archives, filesystem storage helpers, network resolution, signatures,
authenticated provenance, researcher authorization, SSA, new biological rules,
new runtime dependencies and package/version governance under P06. Preserve
`solve_ode`, P04 failure/sampling behavior and every existing BioIR/FIR identity.
All examples, schemas and expectations here remain PROPOSED until accepted.

## Proposed artifacts and identities

Use two UTF-8 JSON artifacts, each schema version `0.1.0`:
[RunManifest](run-manifest-m0.schema.json) and
[ODEResult](ode-result-m0.schema.json). Every schema member is required;
unknown members and unsupported schema versions are rejected at every level.
There are no inferred defaults, optional metadata or executable values.

The manifest records exact Design and Experiment `schema_version`, `id`,
`revision`, `digest` references, plus FIR `schema_version`,
`canonicalization_version` and mathematical `digest`. Source digests retain
P01's content-only definition; FIR identity retains P03's domain/version wrapper
and excludes provenance and execution. Matching digest syntax or matching FIR
alone cannot establish source correspondence. Distinct BioIR documents can
compile to identical mathematical FIR.

`output.sha256` is lowercase hexadecimal SHA-256 of **the exact supplied result
bytes**, including whitespace, property order, IDs, units, values and any final
newline. `output` also declares result schema version, `application/json` and
`utf-8`. There is no normalized result identity, JCS transformation or digest
inside the result. Formatting changes change the checksum. A producer may choose
any conforming JSON formatting that preserves values. Readback retains and
returns the original result bytes; hashing a reserialized substitute is invalid.

The optional external expected manifest checksum similarly hashes the exact
UTF-8 manifest input bytes. For a string input these are its strict UTF-8 bytes.
Manifest JSON emitted by a loaded record retains that input text so its trusted
checksum remains verifiable. Neither checksum is a signature or execution
attestation. Without an independently trusted expectation, readback establishes
internal consistency only. Plausible altered samples with recomputed checksums
can pass; a trusted checksum detects alteration against that expectation.
Readback does not prove that a solver ran, numerical correctness, biological
validity, authorship or researcher authorization.

## Raw JSON and numeric fidelity

Require strict UTF-8 without BOM, valid JSON and Unicode scalar strings. Reject
malformed/truncated JSON, malformed UTF-8, unpaired surrogates (including escaped
ones), duplicate decoded object keys (including escaped aliases), trailing data,
comments, trailing commas, NaN/infinity literals and boolean-as-number coercion.
Do not normalize Unicode, sort IDs, repair fields or silently discard extras.

Apply **field-specific** numeric decoding, not blanket P03 binary64 parsing:

- Times, sampled values, tolerances, maximum step and elapsed seconds decode
  numeric tokens directly to correctly rounded binary64, nearest ties to even.
  Reject overflow, nonfinite values and a nonzero decimal significand that
  rounds to zero. Accept finite subnormals and exact zero with either sign.
  Preserve every represented bit, including `-0` / `-0.0`; transport serialization
  must preserve negative zero rather than applying JCS's zero normalization.
  Numeric strings are rejected. Ordinary solver arithmetic may underflow to
  zero under P04; rejecting a nonzero *serialized token* that rounds to zero
  does not forbid serializing that already represented zero.
- Revisions, `max_nfev`, `nfev`, `njev`, `nlu` require JSON **integer-form tokens**
  (no fraction or exponent) decoded as exact integers. Exclude booleans.
  Revisions retain P01's range 1 through 9007199254740991. Budgets are positive;
  counters nonnegative. Budgets and counters have no binary64 safe-integer cap:
  `9007199254740993` remains that integer. Reject `1.0` and `1e0` in these fields.

The structural schemas cannot check token form, signed-zero preservation,
correct rounding, finiteness or every semantic relation. Passing JSON Schema
alone is insufficient. JSON numbers in binary64 fields may use integer spellings;
their represented values follow binary64 rules regardless of spelling.

## Manifest fields and observations

- `kind = RunManifest`, `schema_version = 0.1.0`, `status = success` and
  `repeatability = bounded_numerical_agreement` identify the only supported case.
- `sources` and `fir` contain the exact references above.
- `execution` contains `profile = ode`, ordered `time_grid`, explicit `method`
  (`DOP853` or `Radau`), `rtol`, `atol`, `max_step` and exact `max_nfev`.
  Apply all P04 settings validation, including the relative-tolerance floor.
- `randomness` is exactly `{"rng":"none","seed":null}`. Deterministic M0 ODE
  uses no RNG; a seed is not applicable. Reject any fabricated seed, generator,
  replicate or stochastic setting, rather than silently ignoring it.
- `solver` records `name = scipy.integrate.solve_ivp`, the method and fixed
  options `first_step = null` (automatic selection), `vectorized = false`,
  `dense_output = false`, `events = null`. `jacobian` is `constant_exact` for
  Radau and `not_supplied` for DOP853. No callback or arbitrary keyword forwarding.
  Solver and execution method must agree. The backend version is in environment.
- `evaluations` records actual `nfev` (P04 RHS calls, including initialization
  and interpolation), `njev` and `nlu`. `nfev <= max_nfev`. Counters are observations,
  not reconstructed from timings or method names.
- `environment` records nonempty version strings for `python_implementation`,
  `python_version`, `fenix_bio_version`, `rfc8785_version`, `numpy_version` and
  `scipy_version`. These report the producer environment. Readback preserves
  them verbatim and does not replace them with the reader's installed versions
  or require a version match. This introduces no P06 compatibility policy.
- `timing` records `started_at_utc` and `finished_at_utc` in fixed
  `YYYY-MM-DDTHH:MM:SS.ffffffZ` form, with valid Gregorian dates and seconds
  00–59, plus finite nonnegative binary64 `elapsed_seconds`. Observe wall and
  monotonic clocks at the start, before source revalidation/compilation, and at
  the finish, after output serialization/checksum and before manifest assembly.
  Duration is the difference of the monotonic observations in seconds. Wall
  clocks can adjust: finish need not be later than start, and wall subtraction
  need not equal elapsed duration. Do not serialize absolute monotonic readings.
- `integration` is `skipped_zero_grid` exactly when the sole requested time is
  numerically zero (including negative zero). Then all three counters are zero
  and initial state is returned after normal validation, without a solver call.
  Otherwise it is `performed` and `nfev > 0`. Failed execution produces no
  successful run record, partial artifact or substitute analytical solution.

P04's bounded sample agreement remains the repeatability claim. There is no
guarantee of identical rerun bytes, even on the same host. Local tolerances are
not global error certificates. P07 adds no new acceptance thresholds.

## Result layout and cross-artifact validation

`kind = ODEResult`, `schema_version = 0.1.0`, `fir_digest` and `time_unit = s`
accompany ordered `times`, `state_ids`, `state_units`, `state_values`,
`observable_ids`, `observable_state_ids`, `observable_units`, `observable_values`.
Both value arrays are sample-major: one row for each time and one column per
corresponding ID. Each ID/unit array has the same length as its columns.

Resolve columns in normalized FIR declaration order (P03); never infer biological
identity from a column position. M0 has exactly state `x` with unit `molecule`
and representative-cell expected-count semantics under P02. Observable IDs,
mapped state IDs and units exactly match the complete compiled FIR observable
list in that order. Empty observables have empty ID/mapping/unit arrays and an
empty value row for every time. No implicit unit conversion is allowed.

Times follow P04: nonempty, finite, nonnegative and strictly numerically
increasing; -0 and +0 together are duplicates. Result times and manifest grid
agree **bit for bit**, including signed zero. Samples are finite and nonnegative;
negative zero is accepted. Observable values are bit-identical copies of their
mapped state samples. Where a sample time is zero, its state is numerically
equal to the compiled initial state (zero sign is not a new FIR distinction).
Positive-time sample values are not recomputed during loading.

Readback requires an exact supplied local `ExperimentDocument` with its verified
Design. Revalidate both committed content digests and the Experiment's full
Design reference under P01, compile under P02/P03, and check all manifest source
schema versions, IDs, revisions and digests against those exact documents.
Check the FIR version pair and mathematical digest in the manifest and result
against the compilation. Check settings, solver/options/randomness, counters,
grid, dimensions, IDs, units and complete direct observable correspondence.
Verify the result byte checksum and, when supplied, the external manifest byte
checksum. Any mismatch rejects the record; nothing is repaired. These checks
perform no network lookup and never execute the ODE.

## Proposed native Python boundary

```python
run_experiment(experiment: ExperimentDocument,
               spec: ODEExecutionSpec) -> RunRecord

RunRecord.from_json(manifest_json: str | bytes, result_bytes: bytes, *,
                    experiment: ExperimentDocument,
                    expected_manifest_sha256: str | None = None) -> RunRecord
```

`run_experiment` revalidates the exact committed source pair, compiles and
executes it, then captures a successful record in one operation. Preserve
existing solver exceptions and no-success-on-failure behavior. There is no
convenience API attaching arbitrary caller trajectories to digest strings.

`RunRecord.manifest` is a validated immutable `RunManifest`; `RunRecord.result`
is a validated immutable `ODEResult`. Use validated factories with immutable
nested storage and fresh `to_dict()` values. `manifest.to_json()` exposes the
manifest text; `record.result_bytes` exposes exact immutable result bytes.
Validation failures expose a category and JSON Pointer path identifying the
artifact/field. Malformed expected checksums also reject. Callers own all
filesystem storage. `solve_ode` remains available for standalone FIR execution;
its existing public trajectory type is unchanged.

## Evidence, alternatives and acceptance gate

The [hand-prepared examples](examples/README.md) use existing source documents,
approved FIR identity artifacts and selected approved analytical expectations.
Synthetic manifest counters, environment and times illustrate structure; they
are explicitly not execution receipts. A separate transport-only vector probes
signed zero, finite subnormals, largest finite binary64 and exact large integers.
The [read-only audit](review_p07.py) imports no FENIX production modules. It
checks structure, byte hashes, binary64 bits and reference correspondence; it
never rewrites examples or produces golden numerical values from the solver.
Independent system SHA-256 checks supplement the Python checksum audit.

Alternatives rejected for this bounded proposal: JCS result normalization loses
signed zero and obscures exact-byte artifact identity; FIR-only manifests cannot
distinguish different source contexts; accepting arbitrary trajectories weakens
the capture boundary; archives and signatures add unrelated lifecycle/trust work.
The chosen exact-byte scheme requires preserving transport bytes and explicitly
does not authenticate the recorded execution.

Before implementation: human PI must explicitly ratify the reviewed contract,
schemas and bounded candidate reference expectations by revision. Before
implementation approval: native tests cover both methods through capture and
readback, all raw JSON failures, binary64 and exact integer boundaries, wrong
same-FIR sources, units/IDs/dimensions/grid/observables, preserved environment,
immutability, solver failure, skipped/late grids, unchanged source/FIR identities,
trusted checksum behavior and proof loading never calls a solver. Run the
package/native suites, harness/link checks, Ruff, strict mypy, distribution build
and complete clean-wheel package suite with locked runtime dependencies only;
extend CI's explicit lint targets and ordinary package discovery. Record exact
commands, versions, input/artifact hashes and PASS/FAIL/NOT RUN outcomes in new
evidence; preserve original receipts and accepted fixtures.

**Human PI ratification: PENDING. Native implementation and its tests: NOT RUN.**
