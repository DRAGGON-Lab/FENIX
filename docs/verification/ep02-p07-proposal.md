# EP-02 / #22 — P07 contract proposal evidence

**PROPOSED; explicit human-PI ratification is pending. No native P07 API exists.**

Baseline: `b6beb5e` (merged #63, including #21's binary64 output correction).
Date: 2026-11-16. This delivers the contract/evidence stage of #22 only.
Issue #22, its parent epic, #29 and #42 remain open. No production package,
dependency lock, approved fixture or historical receipt/report is changed.

The [proposal](../../spec/results/proposals/ADR-P07.md) defines exact verified
source references, existing FIR identity, exact-byte result checksums,
field-specific numeric fidelity, capture/readback boundaries and evidence limits.
Its [candidate examples](../../spec/results/proposals/examples/README.md) are
synthetic transport/reference illustrations, explicitly not execution receipts.
The independent [audit source](../../spec/results/proposals/review_p07.py) imports
no FENIX code and does not call a solver or write examples.

## Fixed evidence and observed correction

Three candidate artifact pairs cover late-first sampling, a signed-zero zero-only
grid, empty observables, both method-option declarations and an exact work budget
greater than 2^53. Three positive-time sample values are roundings of the already
approved `baseline-zero` oracle; two zero-time examples use exact initial counts.
Eight separate binary64 transport probes cover signed zero, subnormals, the
normal boundary, largest finite binary64 and integer-form rounding. Integer
transport probes preserve exact values beyond binary64's safe-integer range.

The initial rational-nearest audit **FAILED**: the manually entered 1-second
candidate token `9.516258196404043` decoded as `40230852fe8bb1d3`, one ULP above
the nearest binary64 to the approved decimal. The candidate was corrected to
`9.516258196404042` (`40230852fe8bb1d2`), its candidate output checksum and manifest
were refreshed, and the unchanged rational-nearest check passed. No accepted
oracle, executor, threshold or scientific rule was changed to admit the example.

The scientific review's independent ECMAScript identity audit also **FAILED**
for the initial empty-observable candidate: preparation and the first Python
audit sorted only assumptions, omitting P03's reaction ordering. The erroneous
candidate digest `8fd86d529fac2ec4a3a10b5322276d3f50d7527eecbcbf26b948df8542e94c01`
was replaced with the independently confirmed normalized identity
`817e3383baa507ed0b727c8fa563d6040b965829c0f940a21a612a3b847627cb`.
The audit now explicitly sorts all six P03 declaration collections. Only
proposed empty-result/manifest bytes and their candidate checksums changed;
existing P03 rules and approved artifacts remain unchanged. This illustrates
why serialization/checksum agreement alone is insufficient scientific evidence.

The audit checks exact SHA-256 bytes, independent external JCS source-content
digests, existing FIR identity correspondence, exact observable copies and
selected schema rejections. It derives binary64 rounding intervals with exact
rational arithmetic from IEEE exponent/significand fields, including the largest
finite value's upper boundary. A formatting-only change preserves the decoded
object while changing its checksum. The retained
[JSON audit](p07-candidate-audit.json) identifies the source artifacts by SHA-256.
An independent system `shasum` check is retained in
[byte checksums](p07-byte-checksums.txt).

These checks cover fixed examples and mutations, not a general raw decoder,
source resolver, compiler or loader. In particular, duplicate keys, malformed
Unicode, field-specific token rejection in native P07 loading, cross-artifact
semantic mutations and no-solver readback remain implementation obligations.
Synthetic samples with freshly recomputed checksums can appear consistent;
checksums do not authenticate execution or validate the numerical method.

## Exact commands and outcomes

All uv commands below run from the repository root with
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Runtime/tool versions and hashes are
retained in the JSON report. uv 0.11.29; Python 3.12.13. Existing package suites
are baseline regression checks, not evidence that P07 has been implemented.

| Command | Actual outcome |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS; locked environment unchanged |
| `uv run --project packages/python --locked --offline python spec/results/proposals/review_p07.py > docs/verification/p07-candidate-audit.json` | PASS; 3 pairs, 3 analytical samples, 8 binary64 probes, 99 structural rejection mutations |
| `shasum -a 256 spec/results/proposals/examples/*.json spec/results/proposals/*.schema.json spec/results/proposals/ADR-P07.md spec/results/proposals/review_p07.py spec/results/proposals/review_p07.js > docs/verification/p07-byte-checksums.txt` | PASS; independent SHA-256 values match Python report/catalog |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness methods |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 69 existing methods, including both P04 methods and oracle comparisons |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS; 2 methods, 29 fixed projections |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS; 3 methods, original 92 P01 and 97 P01 rejection cases |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS; 3 methods, overlapping 207/84 catalogs and producer controls |
| `uv run --project packages/python --locked --offline ruff check spec/results/proposals/review_p07.py` | PASS |
| `uv run --project packages/python --locked --offline ruff format --check spec/results/proposals/review_p07.py` | PASS; 1 file |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml` | PASS; 13 existing package source files |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml spec/results/proposals/review_p07.py` | PASS; 1 audit source, with a targeted `import-untyped` annotation for existing jsonschema (no installed stubs); no package-wide suppression |
| `node spec/results/proposals/review_p07.js` | PASS; Node v24.18.0, 7 candidate hashes, 3 result hashes/normalized FIR identities, 8 binary64 probes |

The first supplementary audit-source mypy invocation **FAILED** for missing
jsonschema stubs and local variable type reuse. Distinct path names and explicit
object types resolved the latter; one import-specific `import-untyped`
annotation records the external library's missing stubs. No new dependency or
blanket missing-import suppression was introduced. Subsequent strict audit and
unchanged package checks passed.

Final repository/link and protected-file checks are recorded below. Distribution build, clean-wheel
suite, Julia execution, P07 runtime tests and CI lint-target changes are
**NOT RUN / deferred** for the separate implementation PR after PI ratification.
The unchanged native solver tests do not establish #29 or biological validity.

## Review and approval status

Independent engineering and scientific reviewers report no remaining contract
blocker after the corrections above. Both also found that the existing
`results/` ignore pattern hid the new specification directory. A narrow
`!/spec/results/` exception resolves this delivery issue. An initial repository
check failed while its linked verification narrative was still absent;
the complete proposal now passes the checker.

The engineering reviewer independently checked strict UTF-8, decoded duplicates
and Unicode scalar strings on the eight candidate JSON artifacts; exact bytes
and formatting controls for all three result pairs; and decimal-neighbor
intervals for eight numeric probes with 1200-digit Decimal arithmetic. Those
bounded inline review checks passed; they are not a retained general decoder.
The reviewer separately replayed the tracked audit, lint/format and checksum
checks and confirmed protected tracked files were unchanged.

The scientific reviewer independently evaluated the three positive-time samples
with 120-digit Decimal arithmetic using the represented binary64 beta, and
confirmed nearest-binary64 roundings. Their independent ECMAScript audit first
detected the empty-model ordering error, then passed all corrected examples.
Its original source is retained unchanged as
[review_p07.js](../../spec/results/proposals/review_p07.js), SHA-256
`616513961648cfad737948c2f62fd7ffbe0672d8bcb1fdb6a7c2b8335f8efe1f`.
Review agents provide independent checks, not human scientific approval.

| Final command | Actual outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/local links, not science |
| `uv run --project packages/python --locked --offline python spec/results/proposals/review_p07.py > /private/tmp/fenix-p07-final-replay.json` | PASS |
| `cmp docs/verification/p07-candidate-audit.json /private/tmp/fenix-p07-final-replay.json` | PASS; deterministic bounded-audit report replay |
| `shasum --check docs/verification/p07-byte-checksums.txt` | PASS; frozen candidate and proposal source bytes |
| `git diff --exit-code origin/main -- packages conformance docs/approved-decisions.md .github` | PASS; existing implementation, approved artifacts and CI unchanged |
| `git diff --check` | PASS |

Only new evidence files are added; historical verification reports remain
byte-for-byte unchanged. The contract PR must not close #22 or claim its runtime
API exists. Implementation starts only after explicit ratification of the
reviewed P07 revision and these bounded candidate expectations.
**Human PI ratification: PENDING. Implementation approval: PENDING.**
