# EP-03 / #25 — native Julia M0 BioIR-to-FIR compiler

Refs [#25](https://github.com/DRAGGON-Lab/FENIX/issues/25). Base: merged #24,
`79b75a21149c`, on `feat/25-julia-compiler`. The human PI accepted the bounded implementation at reviewed revision
`da13860b78e08928276009fb7e386e98ef271be0` on 17 November 2026; see the
[acceptance record below](#human-pi-implementation-acceptance--2026-11-17). No contract, approved fixture, Python implementation,
package version or historical verification receipt changes are included.

## Behavior and scope

`Fenix.compile_experiment` reverifies native committed Design/Experiment sources
through P01, binds production/decay function roles to `alpha`/`beta` independently
of names/order, and emits immutable P02 mathematical FIR. It preserves represented
values and named observables, including empty observables, without a volume factor.
Producer provenance includes exact source digests, complete symbol maps and the
provisional package name and actual installed version. Source checks cover units,
assignments, initial counts, function targets and exhaustive observable agreement.

`Fenix.FIR` provides validating constructors/factories, fresh exports, standalone
models/documents and explicit source/capability checks. P03 parses all numeric
tokens directly to binary64; P01 retains its existing default and token limits.
Native FIR numeric fields require finite `Float64`. Validation precedes sorting;
normalization copies and sorts only six ratified declaration collections using
UTF-16 keys. Model bytes and wrapped identity bytes remain distinct; only identity
bytes enter the digest. Provenance is excluded. No algebraic repair occurs.

Scientific authority is ratified [P02](../../spec/fir/proposals/ADR-P02.md),
[P03](../../spec/canonicalization/proposals/ADR-P03.md) and unchanged independent
approved catalogs. Solvers, SSA execution/eligibility, broader FIR mathematics,
empirical validity and whole-project release authorization remain outside scope.

## Executed evidence

Julia **1.10.13**, CPython **3.12.13**, uv **0.11.29**, Node **24.18.0**.
The [machine receipt](ep03-julia-compiler.json) records exact commands, outcomes,
log hashes, report identities and a source fingerprint. Local Julia uses
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and `JULIA_PKG_OFFLINE=true`;
uv uses the locked offline environment after cached installation.

- **PASS:** package `Pkg.instantiate(); Pkg.test()`, retaining existing builder,
  parser and committed-document coverage; new FIR/compiler regressions include
  mutation isolation, roles/names/order, numeric boundaries, metadata, volume,
  empty observables and source mismatches.
- **PASS:** all **207** approved rejection cases, with exact outcome/category/
  JSON Pointer/input-document labels; reference-only stage labels remain outside
  the native API.
- **PASS:** all **84** P03 cases, including exact normalized objects, model bytes,
  identity bytes/digests, idempotence and round trips.
- **PASS:** native compilation of all **nine** accepted producer controls against
  fixed source/FIR references, independent output schema and source validation.
- **PASS:** **ten** exact binary64 triples compiled and extracted; bits, units,
  signed stoichiometry and exact AST templates checked before the unchanged Julia
  oracle evaluates all **40** fixed samples at **512/1024 bits**, with 70-digit
  precision stability. This is a compiler/oracle bridge, not numerical integration.
- **PASS:** standalone package copied outside the repository, with `PATH=/nonexistent`
  and explicit assertions that neither `python` nor `python3` is discoverable.
- **PASS:** existing 29 Julia content projections, 92 original P01 and overlapping
  97 P01 rejection document cases, repository checker/harness, Python package and
  native FIR suites, both independent P01/rejection/oracle references and report
  comparisons, exact-rational oracle audit, both P03 serializers and comparisons,
  and reference harness regressions.
- **PASS:** evidence output protection for fixtures/sources, live and dangling
  symlinks, dangling parent directories and hardlinks (**10** regression assertions).

Catalog sets overlap and are bounded. Historical `NOT_RUN` rows remain intact;
new observations live in the separate native report, uploaded by Julia CI.
The report fingerprints runtime, sources, catalogs, evaluators, contracts and
locked reference dependencies. Hashes are integrity evidence, not authentication.

## Review disposition

Independent engineering review found one report-output overwrite risk. The
writer now validates destinations before execution, confines in-repository output
to `artifacts/`, resolves symlinks and rejects dangling/hardlink aliases. Independent
recheck passed all ten regressions; no engineering findings remain.

A separate reviewer found no blocking scientific issues in FIR/compiler/source
checks or the oracle bridge and independently reran conformance. That reviewer
implemented the parser policy, so the independent scientific review excludes the
parser implementation; engineering review includes it. Agent reviews do not
substitute for human PI acceptance. Hosted CI status is recorded separately in
the PR; this local receipt does not assert hosted execution or merge approval.


## Human PI implementation acceptance — 2026-11-17

The human PI approved reviewed implementation revision
[`da13860b78e08928276009fb7e386e98ef271be0`](https://github.com/DRAGGON-Lab/FENIX/commit/da13860b78e08928276009fb7e386e98ef271be0)
on [PR #69](https://github.com/DRAGGON-Lab/FENIX/pull/69), following the reported
verification and review disposition, instructing in this conversation:

> I approve this, record this desicion and push it to the PR

Decision: **ACCEPTED** for the bounded issue #25 native Julia M0 FIR/compiler
implementation described above. The reviewed [hosted CI run](https://github.com/DRAGGON-Lab/FENIX/actions/runs/44098146298)
passed all seven jobs, including native FIR/compiler conformance and artifact
upload. Approval is the explicit human instruction, separate from those checks
and agent reviews; no independent GitHub review submission is inferred.

The adjacent JSON receipt remains unchanged as historical execution evidence:
its source fingerprint, pending-acceptance state and pre-push hosted-CI
`NOT RUN` entry describe the time it was recorded. This addendum records the
later human decision without rewriting those observations.

Acceptance changes no scientific contract, approved fixture, implementation API,
package version or mathematical semantics. Native numerical execution, SSA,
independent cross-language acceptance, parent EP-03 and broader release gates
remain separate. This instruction authorizes recording and pushing the decision;
merge and issue-state changes remain separate actions.

Documentation-only recording checks: repository checker, harness unit tests and
`git diff --check` **PASS**. Scientific suites were not rerun for this acceptance
addendum; the source-linked implementation results above remain the evidence.
