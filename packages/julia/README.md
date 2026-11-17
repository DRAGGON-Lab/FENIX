# Native Julia M0 BioIR content

Provisional package/module name `Fenix` and version `0.0.0` remain subject to
ADR-P06. The package implements uncommitted, immutable M0 content under ratified
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
stored or serialized. Digest integrity, committed envelopes, canonical JSON,
revision replacement and exact trusted Design resolution belong to #24.
Compiler, solver and result APIs are not implemented.

Constructors accept vectors or tuples and snapshot them into typed immutable
tuples. Nested values must use the native constructors. Exported dictionaries
and arrays are fresh copies. Declaration order is preserved. Fixed M0 kind and
schema tokens have defaults; IDs, revisions, quantities and interventions are
explicit. No unit conversion or scientific repair occurs.

Quantities accept finite `Float64` and built-in fixed-width integers within
`[-(2^53-1), 2^53-1]`, normalized to `Int64`; quantities must be nonnegative and
volumes positive. `Bool`, `Float32`, arbitrary precision and other numeric types
are rejected. Fractional expected counts, subnormals and negative zero are
supported. Raw lexical underflow and integer-token checks belong to #24 parsing.

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
deferred cases; this is not full native document conformance. JSONSchema remains
in the pinned reference environment. The library uses JSON.jl for ordinary JSON
serialization and keeps its generated Manifest untracked.
