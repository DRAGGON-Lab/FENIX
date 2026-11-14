# EP-01 BioIR/FIR rejection reference evidence — REVIEW_REQUIRED

Issue [#17](https://github.com/DRAGGON-Lab/FENIX/issues/17), M-1 / EP-01.
Date: 2026-11-14. Branch: `conformance/17-negative-fixtures`.
Base: `origin/main` at `e8e0fa327294795c9384cb5a1b8daaa82a102736`, including
merged PR #55. The [catalog](../../conformance/rejections/catalog.json) and
concrete diagnostic expectations remain **REVIEW_REQUIRED**. Plan approval
allows reference implementation and review preparation; human PI acceptance of
the suite and evidence remains pending. Keep #17 open.

## Scope, contracts and source identity

One implementer owns catalog publication, both native references, tests, CI and
documentation. Ratified P01/P02/P03 supply the scientific rules; the catalog
provides explicit per-case candidate outcomes and paths before the reference
adapters are implemented. Existing raw artifacts are referenced by path and
SHA-256. New raw inputs cover gaps without changing prior bytes or expectations.

The [suite description](../../conformance/rejections/README.md) explains operations,
stages, diagnostic categories and dependency identities. `model`, `producer`
and `capability` are separate reference operations. There is no public package
validator, compiler, normalizer, solver, ExecutionSpec schema, new event behavior,
new stochastic eligibility or scientific-contract change. A mathematical model
check alone makes no source-correspondence claim.

Verification ran on the dirty issue branch at the base above. Source fingerprint:
`30777fd6c8d8ae02e35a821c3cd1ec20a382ff71f3df3507dfa91a0d621daced`.
Algorithm: SHA-256 of sorted repository-relative path + NUL + exact file bytes +
NUL over all non-cache files under `conformance/rejections/`, plus
`.github/workflows/scaffold-smoke.yml`, `conformance/README.md`,
`conformance/julia/README.md`, `conformance/python/p01.py`,
`conformance/julia/p01.jl`, `docs/DEVELOPMENT_WORKFLOW.md` and `spec/README.md`
(**75 files**). This record and retained reports are excluded to avoid circular
identity. Git commit metadata is outside this source fingerprint.

Runtime versions: uv **0.11.29**, CPython **3.12.13**, `jsonschema` **4.26.0**,
`rfc8785` **0.1.4**, Julia **1.10.13**, Julia `JSON` **1.13.4**,
`JSONSchema` **1.6.0**, Node **24.18.0**. Both existing dependency locks are
unchanged. Commands below run from the repository root. Locally, `julia` denotes
`/tmp/julia-1.10.13/bin/julia` with `JULIA_DEPOT_PATH=/tmp/fenix-julia-depot`
and `JULIA_PKG_OFFLINE=true`; Python commands use
`UV_CACHE_DIR=/tmp/fenix-uv-cache`. These cache locations are local execution
details, not repository dependencies.

## Coverage, independence and diagnostic evidence

The suite has **207 cases: 145 reject, 62 accept**. These include all 92 P01
inputs, all **17** historical P03 `contract_only` inputs, 13 P03 FIR identity
inputs, all **24** P02 examples and 61 additional cases. There are **56 new raw
artifacts**; existing raw bytes are not copied. The coverage registry has:

| Requirement | Registered cases |
|---|---:|
| Duplicate IDs/keys | 16 |
| Broken revision digest / exact references | 9 |
| Invalid units | 11 |
| Missing port / typed or producer reference | 8 |
| Unsupported profile | 8 |
| Invalid event | 3 |
| P03 contract_only | 17 |
| P02 examples | 24 |
| Positive controls | 62 |
| Numeric policy | 7 |

Groups overlap. Counts are registration coverage, not claims of exhaustive
validation of future contracts. The one-state M0 schema rejects overfull
state/equation collections structurally; repeated IDs in structurally admissible
collections are semantic rejections. Exactly one primary diagnostic is fixed per
fixture. No general precedence for multiply invalid documents is ratified.

Both languages independently parse the original inputs and recognize exact P02
templates, typed references, roles, units and stoichiometry. Neither executes
expressions, performs algebraic repairs, invokes the other language or imports
native FENIX packages. The unchanged schemas decide structural acceptance;
recognized-branch diagnostic expansion localizes errors using pinned library
paths and schema members. Missing/unexpected keys are not parsed from exception
prose. Tests verify declaration permutations and source mappings without mutation.

Opt-in P01 parser internals supply field-level numeric paths and the P03 numeric
policy; default P01 entry points retain the 92-case observations. P01 rejects
unsafe integer tokens; P03 interprets integer-looking tokens directly as binary64.
Tests include nested overflow, nonzero underflow, escaped pointer keys, finite
subnormals and extreme-exponent exact zero. The independent ECMAScript audit
passes **144 BioIR content-digest checks**, including intentionally broken digests;
semantic mutations otherwise retain self-consistent independently checked digests.

Reports are versioned, include runtime and catalog/schema/contract/evaluator/lock
fingerprints, and require one unique row for every case. Comparison checks each
row against fixed catalog expectations, not merely against the other report.
Wrong identities, stale provenance, false success, missing/duplicate/extra cases,
and mutually agreeing incorrect diagnostics fail. Writers protect repository
source, schema, fixture and documentation paths, including symlink/hardlink aliases.
Reports are reproducibility evidence, not authenticated execution attestations.

| Retained artifact | SHA-256 |
|---|---|
| [Catalog](../../conformance/rejections/catalog.json) | `29a1a3a04d12052ae335f1911410be18dafdb2892ea36b446eb86f9fca62fb88` |
| [Catalog schema](../../conformance/rejections/catalog.schema.json) | `169af56dce55bc0d5fb9b870c3345fb4aad4bb83b7610d1bfd688ea3c1ad926c` |
| [Python reference](../../conformance/rejections/reference.py) | `1664291207392b5da2f1dfb7979079201fd0c3c6f406918ccb59acb1dfb1d124` |
| [Julia reference](../../conformance/rejections/reference.jl) | `4172dbf15b6e8f7789b2e53db0b2aa2ac79f4b769eb974e3ed251bad94802359` |
| [Python report writer/comparator](../../conformance/rejections/review.py) | `296c5026aded79e59657dd77119469f42831a6d0f50b4ecd382130a9d0caf97f` |
| [Julia report writer](../../conformance/rejections/review.jl) | `02e647e949608c5d48ecb7868c893ba6984375b2915c132546d3a46bfd520394` |
| [Python report](rejections-python.json) | `01ca22f2af9d485eb900625aaba9e819e91dee2071a232bad8ed5b0f431ddf63` |
| [Julia report](rejections-julia.json) | `3dfa4d5a6a12b90a7de7530e96cec699b2c2fb79747e4282f562a91f5521ebb8` |

Reports were generated under `artifacts/` and copied unchanged to this verification
directory for review. CLI report writers intentionally reject output paths under
repository source/documentation directories. Every referenced input's individual
SHA-256 remains in the catalog; every schema/contract/dependency checksum remains
in each report.

## Executed checks

All final checks below exited **0**. Initial failure records are separate below.

| Exact command | Outcome |
|---|---|
| `uv sync --project packages/python --locked` | PASS; eight existing packages |
| `julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'` | PASS; cached offline environment |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/rejections/tests -v` | PASS; 8 tests, including all 207 cases |
| `julia --project=conformance/julia conformance/rejections/tests/test_reference.jl` | PASS; 268 assertions |
| `julia --project=conformance/julia conformance/rejections/tests/test_harness.jl` | PASS; 39 assertions |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --report artifacts/rejections-python.json` | PASS; 207 cases |
| `julia --project=conformance/julia conformance/rejections/review.jl --report artifacts/rejections-julia.json` | PASS; 207 cases |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare artifacts/rejections-python.json artifacts/rejections-julia.json` | PASS; all fixed diagnostics |
| `node conformance/rejections/audit_inputs.cjs` | PASS; 144 BioIR digest checks |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report artifacts/p01-python.json` | PASS; 92 cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report artifacts/p01-julia.json` | PASS; 92 cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py artifacts/p01-python.json artifacts/p01-julia.json` | PASS; 92 cases |
| `node conformance/reference/check_p01.cjs` | PASS; independent legacy digest/byte checks |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; 24 examples and 8 source structures |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 99 structural assertions |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v` | PASS; 15 tests |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --report artifacts/p03-python.json` | PASS; historical 84-case report |
| `node --test conformance/canonicalization/tests/test_review.cjs` | PASS; 5 tests |
| `node conformance/canonicalization/review_p03.cjs --report artifacts/p03-node.json` | PASS; historical 84-case report |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --compare artifacts/p03-python.json artifacts/p03-node.json` | PASS; 63 PASS, 4 REJECT_CONFIRMED, 17 NOT_RUN unchanged |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/link checks |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke assertions |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v` | PASS; 16 tests |
| `uv run --project packages/python --locked --offline python conformance/production_decay/audit_rational.py` | PASS; existing rational audit |
| `uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --report artifacts/production-decay-python.json` | PASS; existing oracle |
| `julia --project=conformance/julia conformance/production_decay/tests/test_oracle.jl` | PASS; existing oracle tests |
| `julia --project=conformance/julia conformance/production_decay/review_oracle.jl --report artifacts/production-decay-julia.json` | PASS; existing oracle |
| `uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --compare artifacts/production-decay-python.json artifacts/production-decay-julia.json` | PASS; existing fixed references |
| `git diff --check` | PASS |

The final P01 report `cases` arrays were compared exactly with retained pre-change
issue #16 reports (`/tmp/fenix-16-p01-python.json` and
`/tmp/fenix-16-p01-julia.json`): **PASS**, all 92 observations unchanged in each
language. These local baseline files are supplementary evidence; the checked-in
P01 catalog and existing runner tests remain the reproducible baseline.

