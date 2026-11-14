# ADR-P01 — M0 BioIR Design and Experiment documents

**Status: PROPOSED — not ratified; not a normative contract.**

Issue: [#12](https://github.com/DRAGGON-Lab/FENIX/issues/12), parent
[EP-01](https://github.com/DRAGGON-Lab/FENIX/issues/3).
Authority: [approved decisions](../../../docs/approved-decisions.md), especially
D02–D05, D09, D15–D16 and D26. This proposal does not change those decisions.
The human PI must approve the exact proposal before semantic validators,
public APIs or normative fixtures are implemented. No approval is recorded here.

## Decision requested

Adopt the accompanying [candidate schema](bioir-m0.schema.json) and the rules
below as BioIR `0.1.0`, limited to a single representative cell with constitutive
production and first-order degradation of one molecular species. Experiments
have fixed parameters and initial counts. The schema version is proposed;
package names, package versions and compatibility governance remain ADR-P06 work.

The JSON Schema describes structure only. Cross-document references, uniqueness,
units relative to parameter roles, digest integrity and execution eligibility
need separate checks after ratification. A schema-valid document alone is not a
valid executable biological model.

### Documents and identities

Both documents have an envelope containing `content`, `digest` and optional
`metadata`. `content` is scientific; `metadata` is descriptive provenance only
and cannot supply missing scientific fields. The entire committed document is
immutable. Editing content creates a new revision; historical revisions remain
available. Metadata variants cannot alter the scientific revision or its meaning.

Content includes `kind`, `schema_version`, `id`, and `revision`. IDs are local,
case-sensitive ASCII identifiers matching `[A-Za-z][A-Za-z0-9_-]*`, at most 64
characters. IDs carry no biological meaning. Human-readable Unicode names belong
in metadata. Revision numbers are positive integers through `2^53-1`; they
increase when replacing a revision of the same logical ID. No timestamps,
implicit defaults, generated identifiers or implicit unit conversions enter
content. Every array position is significant for BioIR content identity.

**Proposed digest rule:** lowercase hexadecimal SHA-256 over the UTF-8 RFC 8785
JCS encoding of the entire `content` object. The `kind` and `schema_version`
inside that object provide document-domain and version separation. The digest
and metadata envelope fields are excluded. This definition uses RFC 8785
directly, without a FENIX normalization step; it is independent of the later
FIR-specific ADR-P03. Do not use `json.dumps(sort_keys=True)` as its reference.

A resolver receives a document and a caller-supplied local Design collection.
It verifies content integrity before resolving references. It must not fetch a
Design over the network, accept a matching ID with a different digest, substitute
a newer revision, or repair inputs. Experiment Design references include the
exact Design ID, revision and digest; all three must match. Experiment content
is hashed by the same rule, including that exact reference.

### Design content

- One compartment has `kind: representative_cell`, a stable ID and strictly
  positive volume explicitly in litres. The volume does not rescale counts or
  rates in M0. Growth and changing cell volume are unsupported.
- One molecular species references that compartment and declares one port with
  `kind: molecular_count`. Its deterministic amount is the expected number of
  molecules per representative cell, not population-total molecules or a
  concentration. Fractional expected counts are allowed.
- Parameters declare IDs and units. One production-rate parameter uses
  `molecule/s`; one degradation-rate parameter uses `1/s`. These unit spellings
  are proposed exact serialized tokens. Cell scope is carried by the referenced
  compartment, not an implicit population multiplier.
- Exactly one `constitutive_production` function and one `first_order_decay`
  function reference the species and port and their respective rate parameter.
  The port is an amount reference, not an executable callback or serialized
  equation. General expression syntax belongs to ADR-P02.

All compartment, species, port, parameter and function IDs are unique within
their respective collections. Port IDs are scoped to their species. Every
reference resolves in its declared namespace. Functions must target the same
species and its declared port, and must reference distinct parameters with the
units required by their role. Unused or extra parameters are rejected in M0.

### Experiment content

An Experiment contains its exact Design reference and a requested
`profile: m0_ode`, explicitly a proposed capability identifier. It supplies one
quantity-valued assignment for each declared parameter and exactly one initial
count for the declared species. Assignment IDs must be unique and exhaustive.
Rate values and initial counts must be finite and nonnegative. Assignment units
must match their Design declarations exactly; initial counts use `molecule`.

Direct observables reference the species and its amount port. Observable IDs
are unique; an empty observable list is permitted. `interventions` is required
and empty. There is no time grid, solver name, numerical tolerance, RNG setting,
replicate count or run manifest here: those belong to ExecutionSpec/results.

No SSA eligibility follows from this ODE profile. M0 accepts zero production,
zero decay and zero initial count. The proposed function meaning is constant
production at rate alpha and first-order loss at rate beta times current count;
ADR-P02 must encode this in FIR and #15 must establish independent mathematical
references. This document does not ratify those later artifacts.

### Parsing and unsupported input

Reject unknown content fields and unsupported versions rather than guessing.
Parse strict UTF-8 JSON, rejecting duplicate object keys before conversion into
a dictionary, invalid Unicode, NaN/infinities and numeric overflow. Represent
scientific values as finite IEEE binary64 numbers; booleans are not numbers.
Reject integer tokens outside the exact interoperable range `[-(2^53-1),2^53-1]`
before rounding. Decimal/exponent tokens follow correctly rounded binary64
parsing; nonzero inputs rounded to zero are rejected. Negative zero is accepted
as zero and serialized by JCS as `0`. The candidate JSON Schema cannot establish
these raw-token checks. FIR numeric normalization still requires ADR-P03.

Reject additional compartments/species, extracellular or population accounting,
concentration units, transport, nonlinear rates, scheduled events, concentration
observables and executable payloads. Future BioIR versions may describe more
biology; this M0 proposal makes no claim to support those features.

## Alternatives and consequences

1. **Minimal M0 contract (proposed):** gives both native implementations a small,
   auditable target; wider biology requires a later reviewed version/profile.
2. **Broad BioIR now:** could represent nested communities, events and arbitrary
   typed expressions immediately, but introduces scientific choices beyond the
   agreed M0 scope and delays independent verification.
3. **Hash source JSON bytes:** simple to implement, but harmless whitespace or
   object-key changes would change revision identity; rejected in favor of JCS.

ASCII IDs avoid unresolved identifier normalization while preserving Unicode
annotations. Array order remains identity-significant even when a later compiler
could produce the same FIR from reordered declarations. This proposal does not
assert algebraic equivalence or freeze future native builder APIs.

## Candidate examples and validation acceptance

The paired [Design](examples/design.json) and [Experiment](examples/experiment.json)
are **proposal examples, not approved golden fixtures**. Their example digests
were calculated by the external `rfc8785` development tool, not a FENIX compiler.
They require independent verification and PI approval before normative use.

After ratification, Python (`jsonschema`) and Julia (`JSONSchema`) must separately
validate structure and implement the semantic checks above, without calling each
other or importing a FENIX compiler. No remote schema resolution is allowed.

| Case | Expected outcome after ratification |
|---|---|
| Paired examples, ordinary positive rates | Accept; resolve the exact Design |
| Zero rate(s), fractional initial expected count, empty observables | Accept |
| Whitespace/object-key order changes | Preserve digest |
| Content mutation with old digest | Reject document integrity |
| Correct Design ID but different revision or digest | Reject Experiment reference |
| Duplicate raw key or collection ID | Reject before ambiguous lookup |
| Missing port, unknown parameter or wrong parameter role | Reject reference with document path |
| Concentration units or negative/nonfinite quantity | Reject quantity with document path |
| Nonempty interventions or unsupported profile | Reject capability |
| Unknown content field/version or executable callback | Reject without repair |

The full candidate case list becomes reviewed fixtures only after ratification.
Expected error paths use JSON Pointer and rejection categories; identical prose
messages between languages are not required. Fixture publication is #17 work.

## References and evidence limits

- [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html): sections 3.1–3.2 and
  Appendix B govern JCS, Unicode and numeric serialization.
- [JSON Schema Draft-07](https://json-schema.org/draft-07): structural assertions;
  reference integrity and physical units are outside its general guarantees.
- [FENIX architecture](../../../ARCHITECTURE.md): per-cell count accounting,
  separation of biological intent, mathematical FIR and runtime settings.

Two validator implementations are evidence of portability, not independent
biological validation. Package smoke checks do not establish these semantics.
This PR must not close #12 or claim ratification before the required review.

## Human ratification record

- Decision: **PENDING**
- Ratifying human PI: **not recorded**
- Reviewed commit/revision: **not recorded**
- Review date and durable approval link: **not recorded**
- Independent scientific/reference reviewer and evidence: **not recorded**

Approval must cover document boundaries, identity bytes, identifiers, numeric
policy, exact unit tokens, function meanings and capability limits. Changes to
any of these require an explicit revision to this proposal before approval.
