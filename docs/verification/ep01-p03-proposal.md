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
