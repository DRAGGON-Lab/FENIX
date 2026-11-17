# EP-03 / #27 — native Julia run manifests and typed results

Refs [#27](https://github.com/DRAGGON-Lab/FENIX/issues/27). Base:
`82a9b64b45576c298096d48a532a9ea2bdc55c42`, merged proposal PR #71;
branch `feat/27-julia-results`. Authority: ratified [P07](../../spec/results/proposals/ADR-P07.md),
its [Julia/SciML supplement](../../spec/results/proposals/ADR-P07-Julia.md),
P01–P04 and unchanged approved mathematical/reference catalogs.
**Native implementation supplied; separate human implementation acceptance PENDING.**

The human PI explicitly approved the proposal supplied at reviewed revision
`0156143b7555405d8bf00ea9917f4badddf1ceeb` and instructed continuation:

> ok Iapproved and  merged the proposal, continue with the code implementation

The supplement's ratification record identifies the approval and reviewed scope.
It authorizes this separate implementation PR; it does not supply implementation
acceptance, #29, parent epic acceptance or release authorization. Approved
schema/example JSON and historical receipts remain unchanged. The independent
reference lock remains unchanged; Pkg refreshed only the native test lock's Fenix
dependency list to add standard-library Dates. Package versions are unchanged.

## Implemented boundary

`Fenix.Results` exposes immutable `RunRecord`, `RunManifest`, `ODEResult` and
`ResultValidationError`, validated `run_experiment` capture and
`from_json(RunRecord, manifest, bytes; experiment, expected_manifest_sha256)`
readback. Capture observes wall/monotonic clocks before source revalidation,
recompiles the exact local pair, normalizes a FIR copy and solves once. Result
serialization and its exact-byte hash precede finish observations; manifest
assembly follows. UTC timestamps pad millisecond wall observations to six
fractional digits, while elapsed seconds use monotonic observations. Backward
wall adjustments are accepted. Source, FIR and standalone solver APIs are unchanged.

Successful manifests record actual method/settings/counters and installed
runtime/package versions. Jacobian `njev` and W-matrix `nw` keep their SciML
meanings; `nw` is never called `nlu`. Current installed metadata cannot identify
a build reliably, so native capture uses `build_id:null`. Compiler/solver errors
propagate and yield no successful record, fallback or partial substitute.

Readback handles both approved Python/SciPy and Julia/SciML profiles, preserving
recorded producer/build/environment observations. It recompiles supplied local
sources, checks every source reference even for same-FIR alternatives, FIR
identity, profiles/settings/counters, exact result hash and optional trusted
manifest hash. Grids and direct observable values agree bit for bit; complete
normalized interfaces, units, dimensions and zero-time initial state are checked.
It never executes an ODE, queries Git or resolves sources over a network.

The private token-preserving PortableJSON path leaves public P01/P03 policies
unchanged. Numeric fields decode directly from lexemes: binary64 retains signed
zero/subnormals and rejects overflow/nonzero lexical underflow; integer fields
require integer-form spelling with no native Int readback cap. Frozen integer
storage uses decimal strings, avoiding mutable BigInts. Exports create fresh
BigInts and nested containers. Original validated result bytes use immutable
String storage and return a fresh byte vector. Original manifest text is retained.
There is no public arbitrary-trajectory attachment constructor.

## Numerical and transport evidence

The separate pinned native-results runner checks all four accepted Python and
four accepted Julia examples, original formatting/newlines and trusted checksums,
closed shapes, wrong exact sources, grids/counters/units/mappings/dimensions and
recorded observations. A fresh child Julia process traps both native solver
entry points during all eight readbacks. It asserts the loaded package source
and uses the pinned active SciML environment without LOAD_PATH overrides.

Capture is checked against all 40 fixed independent analytical samples using
Tsit5 and Rodas5P at baseline and refined P04 settings: **160** sample/method/
setting comparisons. Binary64 samples convert exactly to 512-bit BigFloat and
are compared against fixed approved decimals under unchanged
`1e-9 + 1e-8*abs(reference)` molecules. Capture's own sample bits must survive
transport; a separate numerical rerun need not reproduce those bits.

| Method | Setting | Maximum fraction of P04 acceptance bound |
|---|---|---:|
| Tsit5 | baseline | 2.715112e-4 |
| Tsit5 | refined | 3.931062e-5 |
| Rodas5P | baseline | 3.983489e-4 |
| Rodas5P | refined | 4.561313e-5 |

Baseline uses rtol=1e-10, atol=1e-12, maximum step=1s; refined uses 1e-11,
1e-13, 0.5s. Every RHS budget is 100000. The existing native ODE suite was also
rerun, including its coarse study and stiff exploratory control. No oracle was
regenerated or threshold weakened. Joint refinement is evidence at fixed
samples, not a global error certificate or method-order estimate.

Fixture-independent package regressions include **395** results assertions and
**77** additional private parser assertions. They exercise numeric token forms,
large integer GMP mutation isolation, signed-zero/subnormal/midpoint transport,
malformed JSON/Unicode/duplicates, both backend payloads, immutable/fresh exports,
failures and clocks. A copied standalone package runs with `PATH=/nonexistent`
and explicit assertions that neither Python nor Python3 is discoverable.

Separate engineering and numerical reviewers found no blocking production
findings. Engineering replayed the native suite. Numerical review independently
recomputed all 160 reported errors from captured bits using 180-digit Decimal
arithmetic against the fixed references, including exact coverage checks. Review
identified two test-quality defects: a helper repaired deleted checksum fields,
and a nested-integer assertion inspected Pair containers rather than contents.
The controls now invoke readback directly and recursively inspect storage, with
GMP mutations of budget, maxiters and backend counter exports. These are agent
reviews; neither substitutes for human implementation acceptance.

## Verification outcomes and limits

The [machine receipt](ep03-julia-results.json) records exact commands, exit
statuses, runtime/source/schema/catalog/lock fingerprints, log/report hashes
and actual PASS/FAIL/NOT RUN outcomes. The separate generated native report
records all 160 rows and eight example pairs. CI uploads it as
`julia-native-results`, alongside existing independent reference artifacts.

Executed checks cover repository/harness, both native package suites, native
Julia content/documents/FIR/ODE/results, standalone Julia without Python,
independent Python/Julia analytical and rejection reports/comparisons, the exact
rational mathematical audit, original/profile audits and an independent source
mutation digest audit. Historical proposal audits retain drafting-era
PROPOSED/PENDING output labels; the explicit PI ratification record governs their
approved scope. They are not a new approval or a replacement for native evidence.

Initial failures are retained in the receipt: the parser's red regression
confirmed its missing private API; a native test used a nonexistent BioIR
`from_dict` factory and was corrected to the existing typed constructor; two
unit test helpers did not initially exercise the intended mutations; and three
legacy native suites were launched before package instantiation had completed.
Those dependency-order failures were rerun after installation. No production
semantic expectation was repaired to pass a test.

Checksums establish artifact consistency against supplied expectations, not
execution authenticity. Plausible altered positive-time values with recomputed
untrusted checksums can pass readback. Bounded analytical agreement does not
prove biological validity, exhaustive numerical reliability or #29 acceptance.
SSA, archives/signatures, package/version governance, parent epic acceptance and
release authorization remain outside scope. No merge or issue closure is automatic.
