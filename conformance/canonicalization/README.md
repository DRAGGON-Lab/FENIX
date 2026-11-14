# P03 candidate serialization evidence — REVIEW REQUIRED

The [PROPOSED ADR-P03](../../spec/canonicalization/proposals/ADR-P03.md) defines
candidate M0 FIR normalization and identity. Nothing here is an approved golden
fixture, production FIR implementation or PI signoff. Existing P01/P02 fixtures
are unchanged. This catalog is separate from P01's stricter numeric token policy.

`catalog.json` is checked against `catalog.schema.json`. Every case names its
stage, exact input bytes/checksum, expected outcome and reference. Canonical
artifacts are exact UTF-8 bytes without terminal newlines; their `sha256` fields
are fixed expected digests. For `fir_identity`, `normalized` is a manually
specified expected model; `model_canonical` is its JCS encoding and `canonical`
is the version/domain wrapper's JCS encoding. Its checksum is the **candidate
FIR digest**. Binary64 input files contain published hexadecimal bit patterns,
not JSON numbers; other `.input` files preserve original bytes, including invalid
UTF-8. All expectation changes require review; no regeneration command is shipped.

## Stages and limits

- `binary64_jcs`: all RFC 8785 Appendix B rows, including nonfinite rejection.
- `json_jcs`: standard serialization of JSON values, including Unicode ordering,
  escaping, numeric rounding and lone-surrogate rejection.
- `fir_identity`: serialize the supplied expected normalized model and wrapper.
  A separate test inspects every catalog entry's expected model for declaration
  ordering across all six collections, using decoded UTF-16 code units and the
  ADR's keys. It also requires every physical expected normalized artifact to be
  referenced and inspected; multiple cases may share one artifact. These checks
  verify ordering invariants on expected objects and exact candidate bytes/digests.
  Native input-to-normalized transformation, complete semantic validation,
  normalization idempotence and end-to-end FIR canonical round trips are **NOT RUN**.
- `contract_only`: proposed FIR parsing/validation outcomes, **NOT RUN**. This
  includes duplicate decoded keys, malformed input, overflow/underflow, unsupported
  versions, duplicate IDs and P02 role/equation/reference/capability failures.

Source provenance in mathematical identity examples is not an assertion of
compiler-output validation. Changed rate/initial/observable models use standalone
FIR. Every mathematical model must independently meet P02 before a future
normalizer accepts it. No solver, statistical or biological validity is claimed.

The RFC Appendix B strings are transcribed published references, not output from
our checkers. Other candidate bytes were prepared with external `rfc8785` from
explicitly authored expected objects, then checked independently with ECMAScript
primitive serialization and UTF-16 property ordering. SHA-256 is checked by both
Python hashlib and Node crypto. These checks do not ratify the normalization
choices or prove arbitrary parser correctness. Unicode primitive cases are not
extensions to P02's ASCII semantic identifiers. Array order changes here belong
to explicit FIR pre-normalization; JCS itself preserves array order.

The initial serialization checks missed reversed observables in the two-observable
permutation pair: both tools faithfully serialized the same incorrectly ordered
expected arrays. The added ordering invariant caught both fixtures independently
of serialization. Their corrected expectations place `amount_x` before
`another_amount`; the original inputs remain distinct and unchanged. The Unicode
comparator probes are test-only strings, not new valid FIR identifiers. See the
[appended correction record](../../docs/verification/ep01-p03-proposal.md#ordering-correction)
for the failing regression, corrected digests and verification commands.

## Reproduce from the repository root

Use existing locked development environments, Python 3.12/uv 0.11.29 and Node 24:

```sh
uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --report /private/tmp/fenix-p03-python.json
node conformance/canonicalization/review_p03.cjs --report /private/tmp/fenix-p03-node.json
uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --compare /private/tmp/fenix-p03-python.json /private/tmp/fenix-p03-node.json
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v
```

Reports identify catalog bytes, implementation, each case's serialization result
and the unexecuted FIR validation/normalization stage. Comparison checks every
row against expected artifacts, rejects stale/incomplete/duplicate reports and
never converts NOT RUN into PASS. It requires two distinct reference tools.
Neither checker imports a FENIX compiler or invokes the other reference tool.

Sources: [RFC 8785 sections 3.1–3.2, Appendices A/B](https://www.rfc-editor.org/rfc/rfc8785.html),
ratified [P02](../../spec/fir/proposals/ADR-P02.md), and the explicit proposed
P03 choices. [Executed review evidence](../../docs/verification/ep01-p03-proposal.md)
records the source fingerprint and remaining gates. Native independent parser,
normalizer, idempotence and round-trip checks require ratification and follow-on
implementation review. Issue #14 remains open for human PI signoff.
