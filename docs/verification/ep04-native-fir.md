# EP-04 / #28 native FIR evidence — review pending

This addendum records implementation evidence for #28, the first EP-04 child.
It does not replace historical reference receipts, close #28 or EP-04, or supply
human PI acceptance. Base: merged main `1c11b814efc725af551c448064c8016c750d3e67`.
Work was isolated in `/private/tmp/fenix-28` on `feat/28-native-fir`; the original
checkout's `.gitignore` and `.ignore` edits were preserved.

## Scope and independent references

Affected files: `conformance/native/` runners, closed test-report schema,
independent reference comparator and corruption tests;
`.github/workflows/native-fir.yml`; development workflow/addendum and a disabled
main-ruleset proposal. No production source, package name/version, scientific
contract, approved catalog/fixture or historical receipt was changed.

Both native packages supply 84 canonicalization outcomes, 207 rejection outcomes
and nine compiler controls. The 13 approved FIR identity cases and nine compiled
controls exchange mathematical model and identity-preimage bytes. Expected
control models come from approved primary artifacts through unchanged P03 sorts
and external RFC 8785 serialization; neither compiler generates expectations.
Complete source references and source/catalog/schema/lock fingerprints accompany
the actual observations. Source-path, runtime-pin and dependency-version checks
bind the report's declared environment to the selected checkout and locks.

No numerical solver claim follows from FIR byte equality. #29 numerical execution
and #30 repository alpha remain separate dependent PRs. Registry publication,
P06, new scientific semantics, fixture regeneration and EP-03 closure are excluded.

## Local verification

CPython 3.12.13; Julia 1.10.13; uv 0.11.29; native Julia environment
`conformance/julia_ode`; reference Julia environment `conformance/julia`.
Julia used `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and
`JULIA_PKG_OFFLINE=true` after dependency installation. Python used the installed
locked environment's `packages/python/.venv/bin/python` directly. These are
local results; CI status must be assessed separately on the PR's actual head.

| Check | Result |
|---|---|
| `uv sync --project packages/python --locked` | PASS after initial DNS failure |
| `python scripts/check_repo.py` and `python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `python -m unittest discover -s packages/python/tests -v` | PASS; 88 tests |
| `python -m unittest discover -s packages/python/tests_native_fir -v` | PASS; all three native catalog/control tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS |
| Julia package and native FIR suites via `--project=conformance/julia_ode` | PASS; 207 rejection, 84 P03, nine compiler controls and 40-sample compiler/oracle bridge |
| `python -m unittest discover -s conformance/native/tests -v` | PASS; 13 tests, including mutually agreeing incorrect reports |
| Both native FIR producers and independent comparator | PASS; 300 rows per language; 13 + nine model/identity pairs |
| `ruff check conformance/native`, `ruff format --check conformance/native`, `git diff --check` | PASS after correcting initial lint/format failures |
| Python P01, canonicalization, rejection and production-decay reference tests | PASS |
| Python reference reports, rational oracle audit, Node P03 tests/report/comparison and rejection digest audit | PASS |
| Julia rejection reference tests/harness/report and Python–Julia reference comparison | PASS |
| Julia production-decay oracle tests/report and Python–Julia oracle comparison | PASS |
| Native Julia lockfile diff | PASS; unchanged |
| Fresh wheel/archive alpha installation and benchmarks | NOT RUN; #30 scope |
| Effective GitHub protection / administrator activation | NOT RUN; exact disabled proposal prepared for review |
| Human acceptance and merge of #28; #29/#30/final EP-04 acceptance | NOT RUN; human gates outstanding |

Earlier failures are retained: initial package installation could not reach
PyPI from the sandbox; an initial manual runner invocation used a malformed
revision length and was rejected; initial Ruff checks found import/style and
loop-closure formatting issues, corrected before final checks. An attempted
combined Julia reference test process redefined its `Main.R` constant; the
reference suite itself passed, and the harness was rerun in a separate process
as prescribed. No scientific fixture or expectation was altered to pass a test.

Independent engineering review checked corruption handling and P03 sorts. It
identified runtime/dependency checking, native digest assertion and loaded-source
binding gaps; those were corrected and re-reviewed. Agent review is not human
scientific approval. Reports provide bounded consistency, not authenticated
execution or biological validity.

## Main protection and remaining acceptance

The stable comparison context is `Native FIR conformance`. The exact
[disabled proposal](ep04-main-ruleset.proposed.json) requires PRs, existing checks
plus the new context, strict up-to-date branches, no bypass and no force
push/deletion. It adds no reviewer-count requirement or CODEOWNERS identity.
Before activation, review the payload against live context names and integration
IDs; afterward verify effective main rules. The historical governance draft
remains unmodified. No claim of merge enforcement is made from YAML alone.

#28 remains pending PR review, CI, applicable administration and human acceptance.
The EP-04 plan requires each child to be merged and accepted separately; passing
this local suite does not authorize an automatic merge or final epic closure.
