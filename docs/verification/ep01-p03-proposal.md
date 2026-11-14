# ADR-P03 proposal evidence — review required

Date: 2026-11-14. Issue [#14](https://github.com/DRAGGON-Lab/FENIX/issues/14).
Branch: `docs/14-jcs-p03-proposal`. Main base:
`c15afd05dfa72c2813c8fe078e5135ab260ab1cf`. The already-approved P02 status record
`72af38b` was carried separately as `f28e24c3b4fd469dafe89daa9a4ee3e6c28590aa`.
No P02 scientific rule or existing example was changed. P03 was checked dirty
before its proposal commit. Human PI signoff and golden-vector approval remain
**PENDING**. The [ADR](../../spec/canonicalization/proposals/ADR-P03.md) is PROPOSED.

## Reviewed source and assumptions

Source fingerprint:
`c37904ece1ca526b4d4979d82abfda6b2a56fdbf92e055a87a22b13fc10c4456`.
Algorithm: SHA-256 of sorted relative path + NUL + bytes + NUL over nonignored
tracked/untracked files in `spec/canonicalization`, `conformance/canonicalization`,
plus `docs/approved-decisions.md` and `.github/workflows/scaffold-smoke.yml`.
147 files; caches and this report excluded. This is a source fingerprint, not a
FIR model identity digest.

The user selected declaration sorting, full binary64 token rounding and a JSON
identity wrapper. The proposed constants are domain `fenix.fir` and independent
canonicalization version `0.1.0`, supporting P02 model schema `0.1.0` only.
Nonzero numeric underflow is rejected; signed zero and finite subnormals are
accepted. These rules are proposals, not self-ratified science.

Sources: [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), sections 3.1–3.2
and Appendices A/B; ratified P01/P02, explicitly distinguished from the proposed
FIR-specific token policy. Appendix B expectations were transcribed from the
published table, including its exact bit patterns. Other candidate bytes were
prepared using external `rfc8785` on explicitly authored expected models, then
checked with independent ECMAScript serialization. Neither tool is a FENIX
normalizer or compiler; no expected model came from such an implementation.

## Executed checks

Environment: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0/rfc8785 0.1.4;
Node v24.18.0; Julia 1.10.13 with the unchanged locked reference environment.
uv commands used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`; Julia commands used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`. Commands ran from root.

| Command/check | Result |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --report /private/tmp/fenix-p03-python.json` | PASS; schema, artifact integrity and candidate serialization |
| `node conformance/canonicalization/review_p03.cjs --report /private/tmp/fenix-p03-node.json` | PASS; independent byte/digest verification |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --compare /private/tmp/fenix-p03-python.json /private/tmp/fenix-p03-node.json` | PASS; complete reports match expected artifacts and each other |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v` | PASS; 3 tests, including evidence-failure subcases |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; 24 FIR examples and 8 source structures |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 99 assertions |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p03-p01-python.json` | PASS; 92 cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p03-p01-julia.json` | PASS; 92 cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-p03-p01-python.json /private/tmp/fenix-p03-p01-julia.json` | PASS; 92 matching independent cases |
| `node conformance/reference/check_p01.cjs` | PASS; 41 independent canonical/digest checks |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| `git diff --exit-code f28e24c -- spec/fir spec/bioir conformance/bioir conformance/python conformance/julia packages` | PASS; existing contracts, fixtures, reference tools and packages unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| Native FIR parser, semantic validation, normalization/idempotence and full FIR canonical round trip | NOT RUN; not implemented before ratification |
| Hosted GitHub Actions execution | NOT RUN locally; new CI job supplied for PR execution |
| Human PI contract ratification and independent golden-vector signoff | PENDING |

All final executed checks exited 0. The 67 catalog rows contain 47 exact
serialization matches, 3 confirmed JCS rejections (NaN, infinity, lone surrogate)
and 17 contract-only NOT RUN cases. **All FIR validation/normalization stages
remain NOT RUN**, including those 13 identity examples for which candidate
serialization is checked. The latter serialize the supplied expected normalized
models; they do not demonstrate a functioning transformation from input FIR.
Candidate digest equality/inequality tests confirm consistent artifact declarations,
not independent execution of N.

The negative evidence tests reject stale catalogs, missing/duplicate report rows,
incorrect digests, tampered artifacts, path escape and false normalization PASS
claims. There is no fixture-regeneration command. The CI job runs these same
standard serialization checks and uploads separate Python/Node reports; Node
is a reference development tool, not a native package runtime dependency.

## Remaining review gate

PI review must cover binary64 information loss, nonzero underflow, declaration
ordering, exact domain/version wrapper and digest scope, candidate normalized
models, Unicode/numeric byte vectors and proposed rejection expectations. No
candidate bytes or digests are labeled approved golden references. No issue was
closed, package published, or compiler/normalizer/solver functionality added.

## Ordering correction

Date: 2026-11-14. PR [#53](https://github.com/DRAGGON-Lab/FENIX/pull/53), same
branch. Correction baseline: `1849e11737b5b5c3c0e1ea0dabf323aa004074c7`.
The earlier evidence above is preserved as a historical record. Its successful
serialization checks missed incorrect expected observable ordering: both reference
tools preserved supplied arrays, and neither checked the declaration-order
invariant on expected models. Mutual byte/digest agreement therefore did not
establish that the expected objects followed the proposed ordering rule.

The regression was added **before** fixture changes. The P03 test command below
exited 1 with exactly two failing subcases: `fir-two-observables` and
`fir-observables-permuted`, each identifying its normalized artifact, `observables`
collection and offending keys `another_amount`, `amount_x`. The other tests and
comparator probes passed. After correcting only that observable order, the same
command passes all five tests. It inspects all six declaration collections on
every `fir_identity` expected object using decoded UTF-16 code units and the
ADR's keys; a set comparison requires every physical expected normalized artifact
to be referenced and inspected, while permitting shared artifacts. The comparator
probes cover `amount_x` before `another_amount` and supplementary Unicode ordering
that differs from Python code-point order. These are test-only strings, not new
valid FIR identifiers.

Only those two normalized models, their model/wrapper canonical bytes and their
six catalog checksum fields were corrected. Both still have identical normalized,
model and identity bytes; original inputs remain distinct, with unchanged SHA-256:

- `fir-two-observables.input`: `d01b45c40e834ad5e60bfefc5005184a86885ab5794a1bad310e00e32959c7ea`.
- `fir-observables-permuted.input`: `818942fc52d059d260219218757e51a37a976e6cf160f91616c2859355579199`.

Both corrected fixtures have these SHA-256 values:

| Artifact | SHA-256 |
|---|---|
| Expected normalized JSON | `dab852d00da5e4bf262ab7eb05f14bf6d3fc778375b24a02ce46ddb7e3980a31` |
| Canonical model bytes | `d0e15f7edbe9ea8aa6540a0a86422388edccb4743f0b2217d8441ac2f5c7a4fb` |
| Canonical identity-wrapper bytes | `003333595f696d2560bd3e6b120cd1c4fb7c8e42f7ff2102d567f6adbb0948a3` |

Each reference serializer compares **complete model and wrapper bytes** against
the artifacts, independently of hashes. Their complete reports are compared
against the catalog and each other. Read-only baseline probes also checked every
input and every other candidate artifact against `git show 1849e117:<path>`,
required that only the six targeted expected files changed, and compared the
permutation pair's normalized/model/wrapper bytes directly. All passed; unrelated
expectations were not regenerated. No regeneration command or CI change was added.

Corrected source fingerprint: `ff7ec0d0a4458ee127182adfcf07d39d88e26f737a209570b426aa2db70b2729`.
Same algorithm and 147-file scope as above; this appended evidence report remains
excluded. Verification ran dirty on the correction baseline. Environment unchanged:
uv 0.11.29, CPython 3.12.13, jsonschema 4.26.0, rfc8785 0.1.4, Node v24.18.0,
Julia 1.10.13. Python commands use `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`;
Julia uses the same depot, offline flag and explicit executable described above.

| Command/check | Correction result |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v` | FAIL before correction (two ordering subcases); PASS after correction (5 tests) |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --report /private/tmp/fenix-p03-correction-python.json` | PASS; exact model/wrapper bytes and digests |
| `node conformance/canonicalization/review_p03.cjs --report /private/tmp/fenix-p03-correction-node.json` | PASS; independent exact model/wrapper bytes and digests |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --compare /private/tmp/fenix-p03-correction-python.json /private/tmp/fenix-p03-correction-node.json` | PASS; complete reports match, 67 rows: 47 serialization matches, 3 rejections, 17 contract-only NOT RUN |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository and relative links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| `git diff --exit-code 1849e117 -- conformance/canonicalization/inputs spec/fir spec/bioir conformance/bioir conformance/python conformance/julia packages .github` | PASS; inputs, P01/P02, packages and CI unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| Native input-to-normalized transformation, complete semantic validation, normalization idempotence, end-to-end FIR canonical round trips | NOT RUN; no native implementation |
| Human PI ratification and reference-vector approval | PENDING |

**Executed:** declaration-order invariants on expected objects, candidate
serialization and digest verification. These do not demonstrate execution of N
on original inputs. ADR-P03 remains **PROPOSED**, the catalog remains
**REVIEW_REQUIRED**, and issue #14 remains open. Approval of the contract,
candidate reference vectors and future native implementations are separate gates.
