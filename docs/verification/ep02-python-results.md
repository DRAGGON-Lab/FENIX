# EP-02 / #22 — source-linked Python results and run manifests

Implements ratified [ADR-P07](../../spec/results/proposals/ADR-P07.md), accepted
at reviewed `bc662d3`, after merged [PR #64](https://github.com/DRAGGON-Lab/FENIX/pull/64).
The branch starts at merged main `da66b3cea2c997a28f2b79d45e5e05e4362d8d97`.
Human implementation review remains pending. Issue #22 stays open; #29, #42 and
the parent epic retain separate gates.

## Scope and behavior

`fenix.results.run_experiment` revalidates the exact committed Design/Experiment
pair through the existing compiler, executes a normalized FIR copy with the
unchanged P04 executor, and captures immutable `RunRecord`, `RunManifest` and
`ODEResult` values. Result columns follow P03 order, with explicit mapped state
IDs and units. Failures propagate without a success record. Zero-only grids skip
integration with zero counters. Build ID is null; installed producer/backend
versions and actual counters are recorded. Wall/monotonic observations bracket
source revalidation through result serialization/checksum.

`RunRecord.from_json` strictly decodes results-local numeric tokens, checks full
source references and recompiled FIR identity, settings, dimensions, units,
column ordering, initial states, bitwise grids/direct observables and exact result
byte SHA-256. It retains original manifest text and result bytes. The caller can
supply an external trusted manifest checksum. Readback never executes a solver,
replaces recorded environment observations or resolves remote sources.

No changes to `solve_ode`, P01–P04, scientific identities, units, dependency
manifests, approved fixtures or previous receipts. No archives, filesystem API,
new runtime dependencies, Julia results or build-ID generation. The protected
input audit compared all 524 existing tracked files outside the three intended
workflow/product/package-documentation edits byte-for-byte against merged main.

## Tests and independent review

The initial test-first check failed with the expected missing `fenix.results`
module. The final 19 new test methods run in ordinary package discovery, covering
both real SciPy methods, zero/late grids, empty/noncanonical multi-observables,
all four accepted artifact pairs and fixed hashes, byte-preserving round trips,
signed zero/subnormals/max-finite/ties-even binary64, exact large integers
including 6,000 digits, and field-specific token rejection. Negative controls
cover malformed UTF-8/Unicode/JSON, duplicate escaped keys, missing/unknown
members, versions/profiles, counters, options/seeds, every source/FIR reference,
wrong same-FIR source contexts, grid bits, dimensions, IDs, units, mappings,
observable samples, initial state, immutability and corrupt committed sources.

Readback solver/environment traps, compiler/solver failure propagation and
clock/compilation/serialization ordering are explicit regressions. The tests
also demonstrate the trust limit: plausible positive-time sample alteration
with recomputed internal checksums can pass; a trusted external manifest
expectation detects that alteration. This does not establish numerical
correctness, execution authenticity, authorship or biological validity.

Independent engineering and scientific reviewers each reran all 19 focused
methods and reported no remaining findings. Both reproduced an extreme-exponent
bug in the first implementation: Decimal's exponent limit leaked
`InvalidOperation` for valid JSON numeric tokens. Lexical significand inspection
now preserves exact signed zeros with enormous exponents and rejects nonzero
underflow as `ResultValidationError`; public regressions include ties to even.
The reviewers checked source/FIR boundaries, timing scope and non-executing
readback. Their full-package/wheel/hosted checks were NOT RUN; owner checks below
are separate. Agent review does not supply human implementation approval.

## Executed verification

The [machine-readable receipt](ep02-python-results.json) records exact command
argument vectors, exit codes, environment, source/artifact hashes, log
hashes/excerpts, independent review scope and observed DOP853/Radau artifact
pairs. These observed captures are execution receipts, not new golden fixtures
or authenticated attestations. Full temporary logs/helper snapshots are in
ignored `artifacts/ep02-22/`; nothing rewrites historical evidence.

Environment: macOS 15.7.9 x86_64, CPython 3.12.13, uv 0.11.29, NumPy 2.5.5,
SciPy 1.18.1, rfc8785 0.1.4, Ruff 0.17.5, mypy 2.4.1 and Julia 1.10.13.
All receipt-wrapper checks set `UV_CACHE_DIR=/tmp/fenix-uv-cache` and unset
macOS `__PYVENV_LAUNCHER__` in the child environment. Commands below ran from the
repository root. Long Ruff commands use the exact CI targets, including the
new module/tests, as retained in the JSON receipt.

| Command | Outcome |
|---|---|
| `uv sync --project packages/python --locked` | PASS; original 69 package tests pass |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 88 methods, including 19 results methods |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS; 2 methods, 29 approved projections |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS; 3 methods, original 92 P01 cases and 97-case rejection subset |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS; 3 methods, 207 rejection cases, 84 canonicalization cases and 9 compiler controls; sets overlap |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/document links, not science |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| Ruff check and format on the exact expanded CI targets | PASS; 25 files |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml` | PASS; 14 production modules, strict |
| `uv run --project packages/python --locked --offline python spec/results/proposals/review_p07.py` | PASS; independent bounded reference audit, no native implementation imports |
| `uv build --project packages/python --offline` | PASS; sdist and wheel |
| `uv venv --python 3.12 --offline /tmp/fenix-22-wheel` | PASS; fresh environment |
| `uv export --project packages/python --locked --offline --no-dev --no-emit-project -o /tmp/fenix-22-runtime.txt` | PASS |
| `uv pip install --python /tmp/fenix-22-wheel/bin/python --offline --require-hashes -r /tmp/fenix-22-runtime.txt` | PASS; only locked runtime dependencies |
| `uv pip install --python /tmp/fenix-22-wheel/bin/python --offline --no-deps packages/python/dist/fenix_bio-0.0.0-py3-none-any.whl` | PASS |
| `/tmp/fenix-22-wheel/bin/python /tmp/fenix-22-wheel-provenance.py` | PASS; site-packages source hash matches reviewed source, development tools absent |
| `/tmp/fenix-22-wheel/bin/python -m unittest discover -s packages/python/tests -v` | PASS; all 88 methods |
| `/tmp/julia-1.10.13/bin/julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 scaffold assertions; no Julia results/ODE claims |
| `python3 /tmp/fenix-22-artifact-audit.py` | PASS; final sdist source/tests/README/project and wheel source match checkout bytes |
| `python3 /tmp/fenix-22-protected.py` | PASS; 524 protected existing files unchanged |
| `packages/python/.venv/bin/python /tmp/fenix-22-capture.py` | PASS; actual DOP853/Radau capture/readback with trusted expected manifest hashes |
| `git diff --check` | PASS |

Five first wrapper-driven import/type checks failed because the inherited macOS
launcher variable selected a system Python prefix. Removing it fixed replay
without changing the package. Failed attempts are retained separately. Ruff
format also initially failed on a newly edited test helper, then passed after
formatting. Initial unused mypy ignore annotations and test helper mistakes were
corrected; no contract expectation, fixture or numeric threshold was weakened.

Source SHA-256 for `results.py`:
`be5b5cb8eb84aafce6da5e967e1b786838a69bea04687f9d4730cc596e8bd3e6`.
Tests SHA-256:
`595456737a1e2ecf7de93ef235cdb686997df0197a2336bda8707b8a4c83a0f9`.
The JSON source fingerprint excludes this evidence pair to avoid self-reference.
Final distributions were rebuilt after the last test formatting edit; the wheel
was reinstalled with `--reinstall --no-deps`, then provenance and all 88 methods
passed again. Exact final artifact hashes and member comparisons are in the JSON.
The clean wheel has exactly fenix-bio, NumPy, SciPy and rfc8785 installed.
Capture's null build ID accurately reflects the unidentifiable editable/build
snapshot; no checkout revision is inferred at runtime.

**NOT RUN:** human implementation approval, Julia results/ODE implementation,
independent cross-language #29 evidence, broader #42 provenance and systematic
#59 generated-input investigation. Hosted CI for this implementation branch is
observed separately after push. Scientific references remain bounded; package
and readback checks do not establish biological validity or identical rerun bytes.

## Non-blocking review disposition

The user-supplied review found no confirmed correctness defect that should block
PR #65 within the approved M0 scope. The following engineering observations are
recorded for human implementation review; they do not constitute merge approval.

**Maintainability:** `results.py` currently keeps strict transport parsing,
semantic validation, immutable value construction and execution capture in one
cohesive module, separated by functions. Reconsider extracting the strict JSON
decoder when another results profile is added. Extraction is deferred from this
PR to avoid unnecessary churn within its bounded M0 scope.

**Numerical and provenance guarantees:** P07 establishes artifact consistency.
Plausible altered positive-time samples with recomputed internal checksums can
pass readback. The existing
[native regression](../../packages/python/tests/test_results.py),
`test_plausible_altered_positive_samples_pass_only_internal_checks`, demonstrates
this behavior and rejection against an external trusted manifest checksum.
That external expectation detects alteration against the trusted artifact; it
does not prove solver execution or numerical correctness. This is the ratified
trust boundary, and requires no behavior change in this PR.

Independent Python–Julia numerical conformance remains
[#29](https://github.com/DRAGGON-Lab/FENIX/issues/29); stronger provenance remains
[#42](https://github.com/DRAGGON-Lab/FENIX/issues/42); generated-input investigation
remains [#59](https://github.com/DRAGGON-Lab/FENIX/issues/59). These observations
do not expand PR #65 or close those follow-ups. The original machine-readable
receipt and its source/artifact hashes remain unchanged.

Follow-up verification: **PASS** for
`UV_CACHE_DIR=/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python scripts/check_repo.py`,
`UV_CACHE_DIR=/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v`
(six tests), and `git diff --check`. Package, numerical and wheel suites were
**NOT RUN** for this documentation-only disposition; their earlier executed
outcomes above remain historical.

## Current integration addendum — 2026-11-16

All preceding receipt and review statements describe their recorded revisions.
The [PI-directed #22 closure](https://github.com/DRAGGON-Lab/FENIX/issues/22#issuecomment-6929801138) occurred at 21:23:45 UTC while PR #65 was unmerged. PR #65 then merged at 21:30:16 UTC as `32acf4f4b51e257c7efed65203360e5e9ee83598`. [Post-merge CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581) passed all seven jobs. The Python M0 path is implemented on main, including P07 capture/readback.

This supersedes earlier availability/pending-review status, without changing the original machine-readable receipt, source/artifact hashes or scientific claims. Julia remains a scaffold. Independent Python–Julia scientific conformance (#29), stronger provenance/archive demonstration (#42), generated-input investigation (#59), P06 governance and final EP-02 PI/release acceptance retain separate scopes. P07 establishes bounded artifact consistency, not execution authenticity, authorship, biological validity or guaranteed exact numerical replay. See the [maintenance audit and action log](ep02-status-governance.md).
