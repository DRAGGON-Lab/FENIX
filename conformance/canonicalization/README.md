# P03 serialization reference evidence — APPROVED

The [ratified ADR-P03](../../spec/canonicalization/proposals/ADR-P03.md) defines
M0 FIR normalization and identity. The human PI approved the contract on
2026-11-14. The human PI accepted the concrete issue #16 serialization vectors
and reference tooling at reviewed revision `a58ea8345f0e2f641ba152b065ee3fa6d9dc0625`
on PR #55. The catalog is **APPROVED**; see the [acceptance record](../../docs/verification/ep01-canonicalization-vectors.md#human-pi-acceptance-recorded).
All 17 contract_only outcomes remain NOT_RUN. Native FIR parser/normalizer and
semantic validation approval remain separate gates. Existing P01/P02 fixtures
are unchanged; this catalog is separate from P01's stricter numeric token policy.

`catalog.json` is checked against `catalog.schema.json` by Python; Node mirrors
the catalog boundary constraints without dependencies. Every case names its
stage, exact input bytes/checksum, expected outcome and reference. Canonical
artifacts are exact UTF-8 bytes without terminal newlines; their `sha256` fields
are fixed expected digests. For `fir_identity`, `normalized` is a manually
specified expected model; `model_canonical` is its JCS encoding and `canonical`
is the version/domain wrapper's JCS encoding. Its checksum is the **expected
FIR digest**. Binary64 input files contain hexadecimal bit patterns (published
Appendix B rows plus the derived negative-infinity sign counterpart), not JSON numbers; other `.input` files preserve original bytes, including invalid
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
  verify ordering invariants on expected objects and exact reference bytes/digests.
  Native input-to-normalized transformation, complete semantic validation,
  normalization idempotence and end-to-end FIR canonical round trips are **NOT RUN**.
- `contract_only`: candidate FIR parsing/validation outcomes, **NOT RUN**. This
  includes duplicate decoded keys, malformed input, overflow/underflow, unsupported
  versions, duplicate IDs and P02 role/equation/reference/capability failures.

Source provenance in mathematical identity examples is not an assertion of
compiler-output validation. Changed rate/initial/observable models use standalone
FIR. Every mathematical model must independently meet P02 before a future
normalizer accepts it. No solver, statistical or biological validity is claimed.

The RFC Appendix B strings are transcribed published references. Issue #16 adds
17 executable vectors (16 raw JSON inputs and negative-infinity bits), whose
expected strings were explicitly authored from RFC 8785 and ratified P03 before
running either oracle. Existing inputs and expectations retain their exact bytes.
Earlier non-Appendix-B candidate bytes were prepared with external `rfc8785` from
explicitly authored expected objects, then checked independently with ECMAScript
primitive serialization and UTF-16 property ordering. SHA-256 is checked by both
Python hashlib and Node crypto. Human approval is recorded separately from these mechanical checks;
they do not prove arbitrary parser correctness. Unicode primitive cases are not
extensions to P02's ASCII semantic identifiers. The generic array/reversed-array pair preserves array positions while sorting
contained object properties. Only the six specified FIR declaration collections
are reordered by the expected FIR pre-normalization; JCS preserves array order.

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
node --test conformance/canonicalization/tests/test_review.cjs
```

The catalog/schema and both checkers accept `REVIEW_REQUIRED` and `APPROVED`
status metadata; reports must match the current catalog status. Unknown statuses
are rejected. Report format version `1` includes catalog/schema/evaluator SHA-256, the exact
registered implementation name, and runtime/serializer identity. Successful
rows carry actual `canonical_hex` bytes and `canonical_sha256`; FIR identity
rows also carry `model_canonical_hex` and `model_canonical_sha256`. Rejected and
unexecuted rows contain no canonical output. Every row names its catalog stage;
FIR validation/normalization always remains NOT_RUN.

Comparison requires exactly `external-python-rfc8785` and
`independent-ecmascript-rfc8785`, current source/catalog/schema provenance and
complete, unique case coverage. It ignores row order and matches every stage,
status, byte string and digest against the fixed artifacts. Two reports agreeing
on incorrect output fail. Runtime metadata is recorded and checked for the
registered runtime/serializer shape; hashes do not authenticate an execution.
Neither checker imports FENIX packages or invokes the other. Both retain direct
byte comparisons independently, reject orphaned fixture files and prevent report
writes to catalog/schema/evaluators or fixture directories, including symlink
and hard-link aliases.

The schema-validated `coverage` map links all nine issue #16 requirements to
executable IDs: UTF-16 ordering, signed zero, numeric spelling, exponent
thresholds, subnormals, nonfinite rejection, Unicode preservation, array order
and the binary64 integer boundary. Missing categories, unknown IDs, duplicate
IDs/references and coverage consisting solely of contract_only cases fail.
All 17 contract_only rows remain NOT_RUN. The [issue #16 verification record](../../docs/verification/ep01-canonicalization-vectors.md)
contains current commands, source/artifact identity and outcomes. The earlier
P03 evidence remains a historical record.

Sources: [RFC 8785 sections 3.1–3.2, Appendices A/B](https://www.rfc-editor.org/rfc/rfc8785.html),
ratified [P02](../../spec/fir/proposals/ADR-P02.md), and the ratified
P03 choices. [Executed review evidence](../../docs/verification/ep01-p03-proposal.md)
records the source fingerprint and remaining gates. Native independent parser,
normalizer, idempotence and round-trip checks remain NOT RUN and require follow-on
implementation review. The [human ratification record](../../spec/canonicalization/proposals/ADR-P03.md#human-ratification-record)
does not approve these vectors or close issue #14.
