# BioIR/FIR rejection reference suite — review required

Issue [#17](https://github.com/DRAGGON-Lab/FENIX/issues/17), under ratified
[ADR-P01](../../spec/bioir/proposals/ADR-P01.md),
[ADR-P02](../../spec/fir/proposals/ADR-P02.md) and
[ADR-P03](../../spec/canonicalization/proposals/ADR-P03.md).
The [catalog](catalog.json) is **REVIEW_REQUIRED**. These concrete expectations
need human PI acceptance; passing reference checks does not approve package
validators, compilers, normalization, solvers or new scientific semantics.
Keep #17 open until the suite and its evidence are accepted.

## Scope and fixed expectations

The catalog registers 207 cases: the 92 existing P01 inputs, all 17 historical
P03 `contract_only` inputs, the 13 P03 FIR identity inputs, all 24 P02 examples,
and 61 additional cases. It references existing raw bytes by repository-relative
path and SHA-256, adding 56 raw inputs only for coverage gaps. No approved
fixture bytes or scientific schemas change. Canonical-only P01 inputs exercise
parsing here; their exact canonical bytes remain checked by the legacy runner.

Each case fixes its operation, raw-input contract, checksummed input/dependency
identities, outcome and contract rationale. A rejection specifies exactly one
stage, category, document identity and RFC 6901 JSON Pointer. `primary`,
`design`, `experiment`, `previous` and `request` identify distinct supplied
inputs; paths are relative to the identified document. Unlocatable malformed
syntax or UTF-8 uses the root (`""`). The `coverage` registry links requirements
to case IDs and rejects duplicate/unknown references. The loader also enforces
complete historical P03 and P02 coverage and rejects orphaned new inputs.

| Family | Reference checks |
|---|---|
| Duplicate IDs/keys | BioIR namespaces; decoded key aliases, nested objects, escaped pointers; FIR parameter/reaction/observable IDs and collection cardinalities |
| Broken revision digest | Corrupt envelopes, content changed with stale digest, exact Design ID/revision/digest, immutable revision checks and supplied-document identity |
| Invalid unit | Unsupported and wrong-role tokens in BioIR assignments, FIR state/rate/equation/observable declarations; no conversion |
| Missing port/reference | Species-scoped BioIR ports, typed FIR namespaces, exact supplied producer maps |
| Unsupported profile | Execution fields inside scientific documents, invalid M0 declarations, separate SSA rejection and ODE acceptance against the same valid FIR |
| Invalid event | Nonempty BioIR interventions and forbidden FIR events/interventions; no event semantics introduced |
| Positive controls | Standalone models, declaration permutations, zero rates, fractional initial counts, empty observables, exact source maps, metadata/display-label variants |

The categories `SCHEMA`, `DUPLICATE_KEY`, `DUPLICATE_ID`, `REFERENCE`, `UNIT`,
`DIGEST`, `DESIGN_REFERENCE`, `IMMUTABLE_REVISION`, `FUNCTION_ROLE`,
`STOICHIOMETRY`, `TEMPLATE`, `SOURCE_REQUIRED`, `SOURCE_DIGEST`, `SOURCE_ROLE`,
`SOURCE_VALUE`, `SOURCE_OBSERVABLE`, `UNSUPPORTED_PROFILE` and raw parsing
categories are reference-harness diagnostics. They establish one primary
expectation for each fixed input, without establishing a general precedence
contract for multiply invalid documents. State/equation arrays exceeding M0's
one-entry limit fail structure at the collection; duplicates in structurally
admissible parameter/reaction/observable collections fail at the repeated ID.
A wrong observable target fails typed model references before producer checks.

## Independent implementations and boundaries

[Python](reference.py) uses pinned `jsonschema` and `rfc8785` tools;
[Julia](reference.jl) uses pinned `JSONSchema`, `JSON` and its native P01 digest
reference. Neither imports a FENIX package or invokes the other language.
Both recognize exact P02 stoichiometry, flux and RHS templates; they never
execute expressions, approximate algebra or sample numerical values.
Role units plus schema constraints and exact templates establish dimensions.

The existing P01 entry points and 92-case observations are preserved. Internal,
opt-in parsing parameters add detailed numeric paths and P03 binary64 handling.
P01 retains its safe-integer-token bound. P03 parses every number token directly
to binary64, including integer spellings: `9007199254740993` is rejected by P01
and accepted as `9007199254740992` by P03. Both reject nonzero underflow and
overflow, accept exact zero with extreme exponents and finite subnormals, and
reject booleans where a numeric field is required.

Structural acceptance always uses the unchanged ratified schema through each
pinned schema library. A separate diagnostic expansion selects recognized
`kind`/`op` branches and obtains field paths from library errors. Missing and
unexpected members are identified from schema data, never exception prose.
Julia serializes its expanded diagnostic schema to remove shared object aliases
before the schema library resolves recursive expression references.

Operations are deliberately separate:

- `parse`: strict P01 or P03 raw-input checks only.
- `design`, `experiment`, `revision`: P01 structure and semantic checks, using
  exact local Design/previous documents. Dependencies are validated and identified
  independently before the primary document's semantic checks.
- `model`: standalone P02 mathematical validation under P03 input policy.
  This establishes model validity, without claiming source correspondence.
- `producer`: mathematical validation plus exact local P01 Design/Experiment
  validation, digest agreement, complete species/port/compartment and parameter
  maps, function roles, represented values, initial counts and exhaustive
  observables; supplied display labels must refer to declared observables.
- `capability`: validate a mathematical model, then evaluate a separate
  harness-only `{ "profile": "ode" }` or `{ "profile": "ssa" }` input.
  This is not an ExecutionSpec schema, solver or execution API.

No validation path repairs, normalizes or mutates scientific input. The
[ECMAScript audit](audit_inputs.cjs) independently verifies checksums and JCS
content digests for every BioIR document used by these cases. Only explicitly
intended digest failures may retain stale digests. This prevents unrelated digest
errors from masking semantic mutations.

## Run and compare

From the repository root, with the locked environments installed:

```sh
uv sync --project packages/python --locked
julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/rejections/tests -v
julia --project=conformance/julia conformance/rejections/tests/test_reference.jl
julia --project=conformance/julia conformance/rejections/tests/test_harness.jl
uv run --project packages/python --locked --offline python conformance/rejections/review.py --report artifacts/rejections-python.json
julia --project=conformance/julia conformance/rejections/review.jl --report artifacts/rejections-julia.json
uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare artifacts/rejections-python.json artifacts/rejections-julia.json
node conformance/rejections/audit_inputs.cjs
```

Version 1 reports retain runtime/dependency identities and SHA-256 fingerprints
of the catalog, catalog schema, ratified schemas/contracts, evaluators, dependency
locks and historical catalogs. Comparison requires exactly the registered Python
and Julia implementations in that order, one unique row per case, current
provenance and exact fixed expected diagnostics. Mutually agreeing incorrect
reports fail. Reports are reproducibility evidence, not authenticated execution
attestations. Runtime identities must match CPython 3.12 / Julia 1.10.13 and the
locked direct reference dependencies.

Both writers reject report paths inside the repository except `artifacts/`,
and reject symlink/hardlink aliases of protected source, schema or fixture files.
Native CI jobs test and upload reports separately; a dependent locked Python job
compares them and runs the digest audit. The tests include corrupt catalogs,
missing dependencies, unsafe paths/checksums, orphaned inputs, missing/extra/
duplicate report rows, stale fingerprints and wrong diagnostics/identities.

[Verification and remaining acceptance](../../docs/verification/ep01-rejections.md)
records executed commands and bounded claims. The approved P03 catalog is
unchanged: its 17 historical `NOT_RUN` rows remain historical evidence; new
execution results appear only in this suite.
