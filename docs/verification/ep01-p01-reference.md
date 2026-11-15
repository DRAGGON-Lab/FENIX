# P01 reference implementation and fixture review evidence — APPROVED

**Current fixture status: APPROVED by the human PI on 2026-11-15.** See the
[acceptance record](#human-pi-acceptance-recorded). Earlier REVIEW_REQUIRED and
pending-review statements below describe the historical implementation review.
Native FENIX implementations and exhaustive input validation remain unapproved.

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


## Human PI acceptance recorded

- Decision: **ACCEPTED** for all 92 registered reference expectations under
  **ADR-P01 / BioIR M0 subset v0.1.0**. The catalog now records APPROVED.
- Human PI: the approving repository user in this conversation; no separate
  personal name was supplied.
- Approval recorded: **2026-11-15**.
- Exact reviewed catalog SHA-256:
  `6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390`.
  Those catalog bytes are present at the approval-record base
  [`eb750ff`](https://github.com/DRAGGON-Lab/FENIX/commit/eb750ff).
- Approval source: explicit user statement in this conversation, transcribed
  below; no public approval URL was supplied.

> I reviewed ADR P01, ADR-P01 / BioIR M0 subset v0.1.0
>
> Reviewed catalog SHA-256
> 6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390
>
> Approval scope: All 92 registered reference expectations, comprising 34 expected acceptances and 58 expected rejections, including five canonical-serialization expectations, binary64 bit patterns, and declared diagnostic categories and paths.
>
> Not approved by this decision: Native FENIX implementations, exhaustive input validation, compiler correctness, solver correctness or future BioIR semantics.

The recorded counts match the exact reviewed catalog: **34 acceptances**,
**58 rejections**, **five canonical-serialization expectations** and **nine
binary64 bit-pattern expectations**. The scope includes every registered
expectation and its declared category/path; absent paths do not acquire new
requirements. General error precedence for multiply invalid documents remains
outside this bounded fixture decision.

**Not approved:** native FENIX implementations, exhaustive input validation,
compiler correctness, solver correctness or future BioIR semantics. This fixture
acceptance neither changes ADR-P01 nor grants broader parser/validator
implementation approval. No package API, compiler or solver is introduced. This
record performs no merge or issue closure.

The catalog changes only its approval status and scope metadata. Every case
record and raw input remains unchanged from the reviewed bytes. Catalog and
report hashes change with that metadata; the reviewed hash above continues to
identify precisely what was accepted. Both independent 92-case reports are
refreshed with approval provenance, preserving all observed rows. The accepted
207-case rejection suite's reports are also refreshed because they fingerprint
the P01 historical catalog; its cases and observed rows remain unchanged.
Earlier report hashes/status statements identify the historical review; the
retained report paths now contain the refreshed provenance described below.

Approval-record source fingerprint:
`4225a008b9ddf8f45e9f6c52a70208a2a97e828648b4e5f53cfaa3364a514bfc`.
Algorithm: SHA-256 over sorted repository-relative path + NUL + bytes + NUL
for these 13 changed source/index files: `ARCHITECTURE.md`, `PRODUCT.md`,
`conformance/README.md`, `conformance/bioir/README.md`,
`conformance/bioir/catalog.json`, `conformance/compare_reports.py`,
`conformance/julia/run_p01.jl`, `conformance/python/run_p01.py`,
`conformance/python/tests/test_reports.py`, `conformance/reference/check_p01.cjs`,
`docs/approved-decisions.md`, `spec/README.md` and `spec/bioir/README.md`.
Evidence records and generated reports are excluded to avoid circular identity.
Checks ran dirty on base `eb750ff6b681af61f775ec1ad17156663a390ed1` on branch
`conformance/12-p01-fixture-acceptance`, using the same locked runtime versions
and local cache/depot settings documented above.

| Approval-record artifact | SHA-256 |
|---|---|
| Catalog (approval status/scope metadata only) | `ffd8b03732094543baff2464ab8c83f672dab6ebb22f2237621a1df8e493fcbc` |
| P01 comparator | `93d39824f260b3c5fc4df4486339df20c86c63c1d33c4ca2480ef71d36aa65d6` |
| Python runner | `90ed33edde58da9d0caf38b3e1f80619f055cf180ad8027c73e97e82e86b8c06` |
| Julia runner | `b17090e450f5abd825da44fd18703d743d584e1ae57272b1dce3750f7121dd02` |
| Node audit | `cba2157148d2712870382ecc554391ba317a14a842a000b8b6375d308851651a` |
| [Python P01 report](p01-reference-python.json) | `79b198c4d4bd84ff8750b5d690971e1476d29b8992d638c0de2a86449bed1071` |
| [Julia P01 report](p01-reference-julia.json) | `ebc4a87d7f3c45e90d0f40456e9069c78281c61559fa29f39f78be5d36b64f71` |
| [Python rejection-suite report](rejections-python.json) | `08828c81c0ec4e3777a256ebda8621c7bd4d2f4254accdcf3583fbb1d0e9b349` |
| [Julia rejection-suite report](rejections-julia.json) | `041b2527927d762c6ad89e5ff6dc03071039eca5e6e90effad1e4501f8e19a06` |

The new CLI-status regression initially **FAIL**ed against the old comparator's
hard-coded pending-review message. It now reports the actual catalog status.
The existing wrong-status regression now selects the status opposite the
catalog's current value, preserving its negative assertion after approval.
The existing schema already permits REVIEW_REQUIRED and APPROVED; new checks
confirm both and reject unknown status. No schema or validation rule changes.

| Exact command/check | Acceptance-record outcome |
|---|---|
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS; 8 tests, including all 92 expectations and status regressions |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report artifacts/p01-python.json` | PASS; 92 cases, APPROVED |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report artifacts/p01-julia.json` | PASS; 92 cases, APPROVED |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py artifacts/p01-python.json artifacts/p01-julia.json` | PASS; all 92 expectations |
| `node conformance/reference/check_p01.cjs` | PASS; 41 canonical/digest checks, APPROVED |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/rejections/tests -v` | PASS; 10 tests, including 207 cases |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --report artifacts/rejections-python.json` | PASS; 207 unchanged cases |
| `julia --project=conformance/julia conformance/rejections/review.jl --report artifacts/rejections-julia.json` | PASS; 207 unchanged cases |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare artifacts/rejections-python.json artifacts/rejections-julia.json` | PASS; refreshed historical-catalog provenance |
| `node conformance/rejections/audit_inputs.cjs` | PASS; 144 BioIR digest checks |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/link checks |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke assertions |
| Structured audit against `eb750ff` | PASS; exact reviewed hash, 92 unchanged catalog case records and 92 byte-identical raw inputs; identical P01 and rejection-suite report case rows in each language |
| `git diff --exit-code HEAD -- conformance/bioir/inputs conformance/bioir/catalog.schema.json conformance/python/p01.py conformance/julia/p01.jl spec/bioir/proposals spec/fir spec/canonicalization packages conformance/canonicalization conformance/production_decay conformance/rejections .github/workflows/scaffold-smoke.yml` | PASS before the approval-record commit; schemas, scientific validators, mathematical contracts, fixture artifacts, packages and CI unchanged |
| `git diff --check` and `git diff --cached --check` | PASS; working and staged changes |
| Hosted CI for this approval-record commit | NOT RUN locally; checked separately on its PR after push |

This acceptance is established by the explicit human decision, with the reviewed
catalog digest and scope above. Passing reference checks does not expand it.

A separate read-only acceptance-record review independently verified the exact
reviewed hash, scope/counts and exclusions, 92 unchanged inputs/cases/report rows,
207 unchanged rejection rows, the 13-file source fingerprint, all nine current
artifact hashes, both retained-report comparisons, links and protected-path/
whitespace audits. No confirmed finding remained. This review supplies record
verification; human acceptance derives from the explicit statement above.
