# Native Python M0 BioIR

Provisional distribution `fenix-bio`, module `fenix`, version `0.0.0`, pending
package governance ADR-P06. Python 3.12+; the runtime JCS dependency is `rfc8785>=0.1.4,<0.2`. Julia is not required.

`fenix.bioir` provides immutable, keyword-only dataclasses for the ratified
[P01 M0 subset](../../spec/bioir/proposals/ADR-P01.md). `DesignContent` and
`ExperimentContent` are **uncommitted content objects**. Construction validates
native values and local references. `to_dict()` returns fresh dictionaries/lists;
`to_json()` emits ordinary JSON with `allow_nan=False`, preserving declaration
order and accepted numeric values without sorting or normalization.
Successful construction or serialization does not establish committed document
validity. In particular, an Experiment can carry a syntactically valid but
incorrect Design digest when using the content-only API. Use the committed document API below to verify identity.

```python
from fenix.bioir import (
    Compartment, DesignContent, DesignReference, ExperimentContent, Function,
    InitialCount, Observable, Parameter, ParameterAssignment, Port, PortReference,
    Quantity, Species,
)

target = PortReference(species="x", port="amount")
design = DesignContent(
    id="production_decay", revision=1,
    compartments=(Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),),
    species=(Species(id="x", compartment="cell", ports=(Port(id="amount"),)),),
    parameters=(Parameter(id="alpha", unit="molecule/s"), Parameter(id="beta", unit="1/s")),
    functions=(
        Function(id="production", kind="constitutive_production", target=target, parameter="alpha"),
        Function(id="decay", kind="first_order_decay", target=target, parameter="beta"),
    ),
)

# Syntactically valid placeholder only: this API cannot commit or hash a Design.
claimed_reference = DesignReference(id=design.id, revision=design.revision, digest="0" * 64)
experiment = ExperimentContent(
    id="baseline", revision=1, design=claimed_reference, source_design=design,
    parameters=(
        ParameterAssignment(parameter="alpha", quantity=Quantity(value=10, unit="molecule/s")),
        ParameterAssignment(parameter="beta", quantity=Quantity(value=0, unit="1/s")),
    ),
    initial_counts=(InitialCount(species="x", quantity=Quantity(value=0.5, unit="molecule")),),
    observables=(Observable(id="amount_x", target=target),),
    interventions=(),
)
content_json = experiment.to_json()
```

All IDs, revisions, quantities and collections are explicit. Only fixed `kind`
and `schema_version` tokens have defaults. Collections require tuples of exact
native value types; lists, mappings and subclasses are rejected as nested values.
These strict boundaries are deliberate M0 reproducibility constraints. An
ergonomic builder layer remains future work and is outside this delivery.
`Quantity` accepts built-in `int`/`float` only, excluding booleans, nonfinite values
and integers outside `[-(2^53-1), 2^53-1]`. Quantities are nonnegative; compartment
volume must be positive. Exact units are `L`, `molecule`, `molecule/s`, `1/s`,
with role checks and no implicit conversion. Zero rates, fractional expected
counts, signed zero, positive subnormals and empty observables are accepted.

`source_design` is required validation context, neither stored nor serialized.
The reference ID/revision must match it; digest syntax is checked, but **digest
correspondence and trusted revision identity remain unverified**. Rebuilding an
Experiment (including `dataclasses.replace`) requires supplying `source_design`
again. Frozen content does not establish an archive of immutable committed revisions.
Issue #19 now makes verified Design content digests and exact ID/revision/digest
correspondence a high-priority gate before accepting committed Experiments.

Failures raise `BioIRValidationError(ValueError)` with `category`, `path` and a
readable message. Paths are JSON Pointers relative to the constructor that failed:
`Quantity(value=-1, unit="molecule")` reports `/value`; an unresolved function port
at Design construction reports `/functions/0/target/port`. Unknown keywords,
missing arguments and positional arguments retain Python's `TypeError`.
One primary diagnostic is returned; multiply invalid inputs have no universal
error precedence guarantee. Categories follow the applicable P01 reference names;
native nonfinite quantities use `NUMBER_RANGE` and oversized integers use
`INTEGER_RANGE`. Structural and role-local quantity violations use `SCHEMA`.

