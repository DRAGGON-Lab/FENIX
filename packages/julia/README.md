# Native Julia M0 BioIR documents and FIR compilation

Provisional package/module name `Fenix` and version `0.0.0` remain subject to
ADR-P06. The package implements immutable M0 content and committed documents under ratified
ADR-P01. It runs independently of Python, without SciML or Catalyst.

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
FIR compilation is available below; solver and result APIs are not implemented.

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
