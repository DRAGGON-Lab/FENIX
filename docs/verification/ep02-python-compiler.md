# EP-02 / #20 — native Python M0 BioIR-to-FIR compiler

Issue [#20](https://github.com/DRAGGON-Lab/FENIX/issues/20), parent #4.
Implementation starts from merged PR #60, main
`e18245573a01d1a8ed68dba58741229eb51a28e0`, on
`feat/20-python-bioir-fir-compiler`. All listed upstream issues (#13, #15, #16,
#19) were closed before implementation. Human implementation review remains pending.

## Delivered behavior and boundaries

`fenix.compiler.compile_experiment` accepts a verified immutable Experiment,
rechecks exact P01 source identities, resolves function roles independently of
source names/order, and produces validated immutable FIR. Model fields include
exact P02 stoichiometry/flux/RHS templates, binary64 initial/rate values, units,
exhaustive named observables, fixed assumptions and ode=true/ssa=false. There is
no volume multiplier, unit conversion, inferred biological default or expression
execution. Compiler provenance includes both source digests and complete state/
parameter symbol maps. Author metadata and execution settings are not copied.

`fenix.fir` supplies validated immutable FIRModel/FIRDocument factories with fresh
serialization, standalone mathematical validation and separate exact source checks.
P03 normalization copies and sorts only the six approved declaration arrays by
UTF-16 ordering. Model bytes are JCS(N(model)); identity bytes contain the exact
fenix.fir/0.1.0 wrapper. SHA-256 hashes identity bytes. Provenance is excluded;
observable IDs and every other semantic field remain included. Canonical model
readback, idempotence and permutation behavior are tested. No general algebraic
simplification, equivalence or stochastic propensity support is inferred.

The shared private JSON parser now has an explicit P03 mode: all numeric tokens
resolve directly to binary64. Its default remains P01, with the unchanged safe
integer-token bound. Programmatic FIR mathematical numbers require finite native
floats; the compiler explicitly resolves already validated BioIR quantities.
The [package README](../../packages/python/README.md) documents APIs and diagnostics.

No solver, numerical tolerance/failure rule, SSA eligibility, community mechanism,
persistent archive or authenticated provenance is implemented. Numerical execution
remains #21/P04 work; results remain #22/P07. Verified digests are not proof of
origin or researcher authorization. Global history and concurrent branch control
remain outside scope. Systematic generated-input testing remains #59. No empirical
biological validity or cross-language compiler parity is established here.

## Fixed evidence, independence and provenance

The native FIR suite executes all **207** approved rejection cases, checking
outcomes/categories/document paths/supplied-input identities; reference-only stage
labels are not added as a native API. It also executes all **84** canonicalization
cases: 27 binary64 JCS, 27 generic JSON JCS, 13 FIR identity and 17 contract controls.
The 13 identity vectors check expected normalized objects, model bytes, identity
bytes and fixed SHA-256 values, plus idempotence/readback. The 17 controls include
raw parsing scalars as well as invalid FIR; adapters dispatch the intended operation
without implementing semantics. All **9 accepted producer/source controls** check
compiled models and identity, complete source validation and ratified schema output.
These sets overlap and must not be added as unique independent scientific examples.

The existing content and document suites remain unchanged and pass (29 content
projections; original 92 P01 and 97-case P01 subset with schema checks). Package
regressions cover renamed/misleading source parameter names, reorderings, zero
rates, fractional/empty observations, signed zero/subnormals/large floats, immutable
nested storage, fresh copies, excluded provenance and unsupported capabilities.

Production does not read schemas/fixtures or import reference validators. Python
production and reference serialization share rfc8785; their agreement alone is not
independent canonicalizer evidence. Approved fixed bytes and independent Julia/
Node audits provide additional bounded evidence. No approved fixture, catalog,
contract, reference evaluator or lockfile is changed. Both retained rejection
reports were regenerated and verified to differ only in the Python configuration
fingerprint; every one of their 207 rows and all other fields remain unchanged.
Historical reference reports and their NOT_RUN rows retain their meaning. Native
validation/normalization outcomes appear in this new record, not retroactively in
legacy reports. Initial failing regressions were recorded before implementation.
Three intermediate native test-adapter failures routed raw scalar controls through
FIR loading or failed to catch a primitive Unicode rejection; routing was corrected
without changing production scientific behavior or expected fixtures.

## Execution and review

The [machine-readable receipt](ep02-python-compiler.json) contains exact commands,
UTC times, exit codes, output excerpts, log hashes, runtime/dependency versions,
per-file SHA-256 source hashes, source identity and artifact hashes. Verification
ran dirty on the main revision above. The aggregate fingerprint hashes sorted
relative path + NUL + file bytes + NUL, excluding this evidence pair to avoid
self-reference. Full logs remain in ignored `artifacts/ep02-20/`. Earlier evidence
records are preserved as historical source snapshots.

Environment: macOS 15.7.9 x86_64; Python 3.12.13, uv 0.11.29, Ruff 0.17.5,
mypy 2.4.1, jsonschema 4.26.0, rfc8785 0.1.4, Julia 1.10.13, Node 24.18.0.
uv uses `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia uses the existing
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia`. Dependencies were available from local cache.

Final local outcomes are PASS (exit 0), as recorded individually in the receipt:

- Editable and clean-wheel package tests: 46 methods each; native FIR: 3 methods
  covering 207/84/9 controls; existing document/content suites: 3/2 methods.
- Ruff lint/format: 21 files; strict mypy: all 12 production modules.
- Source/wheel build; locked runtime export/install; wheel audit confirming only
  fenix-bio/rfc8785 installed, py.typed, and installed compiler/FIR source equality.
- Original P01 Python tests: 8, Python/Julia reports/comparison: 92 cases, Node
  byte/digest audit: 41.
- Rejection Python tests: 10; Julia reference/harness: 268/45 assertions;
  independent 207-case reports/comparison and Node digest audit: 144.
- P03 reference Python/Node tests: 15/5, reports and comparison. Their historical
  17 contract-only rows remain NOT_RUN in those serialization-only reports.
- Existing production-decay reference Python/Julia tests: 16/648 assertions,
  rational audit of 40 samples, reports/comparison of 160 computations agreeing
  at 70 significant digits. These checks do not imply a new numerical executor.
- Julia library smoke: 2 assertions; repository/link checks; harness: 6 methods;
  YAML syntax; protected-artifact/retained-row audit; working/staged whitespace.

Separate engineering and scientific reviewers inspected actual code and executed
focused checks. Both found no confirmed correctness defects. Engineering also
verified the clean wheel and source equality; scientific review checked ratified
mathematics, roles, normalization and identity boundaries. These bounded agent
reviews are not human PI approval or exhaustive generated-input validation.
Hosted CI is observed separately on the PR. No automatic merge, package release,
parent epic closure or subsequent delivery is included.

## Review follow-up: limits and retained-report hashes

This documentation/tracking follow-up starts from `d64d019` on PR #61. It changes
only this record, the [Python README](../../packages/python/README.md#compiler-guarantees-and-evidence-limits)
and the [rejection verification page](ep01-rejections.md#ep-02-compiler-configuration-provenance-refresh).
Production code, public APIs, tests, dependencies, scientific contracts, approved
fixtures, retained report bytes and original execution receipts remain unchanged.
No solver work, report regeneration, implementation approval, merge, parent epic
closure or start of #21 is included.

- **Compiler correctness versus solver correctness:** #20 emits validated
  mathematics but does not execute the ODE or compare library-produced
  trajectories against the analytical oracle. The earlier production-decay oracle
  checks validate reference evidence. Numerical execution remains
  [#21](https://github.com/DRAGGON-Lab/FENIX/issues/21)/P04, followed by the
  independent scientific gate in [#29](https://github.com/DRAGGON-Lab/FENIX/issues/29).
- **FIR identity versus biological equivalence:** matching FIR means matching
  the complete resolved M0 mathematical model and named observable interface.
  It does not establish identical experimental biological behavior. BioIR array
  order remains identity-significant under P01; P03 normalizes only the six FIR
  collections `states`, `parameters`, `reactions`, `observables`, `equations` and
  `assumptions`. Reordering BioIR declarations can change source digests/maps
  while preserving the compiled FIR identity; source agreement remains a separate
  check.
- **Bounded conformance:** fixed cases do not exhaust interactions among numeric
  boundaries, declaration permutations and source mappings. Generated-input and
  metamorphic investigation remains outstanding under
  [#59](https://github.com/DRAGGON-Lab/FENIX/issues/59), with #20 as the prerequisite
  for FIR normalization/compiler-source interactions. Its existing BioIR,
  replay/minimization and independent-reference obligations remain in force.
  This work does not retroactively block #20 or select a framework/dependency.

The rejection page now labels the P01-refresh hashes as historical and declares
the current #20 report hashes beside direct artifact links. Both current hashes
agree with artifact bytes and the original [compiler receipt](ep02-python-compiler.json).
Earlier execution evidence and receipt contents are preserved. Future regeneration
must update the current declarations and verify them against artifact bytes.

Tracking updates were applied and read back through the GitHub API:
[#59](https://github.com/DRAGGON-Lab/FENIX/issues/59) retains its original BioIR
acceptance notes and adds the FIR/compiler interaction requirements above;
[PR #61](https://github.com/DRAGGON-Lab/FENIX/pull/61) records all three limits,
the corrected artifact references and #59 linkage. Both remain open; the PR is
unmerged and human implementation approval remains separate.

### Follow-up verification, separate from original execution

Executed on **2026-11-16 UTC**, with HEAD
`d64d0192aeecbf52f42d55133c802bcf94f56e07` and the three Markdown files dirty.
Runtime: Python 3.12.13 and uv 0.11.29. All uv commands below use
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache` and locked offline dependencies.
The sorted path + NUL + bytes + NUL SHA-256 over **488 tracked files**, excluding
`docs/verification/ep02-python-compiler.md`, is
`a9d448623472f58d254724c96dc4a92f2f0e240f5a736b0ee4d0539c0dbb2954`.
This fingerprints the follow-up source state without self-reference; it does not
replace the original receipt's source identity. No new regression test is added
for this prose correction; the existing positive/negative suites are retained.

| Exact command | Fresh outcome |
|---|---|
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv sync --project packages/python --locked --offline` | PASS (exit 0); 14 packages checked, no dependency change |
| `python3 /private/tmp/fenix-20-followup-audit.py` (complete source below) | PASS (exit 0); both current declarations equal report SHA-256 and original receipt entries; exactly three Markdown changes; all protected tracked files unchanged from `d64d019`; original compiler evidence preserved byte-for-byte as a prefix |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare docs/verification/rejections-python.json docs/verification/rejections-julia.json` | PASS (exit 0); 207 fixed expectations, APPROVED; compares retained bytes without report generation |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS (exit 0); repository consistency and local links, not scientific conformance |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS (exit 0); 46 tests |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS (exit 0); 3 methods covering the overlapping 207 rejection, 84 canonicalization and 9 producer/source controls |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS (exit 0); 6 harness tests |
| `git diff --check && git diff --cached --check` | PASS (exit 0); working and staged whitespace |

Fresh wheel build/install/tests, numerical solver execution, systematic generated
inputs and broad Python/Julia reference execution: **NOT RUN** in this follow-up.
The historical results above remain historical. No check in this follow-up
establishes solver correctness, biological equivalence or exhaustive conformance.
Hosted checks for the new commit are observed separately on PR #61.

Reproduce the hash and unchanged-file audit from the repository root by saving
this exact source to `/private/tmp/fenix-20-followup-audit.py` and running the
command above (valid before or after the follow-up commit):

```python
import hashlib
import json
import re
import subprocess
from pathlib import Path

baseline = "d64d019"
allowed = {
    "packages/python/README.md",
    "docs/verification/ep01-rejections.md",
    "docs/verification/ep02-python-compiler.md",
}
changed = set(subprocess.check_output(
    ["git", "diff", "--name-only", baseline], text=True
).splitlines())
assert changed == allowed, changed
assert not subprocess.check_output(
    ["git", "ls-files", "--others", "--exclude-standard"], text=True
).strip(), "Unexpected untracked files"
subprocess.run([
    "git", "diff", "--exit-code", baseline, "--", ".",
    *[":(exclude)" + path for path in sorted(allowed)],
], check=True)
record_path = "docs/verification/ep02-python-compiler.md"
original = subprocess.check_output(["git", "show", baseline + ":" + record_path])
assert Path(record_path).read_bytes().startswith(original), "Earlier evidence rewritten"
page = Path("docs/verification/ep01-rejections.md").read_text()
current = page.split("## EP-02 compiler configuration provenance refresh", 1)[1]
receipt = json.loads(Path("docs/verification/ep02-python-compiler.json").read_bytes())
for label, language in (("Python", "python"), ("Julia", "julia")):
    path = "docs/verification/rejections-" + language + ".json"
    pattern = (r"\| \[" + label + r"\]\(rejections-" + language
               + r"\.json\) \| `([0-9a-f]{64})` \|")
    declarations = re.findall(pattern, current)
    actual = hashlib.sha256(Path(path).read_bytes()).hexdigest()
    assert declarations == [actual], (path, declarations, actual)
    assert receipt["artifacts"][path] == actual, path
    print("PASS:", path, actual, "matches current declaration and receipt")
print("PASS: exactly three Markdown files changed; all protected tracked files unchanged")
print("PASS: original compiler evidence preserved as an exact byte prefix")
```