Protected-path audit:

```sh
git diff --exit-code origin/main -- spec/bioir spec/fir spec/canonicalization conformance/bioir conformance/canonicalization conformance/production_decay packages conformance/julia/Project.toml conformance/julia/Manifest.toml
```

**PASS**: ratified contracts/schemas, approved scientific fixture bytes/catalogs,
package sources and reference dependency locks are unchanged. `spec/README.md`
only gains an index link, outside those protected scientific directories.

## Regression and independent review record

Initial regressions **FAIL** as intended before adapters/report code existed
(`ModuleNotFoundError` for `reference`, then `review`). The first Julia missing-AST-
member probe exposed a stack overflow in schema diagnostic expansion due to
shared object aliases during library reference resolution. Serializing the
expanded diagnostic schema removes those aliases without changing full-schema
acceptance; both native suites subsequently passed the fixed expected path.

The broader verification's first temporary Python subprocess runner inherited
macOS `__PYVENV_LAUNCHER__` from `/usr/bin/python3`, causing dependency/import
failures despite the installed uv environment. Removing that inherited launcher
variable from the temporary runner restored the locked interpreter. All affected
commands were rerun successfully; the environment failure is not reported as a
passing run. No package or dependency change was made to accommodate it.

Separate read-only scientific review independently executed both 207-case native
validators, the 144-check digest audit, P03 numeric edge probes and protected-path
audit; it found **no confirmed scientific defect**. Separate engineering review
found a **P2** overwrite-protection defect: hardlinks to documentation escaped the
initial selected-directory scan. Both writers now inspect all repository source
files while pruning generated/environment directories. New Python and Julia
hardlink regressions pass. Engineering re-review found **no remaining confirmed
finding**, independently passing Python tests, 268 Julia reference assertions,
39 Julia harness assertions and legacy P01 comparison. Agent reviews provide
engineering/scientific evidence, not human PI approval.
A separate read-only documentation review verified counts, all eight recorded
artifact hashes, the 75-file source fingerprint, retained reports, commands and
approval boundaries. Its P3 Node test-count typo was corrected to five; no
remaining confirmed documentation finding was reported.

Hosted GitHub Actions execution: **NOT RUN locally**. CI now extends the native
Python/Julia jobs with separate reports and uses a dependent comparison job under
the locked Python environment. CI status is to be assessed on the PR.
Human PI acceptance of the concrete rejection suite: **PENDING / NOT RUN**.
Public package parser/validator, compiler, normalization, solver and biological
validation: **NOT RUN / outside this fixture-publication task**. The approved P03
catalog's historical 17 `NOT_RUN` outcomes remain unchanged; this suite supplies
new, separately scoped execution evidence.
