# EP-01 BioIR/FIR rejection reference evidence — APPROVED

**Current status: APPROVED by the human PI on 2026-11-15.** See the
[acceptance record](#human-pi-acceptance-recorded). The negative capability
fixtures are **not exhaustive**. Earlier REVIEW_REQUIRED and pending-acceptance
statements below describe the reviewed implementation revision.

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

Hosted GitHub Actions execution: **PASS**, all seven jobs at scientific-source
commit `cbe599f856d955faa1664d34306eb1ac3f3ec0d6` on
[PR #56](https://github.com/DRAGGON-Lab/FENIX/pull/56),
[run 43655199519](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43655199519).
This includes Repository harness, Python-only package, Julia-only package,
Candidate P01 reference conformance, Candidate P03 serialization evidence,
Candidate production-decay reference agreement and the new Candidate BioIR/FIR
rejection reference agreement. Native reports were produced separately and
successfully compared by the dependent locked Python job. This hosted result
was observed after the local verification above; the subsequent evidence-only
record amendment does not change the 75-file source fingerprint.
Human PI acceptance of the concrete rejection suite: **PENDING / NOT RUN**.
Public package parser/validator, compiler, normalization, solver and biological
validation: **NOT RUN / outside this fixture-publication task**. The approved P03
catalog's historical 17 `NOT_RUN` outcomes remain unchanged; this suite supplies
new, separately scoped execution evidence.


## Human PI acceptance recorded

- Decision: **ACCEPTED** for the concrete 207-case rejection reference suite and
  its bounded independent Python/Julia evidence. The catalog now records APPROVED.
- Ratifying human PI: the approving repository user in this Codex conversation;
  no separate personal name was supplied.
- Approval recorded: **2026-11-15**.
- Reviewed revision: [`b9bb961e7293c00c5728e8dd374fb4ef7a15b7ef`](https://github.com/DRAGGON-Lab/FENIX/commit/b9bb961e7293c00c5728e8dd374fb4ef7a15b7ef)
  on [PR #56](https://github.com/DRAGGON-Lab/FENIX/pull/56).
- Approval source: explicit user instruction in this conversation, transcribed
  below; no public approval URL was supplied.

> Ok I approve this. Record that the negative capability fixture was not exhaustive and push the changes.

**The negative capability fixtures are not exhaustive.** Acceptance covers the
207 registered cases, their fixed expected diagnostics and the supplied evidence.
It does not establish complete coverage of unsupported capabilities, malformed
inputs or combinations of faults. No general error-precedence contract follows
from these fixtures. Additional coverage remains possible under the ratified
contracts and its applicable review gates.

Native package APIs, compilers, normalization, solvers and any new scientific
semantics retain separate approval requirements. This acceptance changes no
P01/P02/P03 scientific rule and does not imply biological validity. This record
performs no merge or issue closure; PR #56 remains for human merge.

Only approval/status handling, report provenance and current-status documentation
change. Both supported statuses, REVIEW_REQUIRED and APPROVED, are accepted by
the catalog schema and faithfully reported by each writer; unknown status and
report/catalog disagreement remain rejected. Fixture contents, all 207 case
records and their coverage registry remain unchanged from the reviewed revision.
Earlier hashes above identify that reviewed revision; retained reports are
refreshed below to carry current approval provenance.

Approval-record source fingerprint:
`24c538ca3111167686ab9c2ef4c4be7fe80f7b707195230c64e2deff67585445`.
The sorted path + NUL + bytes + NUL SHA-256 algorithm above now covers the same
75 source paths plus `PRODUCT.md`, `ARCHITECTURE.md` and
`docs/approved-decisions.md` (**78 files**). This record and generated report
files remain excluded. Verification ran dirty on the reviewed revision using
the same locked runtime versions and local cache settings documented above.

| Approval-record artifact | SHA-256 |
|---|---|
| Catalog (only status changed) | `5117b37ec7d4d45e111943e925dcfc27a3ac280ddeabfb456ff37b93a9750088` |
| Catalog schema (supported approval statuses) | `268c37976902079a7ccbd7f365bbbc00a96cb6c9c02902f425b834665f99d5a6` |
| Python report writer/comparator | `87fee105d6229b105293d77a6f9a3dd55a96d2e229edaef1df86dd79697040a0` |
| Julia report writer | `286ed1a678bef040c47b4a513cc9388401c136045598704916269393c5889d23` |
| [Python report](rejections-python.json) | `9792c4f687e04fe19a4a2c6dcd0bd4f200dc2607cbf04f0582421cdaba6761d1` |
| [Julia report](rejections-julia.json) | `fe97b3734912b989fc95f023e010474efc0167d5b04255da262d1014c7f11e36` |

The approval-status regression preceded the schema/writer changes: the APPROVED
catalog was rejected by the old status constraint (**FAIL**, expected). The
updated Python tests exercise both supported statuses, unknown status rejection
and report/catalog disagreement; Julia separately checks both statuses, unchanged
case records, unknown status and current report provenance. Final outcomes follow.

| Exact command/check | Acceptance-record outcome |
|---|---|
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/rejections/tests -v` | PASS; 10 tests, including all 207 cases and approval-status regressions |
| `julia --project=conformance/julia conformance/rejections/tests/test_harness.jl` | PASS; 45 assertions, including six approval-status assertions |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --report artifacts/rejections-python.json` | PASS; 207 cases, APPROVED |
| `julia --project=conformance/julia conformance/rejections/review.jl --report artifacts/rejections-julia.json` | PASS; 207 cases, APPROVED |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare artifacts/rejections-python.json artifacts/rejections-julia.json` | PASS; 207 unchanged outcomes, APPROVED |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare docs/verification/rejections-python.json docs/verification/rejections-julia.json` | PASS; retained approval reports |
| `node conformance/rejections/audit_inputs.cjs` | PASS; 144 BioIR digest checks |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository and links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke assertions |
| Structured comparison with reviewed `b9bb961` of catalog, raw inputs and retained reports | PASS; status/provenance only, 56 unchanged new raw inputs, all 207 case records and coverage unchanged, identical case rows in both refreshed reports |
| `git diff --exit-code b9bb961 -- conformance/rejections/inputs conformance/rejections/reference.py conformance/rejections/reference.jl spec/bioir spec/fir spec/canonicalization packages conformance/bioir conformance/canonicalization conformance/production_decay conformance/julia conformance/python conformance/reference conformance/compare_reports.py .github/workflows/scaffold-smoke.yml` | PASS; mathematical validators, scientific contracts, fixture bytes, package sources, CI, dependency locks and unrelated catalogs unchanged |
| `git diff --check` and `git diff --cached --check` | PASS; working and staged changes |
| Hosted checks for approval-record commit | NOT RUN locally; available on PR #56 after push |

This human acceptance is established by the explicit instruction above, with the
stated non-exhaustive coverage limitation. Automated success does not broaden it.

## P01 fixture acceptance provenance refresh

The human PI separately accepted the 92 P01 reference expectations identified by
reviewed catalog SHA-256
`6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390`.
See the [P01 acceptance record](ep01-p01-reference.md#human-pi-acceptance-recorded).
The catalog's approval status/scope metadata now gives current SHA-256
`ffd8b03732094543baff2464ab8c83f672dab6ebb22f2237621a1df8e493fcbc`.
Both retained rejection reports are refreshed solely in that historical P01
catalog fingerprint. Their 207 case rows and all other report fields are unchanged
from `eb750ff`; native generation and current comparison pass.

Current [Python report](rejections-python.json) SHA-256:
`08828c81c0ec4e3777a256ebda8621c7bd4d2f4254accdcf3583fbb1d0e9b349`.
Current [Julia report](rejections-julia.json) SHA-256:
`041b2527927d762c6ad89e5ff6dc03071039eca5e6e90effad1e4501f8e19a06`.
Earlier hashes above identify the prior evidence revisions. The P01 record retains
current source identity, commands and unchanged-artifact checks. This provenance
refresh changes no rejection expectation or scientific rule. Negative capability
fixtures remain non-exhaustive; native implementation and exhaustive-validation
approval remain separate.

## EP-02 Python content tooling provenance refresh

Issue #18 adds locked development-only Ruff/mypy tooling and Python content
package configuration. The [EP-02 verification record](ep02-python-content.md)
records freshly executed independent reports and their current hashes. Both
retained rejection reports change only the Python manifest/lock fingerprints;
all 207 observed case rows and every other field remain identical to `972f23b`.
The older hashes above identify earlier evidence revisions. This refresh changes
no scientific contract, approved expectation, catalog or raw fixture byte.

## EP-02 committed-document tooling provenance refresh

Issue #19 promotes the existing locked rfc8785 0.1.4 tool to a runtime dependency.
The [committed-document evidence](ep02-python-documents.md) records new native
checks and regenerated reference reports. Both retained rejection reports change
only the Python manifest/lock fingerprints; every other field and all 207 observed
rows match `91dd4c2`. Previous artifact hashes remain historical identities.
