# P01 reference catalog — approved

The human PI accepted all 92 registered reference expectations under
[ADR-P01 / BioIR M0 subset v0.1.0](../../spec/bioir/proposals/ADR-P01.md) on
2026-11-15. The catalog status is **APPROVED**. The reviewed catalog SHA-256 was
`6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390`;
only approval metadata changes after that review. See the
[acceptance record](../../docs/verification/ep01-p01-reference.md#human-pi-acceptance-recorded).

Approval covers **34 expected acceptances and 58 expected rejections**, including
five canonical-serialization expectations, binary64 bit patterns, and the declared
diagnostic categories and paths. It does **not** approve native FENIX
implementations, exhaustive input validation, compiler correctness, solver
correctness or future BioIR semantics. No native modeling package API is added.
P01 fixture acceptance and native implementation approval are separate decisions;
this record performs no merge or issue closure.

## Catalog contract

`catalog.json` is validated against `catalog.schema.json`. Every case names its
contract, operation, source bytes, SHA-256 input checksum, expected outcome and
reference. Inputs are committed `.input` files, including deliberately malformed
UTF-8 and JSON; readers must never pre-parse/reserialize them. Both independent
runners verify checksums and reject unknown catalog operations. No fixture
regeneration or expected-value update command is part of the test workflow.

Operations are `parse` (raw P01 JSON), `canonical` (P01's direct RFC 8785),
`design`, `experiment` (with an explicit local Design input), and `revision`
(with an explicit earlier Design). Revision checks compare against the supplied
trusted previous revision, not a mutable global archive. Envelope metadata
variants preserve scientific identity; changed content at the same or an older
revision is rejected. Neither parser invents missing data or resolves network
references. These are offline reference tools for controlled conformance inputs,
not hardened production ingestion APIs or native authoring builders.

Accepted parser cases specify JSON values or binary64 bit patterns; canonical
cases specify exact UTF-8 text. Integer-token limits are checked before rounding;
`9007199254740992` is rejected but the floating token `9007199254740992e0` follows
P01's binary64 policy. This deliberately distinguishes P01 raw-token rules from
unrestricted RFC 8785 number serialization and the separately ratified FIR
normalization contract.

Cases isolate faults. The catalog does not prescribe which error must win for
arbitrary documents with multiple independent defects. Structural failures use
category `SCHEMA` with root JSON Pointer `""`, since native `oneOf` diagnostics
vary. Semantic/reference failures provide the fault's JSON Pointer, including
zero-based array indices and standard `~0`/`~1` escaping. Native prose exception
messages need not match. Parser paths are asserted only where the catalog gives
one; categories always must match for rejections.

| Reference category | Meaning |
|---|---|
| `JSON_SYNTAX` | Invalid JSON grammar, including non-JSON NaN/infinity tokens |
| `INVALID_UNICODE` | Invalid UTF-8 or unpaired Unicode surrogate |
| `DUPLICATE_KEY` | Repeated decoded object key, including escape aliases |
| `INTEGER_RANGE` | Integer token exceeds P01's exact interoperable range |
| `NUMBER_RANGE` | Floating token overflows finite binary64 |
| `NUMBER_UNDERFLOW` | Nonzero floating input rounds to zero |
| `SCHEMA` | Structural/type/unit-token/version/subset violation |
| `DUPLICATE_ID` | Repeated identifier in a permitted collection |
| `REFERENCE` | Unresolved local species/port/parameter/compartment |
| `UNIT` | Declared quantity/parameter units do not match their role |
| `FUNCTION_ROLE` | Production/decay roles or rate parameters are not distinct |
| `DIGEST` | Claimed digest does not match canonical scientific content |
| `DESIGN_REFERENCE` | Experiment does not match the supplied exact Design |
| `IMMUTABLE_REVISION` | Replacement content reuses or rolls back a trusted revision |

These category names are accepted for the registered reference expectations;
this approval does not define a native package API or universal error precedence.

## Independent implementations and commands

Run from the repository root after the documented uv/Pkg environment setup:

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v
uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report artifacts/p01-python.json
JULIA_PKG_OFFLINE=true julia --project=conformance/julia conformance/julia/run_p01.jl --report artifacts/p01-julia.json
python conformance/compare_reports.py artifacts/p01-python.json artifacts/p01-julia.json
node conformance/reference/check_p01.cjs
```

Python uses its JSON decoder with token hooks and duplicate-preserving object
pairs, Draft-07 jsonschema and external rfc8785. Julia uses an independent raw
byte parser, JSONSchema and a local JCS reference encoder using Julia's Ryu
floating-point formatting. Neither calls the other or imports FENIX. Node is
only an independent reference check; it is not a dependency of either library.

Each report identifies the exact catalog SHA-256 and native runtime. Comparison
rejects incomplete/duplicate cases, stale catalogs, failed cases and disagreeing
categories; agreement on an incorrect category also fails against expectations.
CI produces both native reports separately and compares downloaded artifacts.

## Sources and review boundaries

Expectations come from P01's explicit parser/identity/unit/revision rules,
[JSON Schema Draft-07](https://json-schema.org/draft-07), and
[RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html) sections 3.1–3.2 and
Appendix B. Negative cases are authored mutations of the illustrative P01 pair.
Their scientific-content checksums were prepared with external rfc8785, not a
validator or FENIX compiler. Node independently checks the registered canonical bytes
and example digests. These checks do not prove all possible JCS behavior.

The explicit human approval covers the registered outcomes, canonical text,
binary64 bit patterns and declared diagnostic categories and paths. Future
expectation changes require their applicable scientific review; never weaken
expectations to match a failing implementation. Approval does not establish
exhaustive input validation or universal JCS correctness.
