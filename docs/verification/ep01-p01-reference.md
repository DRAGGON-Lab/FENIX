# P01 reference implementation and fixture review evidence

Date: 2026-11-14. Base: merged PR #50 (`d8379f7f32582b4c7a2ced678160041ce8e31ee0`).
First focused catalog commit: `5c0a5d8`. Remaining source was checked in a dirty
feature branch before the reference implementation/evidence commit.
Source fingerprint: `6332329bcae7eb2e67f3ad68048bc7ec55c1c766a8e2706aea62064254f547f2`.
Fingerprint algorithm: SHA-256 over sorted relative path + NUL + bytes + NUL
for the full `conformance/` tree excluding `__pycache__`, plus the workflow,
root README, development workflow, approved-decision index, and the two spec
index README files. This report and generated reports are excluded.

Catalog SHA-256: `6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390`.
Catalog status: **REVIEW_REQUIRED**, not approved normative/golden fixtures.
Authority: ratified ADR-P01 only. No FIR compilation, P02/P03 normalization,
solver, standards mapping or native public modeling API was implemented.

## Checks actually executed

Environment: macOS x86_64, uv 0.11.29, CPython 3.12.13, Julia 1.10.13,
Node v24.18.0. Python development tools and Julia reference dependencies use
the committed lockfiles. Julia binary: `/private/tmp/julia-1.10.13/bin/julia`.
Prefix uv commands below with `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`;
Julia commands used `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`,
`JULIA_PKG_OFFLINE=true` and `--startup-file=no`.

| Exact command (excluding prefixes above) | Outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 2 packaging tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS, 6 tests including catalog subcases and report fault injection |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p01-python.json` | PASS, 92 candidate cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p01-julia.json` | PASS, 92 candidate cases |
| `packages/python/.venv/bin/python conformance/compare_reports.py /private/tmp/fenix-p01-python.json /private/tmp/fenix-p01-julia.json` | PASS, 92 matching cases with matching catalog identity |
| `node conformance/reference/check_p01.cjs` | PASS, 41 independent canonical/digest checks |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS, 2 packaging tests |
| Ruby `YAML.load_file` on `.github/workflows/scaffold-smoke.yml` | PASS, YAML syntax only |
| `git diff --check` | PASS |
| GitHub Actions execution | NOT RUN locally; pending PR CI |
| Independent human/ChatGPT review of candidate catalog and implementation | PENDING |
| FIR/solver/biological conformance | NOT RUN; outside this P01 task |

Final reported checks exited 0. The initial Julia run failed four cases: native
parsing reports ERANGE for underflow as well as overflow, and Julia's `isequal`
distinguishes signed zero. The Julia adapter was corrected against the existing
expectations, without relaxing them. Two later cases add distinct-role rejection
and acceptance of reordered valid functions while preserving order-sensitive
content identity.

## Artifacts and independent evidence

The checked-in [Python report](p01-reference-python.json) and
[Julia report](p01-reference-julia.json) preserve every observed category/path.
Their catalog identities match the hash above. Neither native runner calls the
other or imports FENIX; the comparator only reads reports. Cross-language
agreement is checked against catalog expectations, not treated as its own oracle.
Fault-injection tests reject missing/duplicate cases, stale catalogs, hidden
failures, non-boolean flags, incorrect status, and two reports agreeing on an incorrect category.

The raw-input outcomes are authored from P01 and RFC/JSON Schema rules, not
regenerated from validator results. Candidate semantic-input digests were
prepared with external `rfc8785`, then checked independently by Node/V8.
The catalog README identifies category semantics and the source boundary between
P01 raw-token restrictions, pure JCS and still-pending P03 FIR normalization.

An additional independent transient stress check compared Julia number encoding
against V8 `JSON.stringify` for 5,000 finite binary64 bit patterns generated with
Python `random.Random(1201)`, `getrandbits(64)` and finite-value filtering. All
matched. Its raw bits and Julia outputs remain at `/private/tmp/fenix-jcs-bits.json`
and `/private/tmp/fenix-jcs-numbers.json`. This is a supplemental engineering
check, not normative vectors or proof of universal canonicalization correctness.

## Review and closure

The issue #12 PR supplies both independent validators and reference-integrity,
revision, unit and schema evidence. Before merge, the human PI must review the
candidate expectations/categories/paths and approve the implementation against
P01's catalog gate. Final review must record fixture approval explicitly; this
report does not grant it. Closing keywords are limited to #12 and must not be
interpreted as completing epic #3 or FIR fixture issues #13–#17.
