# ADR-P03 — M0 FIR normalization, JCS bytes and identity

**Status: RATIFIED by the human PI on 2026-11-14. Independent fixture approval remains pending.**

Issue [#14](https://github.com/DRAGGON-Lab/FENIX/issues/14), dependency
[#13](https://github.com/DRAGGON-Lab/FENIX/issues/13). Authority: D28–D29 in the
[decision index](../../../docs/approved-decisions.md), ratified
[P01](../../bioir/proposals/ADR-P01.md) and [P02](../../fir/proposals/ADR-P02.md).
This contract adds no native compiler, normalizer, semantic validator or solver.

## Ratified decision

Adopt canonicalization version `0.1.0` for P02 FIR model schema `0.1.0` only.
The [candidate catalog](../../../conformance/canonicalization/README.md) contains
review-required reference artifacts, not approved golden fixtures. P01 content
hashing and raw-input rules remain unchanged. No package runtime API is added.

## Input and validation boundary

Strict UTF-8 JSON is required. Reject a BOM, malformed UTF-8, unpaired surrogates,
duplicate decoded object keys (including escaped aliases), comments, trailing
commas, NaN/infinity literals and other JSON extensions. Check duplicates before
constructing dictionaries. Strings preserve Unicode scalar sequences exactly:
no NFC/NFD normalization or case folding. P02 ASCII identifier rules still apply.

Parse **every numeric token**, including integer-form tokens, directly to the
correctly rounded IEEE binary64 value, using round-to-nearest, ties-to-even.
Booleans are not numbers. Reject overflow to infinity and nonzero significands
that round to zero; accept exact zero even with an extreme exponent. Accept
finite subnormals. Signed zero is accepted and canonicalized as `0`.
Programmatic inputs must already be finite binary64 values (booleans excluded),
not arbitrary-precision integers or decimal objects awaiting implicit conversion.

Large integer tokens may round: `9007199254740993` and `9007199254740992` resolve
to the same value. `1000000000000000128` serializes as `1000000000000000100`,
which reads back to that same represented value. Identity concerns represented
binary64 mathematics, not the original decimal-real quantity. Higher precision
requires a future contract; numeric strings are not substitutes in this subset.
This intentionally differs from P01's integer-token bound; never apply this FIR
parser policy to BioIR source documents. Nonnegative state/rate restrictions
are checked on resolved values under P02. Primitive JCS examples with negative
numbers do not establish that those values are valid M0 quantities.

Validate P02 structure, references, uniqueness, roles, dimensions, mathematical
consistency and capabilities **before normalization**. Unsupported versions and
unknown model fields are rejected, never stripped. Validate compiler-produced
envelopes against their exact sources under P02 as a separate producer check,
including assignments, initial counts and exhaustive observables. A model digest
is not proof of source agreement, authorship, biological validity or executability.
Standalone mathematical FIR remains supported. Provenance cannot repair a model.

## Semantic pre-normalization N

Work on a copy of the validated model; preserve the immutable original. Sort only
these explicitly enumerated declaration arrays, ascending by decoded UTF-16 code
units, without locale-dependent comparisons:

| Collection | Key |
|---|---|
| `states`, `parameters`, `reactions`, `observables` | `id` |
| `equations` | `state` |
| `assumptions` | complete string token |

Reject duplicate IDs/roles/assumptions before sorting. Empty observables remain
empty. M0 has one state/equation; these ordering rules do not authorize additional
states. Preserve all other structure and every semantic field. Numeric spelling
and signed-zero equivalence are handled by binary64 interpretation and JCS.
No defaults, unit conversions, algebraic simplification, commutation,
reassociation, state renaming or network-isomorphism comparison is permitted.
In particular, observable IDs remain semantic; display labels do not replace them.
Unknown collections or future schemas require a versioned extension.

N is idempotent. Permuting declaration collections alone preserves normalized
bytes. Altering expression operands is not normalized into an accepted template.

## Exact bytes and digest scope

Serialize using [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), sections
3.1–3.2 and Appendices A/B: recursively sort object keys by unsigned UTF-16 code
units; preserve array order after N; use JCS primitive encodings, shortest
round-trip binary64 number spelling and prescribed string escaping. Emit UTF-8
without BOM, whitespace between tokens or a trailing newline. Never use Python
`json.dumps` as a JCS oracle. Distinguish two byte artifacts:

1. Model bytes: `JCS(N(model))`.
2. Identity bytes: JCS of the exact object below, with no additional fields:

```json
{"domain":"fenix.fir","canonicalization_version":"0.1.0","model":"<N(model) object, not a string>"}
```

The placeholder above denotes the actual normalized model object. The domain
and canonicalization version are literal strings. `model.schema_version` is
retained inside the model and is independent of the canonicalization version.
The identity wrapper is a hash preimage, not a FIR envelope or a model field.
The digest is lowercase hexadecimal SHA-256 over **identity bytes**, not model
bytes, source bytes, an envelope or a digest-containing object.

Only the complete semantic model and the fixed domain/version constants enter
identity. Provenance, compiler/source records, symbol maps, display labels and
ExecutionSpec are excluded. Execution configuration inside `model` is rejected.
GFP/LacI models and display-label variants with matching complete normalized
models share identity; changing an observable ID or a represented initial/rate
value changes the preimage. Unsupported units/capabilities are rejected rather
than assigned a supported M0 identity.

Canonical model bytes must read back under this same numeric policy and yield
the same bytes and identity. No P01 safe-integer check may be applied to them.
Changing the domain or canonicalization version defines a different identity
namespace; only the pair above is supported here. Unknown versions are rejected,
not guessed from input. Later contracts must state compatibility/migration;
existing bytes and identities must not be silently rewritten.

## Evidence and ratification gate

Expected normalized models are manually specified review candidates. Standard
JCS serialization and candidate SHA-256 digests are independently checked by
external Python `rfc8785` and an ECMAScript reference following RFC Appendix A
with required invalid-value guards. Neither is a FENIX compiler or normalizer.
An independent test now checks all six declaration-order invariants directly on
every catalog entry's expected normalized object, with coverage of every physical
normalized artifact, including shared references. Decoded strings are compared by
UTF-16 code units. Comparator probes include supplementary Unicode characters
only as test strings, without extending P02's ASCII identifier rules.

The initial serializers preserved incorrectly ordered observable arrays in two
expected models; successful serialization did not establish declaration ordering.
The new invariant failed on both before their candidate artifacts were corrected
to place `amount_x` before `another_amount`. Original inputs and scientific rules
are unchanged. The [correction evidence](../../../docs/verification/ep01-p03-proposal.md#ordering-correction)
records the regression and independent exact-byte checks.

Parser/normalization rejection expectations are documented but **NOT RUN**;
there is no native FIR parser/normalizer implementation in this change.
Native input-to-normalized transformation, complete semantic validation,
N idempotence and end-to-end FIR canonical round-trip tests remain **NOT RUN**
and required before implementation approval. Checkers never rewrite fixtures.

The RFC Appendix B expectations use published binary64 bit patterns and exact
strings. Other candidate bytes are externally serialized from reviewed expected
objects and cross-checked independently; they are not generated by the future
implementation under test. SHA-256 checks establish byte integrity, not science.

## Human ratification record

- Decision: **RATIFIED** for the M0 FIR normalization, JCS serialization and identity contract.
- Ratifying human PI: the approving repository user in this Codex conversation;
  no separate personal name was supplied.
- Reviewed revision: [`fdee54e5ebc5226c0a83810872311cc8cbbec3fd`](https://github.com/DRAGGON-Lab/FENIX/commit/fdee54e5ebc5226c0a83810872311cc8cbbec3fd).
- Approval recorded: **2026-11-14**, following review of that revision.
- Approval source: explicit user instruction in this conversation, transcribed
  below; no public approval URL was supplied.
- Independent scientific fixture approval and implementation approval: **PENDING**.

> ok I accept ADR-P03 please recorrd it and push it to the branch so I can merge it.

This ratifies canonicalization version `0.1.0` for P02 model schema `0.1.0`,
including the numeric/Unicode input policy, declaration ordering, JCS bytes and
domain/version identity wrapper. It does not approve the candidate reference
vectors as golden fixtures or approve native parser, semantic validator,
normalizer, compiler or solver implementations. The catalog remains
**REVIEW_REQUIRED**. Follow-on implementation and independent fixture review
remain separate gates; this record does not close issue #14 or merge its PR.
Future changes to these scientific rules require human PI approval of a revised
contract. Drafting-era paths remain stable for existing references.
