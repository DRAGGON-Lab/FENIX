# Scientific conformance fixtures — pending

Planned independent analytical production/degradation reference, invalid/unsupported-model cases, canonicalization vectors, community conservation, numerical validation and restricted SSA distribution-level tests. Golden expectations require human scientific approval; neither compiler may solely generate its own expected values. Passing package smoke tests is not scientific conformance.

Development tools are available through Python's locked development group and
the separately pinned [Julia environment](julia/README.md). These environments
provide tooling only; no normative fixtures or scientific validators exist yet.

## Parser and validator fixture catalog gate

ADR-P01 is [ratified](../spec/bioir/proposals/ADR-P01.md). Before parser/validator
implementation approval, a reviewed language-neutral fixture catalog must make
its raw-input and validation requirements executable as acceptance checks.
This follow-on work belongs principally to
[#16](https://github.com/DRAGGON-Lab/FENIX/issues/16) for canonicalization vectors
and [#17](https://github.com/DRAGGON-Lab/FENIX/issues/17) for parser, validation
and rejection fixtures. This records the gate; the catalog is not yet published.

- Each fixture must identify its stable case ID, applicable contract/version and
  operation or validation stage, original input, explicit accept/reject outcome,
  and independent reference or rationale for that expectation.
- Preserve exact source bytes or an explicitly encoded byte representation.
  Duplicate keys, invalid UTF-8/Unicode and numeric token spellings must survive
  loading the catalog; do not store only an already-parsed JSON object.
- Cover duplicate keys, valid/invalid Unicode, negative zero, nonzero underflow,
  binary64 precision and rounding, finite/nonfinite boundaries and integer-token
  limits. Include positive and negative cases where applicable. Accepted cases
  must specify the relevant expected value or canonical bytes when those are
  part of the operation being tested.
- Define stable language-neutral rejection categories per case, distinguishing
  parsing, schema and semantic/reference/capability failures as applicable.
  Record expected document paths where meaningful. Native exception types or
  prose messages need not match; the declared categories and outcomes must.
- Python and Julia must independently process the same original inputs and each
  match the catalog's expected results. Neither may delegate parsing/validation
  to the other or generate the expected results from the implementation under
  test. Record both reports and any discrepancy before implementation approval.
- Keep P01's raw-token policy distinct from pure RFC 8785 serialization and from
  pending P03 FIR normalization. Review and approve expectations under their
  applicable contracts before publishing normative fixtures; do not infer new
  semantics to fill a missing expectation.

The catalog review and both native reports are required evidence. Existing
JSON Schema example probes and package smoke tests do not satisfy this gate.
