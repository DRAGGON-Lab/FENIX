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