Raw JSON parsing, duplicate keys, malformed Unicode, token overflow/underflow,
canonical bytes/digests, envelopes and exact committed Design references are
handled by the committed document API delivered in [#19](https://github.com/DRAGGON-Lab/FENIX/issues/19). Python literals have already
lost raw-token information; e.g. an underflowed literal is indistinguishable from
zero at this boundary. No FIR, compiler, execution, results or wider BioIR support
is supplied. Accepted fractional counts do not establish SSA eligibility.

## Development checks

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v
uv run --project packages/python --locked --offline ruff check packages/python/src/fenix/bioir packages/python/tests/test_bioir.py packages/python/tests_native_content
uv run --project packages/python --locked --offline ruff format --check packages/python/src/fenix/bioir packages/python/tests/test_bioir.py packages/python/tests_native_content
uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml
```

Ruff targets Python 3.12 on the new code/tests. Strict mypy checks `fenix.bioir`
through the editable installation, with the shipped `py.typed` marker and no
blanket missing-import suppression. Configuration follows the
[official Ruff configuration](https://docs.astral.sh/ruff/configuration/) and
[mypy import guidance](https://mypy.readthedocs.io/en/stable/running_mypy.html).
Ruff, mypy and jsonschema are locked development tools; rfc8785 is a locked runtime dependency.

The separate native-content suite uses a test-only structural adapter and
`jsonschema` to check **29 content projections** from the approved 92-case P01
catalog. [Coverage](tests_native_content/coverage.json) lists all 63 deferred cases
and reasons. Detailed paths use the corresponding accepted rejection-suite
expectations, translating constructor locations and `/content` explicitly.
Metadata variants exercise content only. This is not full native 92-case
conformance, biological validation or implementation approval. Both original
catalogs and fixture bytes remain unchanged. The package tests run against an
editable install and a clean wheel without development dependencies in CI.

This evidence consists of approved fixed fixture projections and hand-authored
behavioral regressions. Systematic generated-input/property-based and metamorphic
validation has not been performed. It is tracked in
[#59](https://github.com/DRAGGON-Lab/FENIX/issues/59) following #19's raw parsing and committed identity delivery, without adding an acceptance blocker for #18 or selecting
a testing framework in this delivery.

## Committed documents and exact Design references

`DesignDocument`, `ExperimentDocument` and `Metadata` are frozen, slotted,
keyword-only values. They compute their read-only scientific digest and expose
strict JSON loading. The #18 content constructors remain uncommitted authoring.

```python
from dataclasses import replace
from fenix.bioir import DesignDocument, ExperimentDocument, Metadata

committed_design = DesignDocument(content=design, metadata=Metadata(name="Example"))
resolved_content = replace(experiment, design=committed_design.reference, source_design=design)
committed_experiment = ExperimentDocument(content=resolved_content, source_design=committed_design)
wire_json = committed_experiment.to_json()
loaded = ExperimentDocument.from_json(wire_json, designs=(committed_design,), expected_digest=committed_experiment.digest)
assert loaded.digest == committed_experiment.digest
```

`canonical_content_bytes()` returns direct RFC 8785 content bytes for SHA-256;
it excludes envelope digest and metadata and applies no FIR normalization.
`to_dict()` returns fresh envelope data; `to_json()` is ordinary JSON for transport.
These are distinct operations: a large valid floating token may canonicalize to
an integer spelling outside P01's input token bound. Canonical bytes are hash
material, not a promise of P01 readback. Ordinary envelope JSON round trips preserve
the scientific digest, including large integral floats, signed zero and subnormals.

`from_json(str | bytes, expected_digest=None, previous=None)` rejects malformed
UTF-8/JSON, duplicate decoded keys, invalid Unicode, numeric range/underflow,
missing/unknown fields and invalid content. Experiment loading requires an explicit
`designs` tuple of verified Design documents. Both envelope digests are checked,
and the exact Design ID/revision/digest must match; no network lookup, repair or
newer-revision substitution occurs. Errors use `BioIRValidationError` with
JSON Pointers relative to the input document, including `/content` where applicable.
Required and unknown native constructor arguments retain Python argument errors.

`previous` supplies the trusted predecessor for loading replacement content.
`replace_content(content)` checks against the current document's logical ID and
requires an explicitly higher revision when canonical content changes. Experiment
replacement can supply an explicit `source_design`, otherwise it uses the current
context. Old documents remain unchanged. `with_metadata(metadata)` returns a new
envelope with the same scientific identity; omitted metadata and an explicit empty
`Metadata()` object remain distinguishable. Snapshot/audit identities remain P07.

The document conformance suite exercises all 92 P01 cases and the 97 P01 cases
from the rejection catalog, with no claim for its 110 P03/FIR cases. Generic JSON
fixtures directly exercise private production parser/JCS helpers; envelope cases
use public loaders. The legacy root-only structural paths are coarsened only for
the original catalog comparison; detailed paths and supplied input identities
are checked separately. The 29-case content-only suite remains useful independently.

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v
```

### Guarantees and evidence limits

- **Digest validity is not provenance authentication.** Modified content with its
  correctly recomputed digest is self-consistent, but may differ from what a
  researcher authorized. The optional `expected_digest` permits comparison with
  a trusted external expectation; establishing that trust is the caller's
  responsibility. Signatures, archives and provenance auditing remain future work.
- **Revision integrity is predecessor-relative.** Checks against a supplied
  trusted `previous` document do not establish global revision history, prevent
  concurrent conflicting branches or guarantee storage of historical documents.
  Immutable in-memory values provide no persistence or authenticated archive.
- **Generated-input conformance remains outstanding.** Approved fixed cases and
  hand-authored regressions do not exhaust interactions between numeric parsing,
  canonicalization, revisions and references. Property-based and metamorphic
  investigation remains required future work under
  [#59](https://github.com/DRAGGON-Lab/FENIX/issues/59), without becoming a retroactive
  acceptance blocker for #19's bounded milestone.
- **Python serializer agreement is not fully independent.** Production and the
  Python reference both use `rfc8785`. Their serializer agreement alone is
  insufficient independent evidence. The
  [approved P01 expectations](../../conformance/bioir/README.md),
  [approved canonicalization vectors](../../conformance/canonicalization/README.md)
  and [executed Julia/Node comparisons and audits](../../docs/verification/ep02-python-documents.md#executed-outcomes)
  supply additional bounded evidence for this milestone, without establishing
  exhaustive serializer correctness or biological validity.

## M0 BioIR-to-FIR compiler

```python
from fenix.compiler import compile_experiment
from fenix.fir import FIRDocument, FIRModel, FIRValidationError

fir = compile_experiment(loaded)  # verified ExperimentDocument from above
assert fir.model.to_dict()["capabilities"] == {"ode": True, "ssa": False}
model_bytes = fir.model.canonical_model_bytes()
identity_bytes = fir.model.identity_bytes()
model_digest = fir.digest
standalone = FIRDocument.from_json(fir.to_json())
standalone.validate_sources(committed_design, loaded)
assert FIRModel.from_json(model_bytes).digest == model_digest
```

The compiler accepts an exact native `ExperimentDocument`, using its verified local
Design context. It binds the one species to FIR `x` and binds production/decay
function roles to `alpha`/`beta`, independently of source names and declaration
order. It emits precisely `alpha - beta*x`, the two reaction templates and signed
stoichiometry, resolved values/units, initial count, exact observable IDs, fixed
assumptions and `{ode: true, ssa: false}`. Empty observables stay empty. Volume
introduces no multiplier. Missing assignments fail BioIR validation; inputs are
never repaired or supplied with biological defaults. No solver or SSA eligibility
is implemented. An ODE capability declaration does not assert numerical solvability.

`FIRModel` and `FIRDocument` are immutable, with validated factory construction.
`from_json(str | bytes)` uses P03 binary64 parsing for every number token, including
large integer spellings; BioIR continues to use P01's safe-integer-token rule.
`from_dict` accepts explicit wire-shaped dictionaries, copies them into immutable
storage, and requires finite built-in floats for mathematical numeric fields
(including stoichiometry), excluding booleans and implicit int/Decimal conversions.
Compiler conversion of already validated BioIR quantities to binary64 is explicit.
All returned dictionaries are fresh. Malformed/unknown fields, duplicate IDs,
invalid roles/units/references/templates, reaction/equation disagreement and
unsupported capability declarations fail `FIRValidationError` with category and
FIR-envelope paths such as `/model/parameters/0/unit` or `/provenance/symbol_map`.
No general algebraic equivalence is inferred or executed.

`model.normalized()` returns an independently validated immutable model, sorting
only the six declaration collections specified by P03, using UTF-16 ordering.
Original declarations and expression operand order are preserved; normalization
is idempotent. `canonical_model_bytes()` is `JCS(N(model))`; `identity_bytes()` is
JCS of exactly `{domain: "fenix.fir", canonicalization_version: "0.1.0", model: N(model)}`.
The lowercase SHA-256 `digest` hashes identity bytes, not bare model bytes.
Canonical model bytes read back under P03 with identical bytes and identity.

Compiler envelopes include both source digests and complete state/parameter symbol
maps, plus compiler name/version. These records and optional observable display
labels are provenance and never enter FIR identity. Author metadata and execution
settings are not copied into the model. Observable IDs, initial values, rates,
units, assumptions and capabilities are semantic and do affect identity.
Standalone envelopes may omit provenance. To verify producer/source correspondence,
use `validate_sources(design, experiment)` or supply both `design=` and `experiment=`
to `FIRDocument.from_json`/`from_dict`; one context alone is rejected. A mathematical
model digest alone is not source agreement, provenance authentication, empirical
validation or proof that a solver exists.

The native FIR suite exercises all 207 approved rejection cases with categories,
paths and supplied-input identities, all 84 canonicalization catalog cases
(including 13 exact normalization/identity vectors), and accepted compiler/source
controls. These sets overlap; they do not establish exhaustive generated-input or
cross-language compiler parity. The Python reference shares rfc8785; approved fixed
bytes and independent Julia/Node evidence remain necessary. Original catalog rows,
including historical NOT_RUN statuses, remain unchanged; new native results are
recorded separately.

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v
```

### Compiler guarantees and evidence limits

- **Compiler correctness and solver correctness have separate gates.** #20 emits
  validated mathematics; it does not execute the ODE or compare library-produced
  trajectories against the analytical oracle. Existing production-decay oracle
  checks validate reference evidence. Numerical execution remains
  [#21](https://github.com/DRAGGON-Lab/FENIX/issues/21) under P04, followed by the
  independent scientific gate in [#29](https://github.com/DRAGGON-Lab/FENIX/issues/29).
- **FIR identity describes the resolved mathematical model.** Matching FIR means
  matching the complete resolved M0 mathematical model and its named observable
  interface. It does not establish identical experimental biological behavior.
  P01 BioIR declaration order remains identity-significant; P03 sorts only FIR
  `states`, `parameters`, `reactions`, `observables`, `equations` and `assumptions`.
- **Fixed conformance remains bounded.** The fixed tests do not exhaust
  interactions among numeric boundaries, declaration permutations and source
  mappings. Generated-input and metamorphic investigation remains outstanding
  under [#59](https://github.com/DRAGGON-Lab/FENIX/issues/59), with #20 as the
  prerequisite for its FIR/compiler portion. This follow-up does not retroactively
  block #20's bounded milestone or select a testing framework or dependency.

## M0 ODE execution

The ratified [P04 contract](../../spec/execution/proposals/ADR-P04.md) governs
`fenix.execution`. SciPy and NumPy are standard runtime dependencies; Julia is
not required. Execution accepts a validated `FIRModel`, including standalone
models. Compiler source verification remains separate.

```python
from fenix.execution import ODEExecutionSpec, solve_ode

settings = ODEExecutionSpec(
    time_grid=(0.0, 1.0, 10.0), method="DOP853",
    rtol=1e-10, atol=1e-12, max_step=1.0, max_nfev=100000,
)
trajectory = solve_ode(fir.model, settings)
assert trajectory.fir_digest == fir.digest
# Sample-major rows; columns align with state_ids and observable_ids.
counts = trajectory.state_values
```

Methods are exactly `DOP853` and `Radau`; Radau uses the analytical constant M0
Jacobian. Settings are explicit, frozen and keyword-only. Times must be a nonempty
tuple of finite nonnegative built-in floats in strictly increasing order; -0 and
+0 together are duplicates. Initial conditions apply at zero even if the first
requested sample is later. A zero-only grid returns the initial state after all
configuration/capability checks, without calling SciPy. Numerical settings require
positive finite built-in floats, `rtol >= 100*2**-52`, and a positive non-boolean
integer `max_nfev`. The budget counts RHS calls, not elapsed time or memory.
No numerical defaults, arbitrary solver kwargs, callback execution, method
switching or analytical fallback are exposed.

`ODETrajectory` is frozen with tuple-backed times, sample-major states and named
observables, units, settings, FIR digest, evaluation counts and NumPy/SciPy
versions. Empty observables have an empty row for every requested time. Backend
initial step selection is explicitly `None` (automatic). This standalone
in-memory output remains separate from the source-linked P07 capture API below.

**Numerical agreement is bounded; trajectories are not promised byte-identical.**
DOP853 showed small process-to-process bit differences even on the same host.
Local `rtol`/`atol` control estimates, not certified global error. The native tests
compare the approved 40-sample oracle at P04's absolute/relative acceptance bound
for both methods and two settings. This bounded corpus does not certify arbitrary
finite inputs, biological validity or the independent dual-language #29 gate.

**Every negative sampled count fails, however small.** The PI consciously accepted
that interpolation can cause rejection of a mathematically well-posed simulation.
There is no clipping. Ordinary binary64 underflow, including rounding to zero,
is allowed without a floor. Overflow, nonfinite output and failed/incomplete
integration fail explicitly; no successful partial trajectory is returned.

Invalid settings raise `ExecutionValidationError(ValueError)` with `category` and
field-relative `path`. Unsupported profiles use `FIRValidationError` with
`UNSUPPORTED_PROFILE` at `/profile`. Runtime `ODEExecutionError(RuntimeError)`
contains `category`, the frozen `spec` and actual `nfev`; categories distinguish
`WORK_LIMIT`, `NONFINITE`, `NEGATIVE_STATE`, `SOLVER_FAILURE` and `INVALID_OUTPUT`.
Programming errors are not caught by a blanket exception handler. The FIR's
mathematics, provenance, canonical bytes and digest remain unchanged by execution.

## Source-linked results and run manifests

The ratified [P07 contract](../../spec/results/proposals/ADR-P07.md) governs
`fenix.results`. Native implementation review remains pending under
[#22](https://github.com/DRAGGON-Lab/FENIX/issues/22).

```python
from fenix.results import RunRecord, run_experiment

record = run_experiment(experiment_document, settings)
manifest_json = record.manifest.to_json()
result_bytes = record.result_bytes

loaded = RunRecord.from_json(
    manifest_json, result_bytes, experiment=experiment_document,
    # Optional: expected_manifest_sha256=independently_trusted_sha256,
)
counts = loaded.result.state_values
```

Capture revalidates the exact committed Design and Experiment, compiles and
executes a normalized FIR copy, and records actual diagnostics, explicit solver
options, installed package/backend versions and UTC/monotonic timing. Failed
execution propagates the existing compiler/execution exception without a success
record. Zero-only grids skip integration after validation. `solve_ode` retains
its existing behavior and public trajectory type.

`RunRecord`, `RunManifest` and `ODEResult` are immutable validated values; use
capture or `RunRecord.from_json` to construct them. Typed result attributes use
tuples, including sample-major `state_values`/`observable_values`, named columns,
mapped `observable_state_ids`, units and times. Columns follow P03 normalized FIR
order. `manifest.to_dict()` and `result.to_dict()` return fresh dictionaries.
Callers own storage; no archives or filesystem helpers are provided.

Readback verifies strict JSON, field-specific numeric tokens, exact result-byte
SHA-256, full source references, recompiled FIR identity, settings, dimensions,
ordering, units and bitwise grid/observable correspondence. It never executes
the solver or replaces recorded environment observations. Original manifest text
and result bytes are retained, including formatting and final newlines. Use
`manifest.to_json()` for transport: signed-zero/subnormal binary64 values and
exact integer budgets/counters are preserved, including integers beyond Python's
decimal-string conversion limit. Generic JSON encoders may impose their own
integer limits.

`ResultValidationError(ValueError)` exposes `category` and a JSON Pointer `path`
prefixed with `/manifest` or `/result`. Invalid source context also rejects on
readback; capture preserves existing compiler and execution exceptions.

**Checksums establish consistency against supplied expectations.** A trusted
external manifest checksum detects alteration against that expectation. Without
it, plausible modified positive-time samples with recomputed checksums can pass.
Readback does not establish solver execution, numerical correctness, authorship
or biological validity. Repeatability remains bounded numerical agreement.
Capture records `producer.build_id = null` because this package has no reliable
embedded build identifier; readback preserves non-null recorded IDs. Build-ID
generation, Julia results, broader provenance (#42) and independent ODE evidence
(#29) retain separate gates.
