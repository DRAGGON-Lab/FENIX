# Approved FENIX Architecture v0.1 decisions

**Ratified 2026-11-14:** D01–D29 accepted; Decision 30 approved architecture. These are binding principles, not substitutes for precise mathematical ADRs.

| Decision | Policy |
|---|---|
| D01 | New portability-first FENIX; LOICA 2 ideas are reference, not canonical implementation. |
| D02 | Separate versioned BioIR and resolved mathematical FIR. |
| D03 | Independent native Python and Julia compilers; one normative specification. |
| D04 | Typed declarative biological functions, portable safe expression AST. |
| D05 | Nested BioIR biological hierarchy; initially well-mixed execution. |
| D06 | ODE first; restricted direct SSA follows. |
| D07 | Julia runs directly through SciML; Catalyst optional later. |
| D08 | Identical canonical FIR; ODE numerical and SSA statistical conformance. |
| D09 | Count-space states; seconds/litres; per-cell intracellular, total extracellular. |
| D10 | Clean break from LOICA 2 APIs, formats and migration. |
| D11 | One monorepo; independently installable Python and Julia packages. |
| D12 | Independent BioIR, FIR, Python and Julia versions; compatibility matrix. |
| D13 | Contract-first AI collaboration and human approval for scientific changes. |
| D14 | M0 production/degradation; M1 sender/receiver community. |
| D15 | Separate BioIR Design/Experiment, execution/results separate. |
| D16 | Immutable revisions, stable IDs, exact content-verified design references. |
| D17 | Optional export-first SBOL3/SBML, then SED-ML/OMEX; imports later. |
| D18 | Portable observables/data bindings; external datasets; optional inference. |
| D19 | Dual-level biological design and scenario optimization; FIR never mutated. |
| D20 | Portable declarative objectives/constraints, hard vs soft, multiobjective. |
| D21 | Measure benchmark baselines at M0/M1; optimize after correctness. |
| D22 | Extension-ready capabilities; validated sensitivities/hybrid/spatial later. |
| D23 | Mathematical and numerical evidence mandatory; empirical for predictive claims. |
| D24 | Lightweight run manifests automatic; optional archival bundles. |
| D25 | Staged pre-releases; stable only after ODE+SSA scientific gates. |
| D26 | Language-neutral spec and independent mathematical fixtures are authoritative. |
| D27 | Backend-independent FIR explicitly contains supported ODE/SSA semantics. |
| D28 | FIR digest covers only canonical mathematical semantics, not provenance. |
| D29 | RFC 8785/JCS with versioned FENIX semantic normalization and reference vectors. |

**Current implementation and remaining gates:** Python’s supported M0 path is implemented on main through merged PRs #58/#60/#61/#63/#65; #18–#22 are closed. This is separate from the historical contract/reference approvals below. [EP-02](https://github.com/DRAGGON-Lab/FENIX/issues/4), the bounded native Python M0 implementation milestone, was completed following explicit PI approval on 17 November 2026. Julia M0 content builders, strict committed Design/Experiment documents, canonical content digests, exact local references and native BioIR-to-FIR compilation with P03 identity are implemented; the human PI accepted the bounded issue #25 implementation at `da13860` on 17 November 2026 (see the [acceptance record](verification/ep03-julia-compiler.md#human-pi-implementation-acceptance--2026-11-17)). Native Julia SciML ODE execution is implemented under P04 with explicit Tsit5/Rodas5P methods; the human PI approved the bounded issue #26 implementation at `34a092e` on 17 November 2026 (see the [approval record](verification/ep03-julia-ode.md#human-pi-implementation-approval--2026-11-17)). Julia results/manifests, independent cross-language scientific conformance (#28/#29), and broader whole-project release authorization remain separate gates. P05 SSA, P06 package/version governance and #42 broader provenance retain separate gates. See the [current integration audit](verification/ep02-status-governance.md).

**Scientific source of truth:** ratified ADR/specification and independent reference evidence, not the current source code or test behavior. Human scientific approval is required for revisions.

**Ratified contract, 2026-11-14:** [ADR-P01 — M0-compatible BioIR subset](../spec/bioir/proposals/ADR-P01.md). The human PI approved reviewed revision `35805663e3912f8858bbfbe0c178cf009c5454e2` in this conversation, with the added [fixture-catalog gate](../conformance/README.md#parser-and-validator-fixture-catalog-gate) before parser/validator implementation approval. This does not close #12 or approve golden fixtures; independent native validation and fixture evidence remain outstanding.

**Accepted P01 reference expectations, 2026-11-15:** The human PI accepted the
[P01 catalog](../conformance/bioir/README.md) identified by reviewed SHA-256
`6576accde94a567cee90094f33913ffbddbfec30abfb1047521539a787ff9390`:
all 92 registered expectations, comprising 34 acceptances and 58 rejections,
including five canonical-serialization expectations, binary64 bit patterns and
declared diagnostic categories and paths. The catalog is now APPROVED.
**Not approved:** native FENIX implementations, exhaustive input validation,
compiler correctness, solver correctness or future BioIR semantics. See the
[explicit acceptance record](verification/ep01-p01-reference.md#human-pi-acceptance-recorded).

**Ratified contract, 2026-11-14:** [ADR-P02 — M0 mathematical FIR and capabilities](../spec/fir/proposals/ADR-P02.md).
The human PI approved reviewed revision `86450affca4470d7540d04f04bdc6d3d07e1a60d`
in this conversation with “i approve ADR-P02”. This ratifies the M0 FIR schema
and semantic/producer contract, including initial-count and observable source
correspondence. Independent fixture/rejection review, semantic validation and
implementation approval remain outstanding. P03 normalization, FIR bytes/hashes,
ODE numerical references and SSA eligibility are not approved by this decision.
See the [review evidence and ratification update](verification/ep01-p02-proposal.md).
This approval does not close issue #13 or the remaining EP-01 gates.

**Ratified contract, 2026-11-14:** [ADR-P03 — M0 FIR normalization and JCS identity](../spec/canonicalization/proposals/ADR-P03.md).
The human PI approved reviewed revision `fdee54e5ebc5226c0a83810872311cc8cbbec3fd`
in this conversation with “ok I accept ADR-P03 please recorrd it and push it to
the branch so I can merge it.” This ratifies the M0 FIR normalization, binary64
and Unicode policy, JCS bytes and version/domain identity wrapper contract.
[Candidate evidence](../conformance/canonicalization/README.md) checks expected
declaration ordering and serialization; native input-to-normalized transformation,
complete semantic validation, idempotence and end-to-end round trips are NOT RUN.
At contract ratification, reference-vector and implementation approval remained
pending; subsequent concrete-vector acceptance is recorded below. See the [ratification record](verification/ep01-p03-proposal.md#human-pi-ratification-recorded).
This approval does not close #14 or merge PR #53.


**Accepted scientific oracle:** The human PI accepted the concrete issue #15
[production–decay oracle](scientific-evidence/production-decay.md), its 40 reference
samples, independent evaluators and retained rational audit at reviewed revision
`1982357b3deed88e8e0cd8f745effd5c3bd960b3` on PR
[#54](https://github.com/DRAGGON-Lab/FENIX/pull/54). The catalog is now APPROVED.
See the [acceptance record](verification/ep01-production-decay-oracle.md#human-pi-acceptance-recorded)
for the explicit human instruction, reviewed artifact identity and verification.
This accepts the bounded mathematical reference under P02; it does not ratify
P04 solver thresholds, SSA eligibility or empirical predictive validity.


**Accepted canonicalization references, 2026-11-14:** The human PI accepted the
concrete issue #16 [canonicalization vectors and independent reference checks](../conformance/canonicalization/README.md)
at reviewed revision `a58ea8345f0e2f641ba152b065ee3fa6d9dc0625` on PR
[#55](https://github.com/DRAGGON-Lab/FENIX/pull/55). The catalog is now APPROVED.
The [acceptance record](verification/ep01-canonicalization-vectors.md#human-pi-acceptance-recorded)
retains the explicit approval, reviewed source/artifact identity and verification.
This accepts the bounded serialization byte/digest vectors and supplied expected
normalized-object identity references under unchanged ADR-P03. All 17
contract_only outcomes remain NOT_RUN; native FIR parsing, semantic validation,
normalization, idempotence and end-to-end round trips remain separate gates.


**Accepted rejection references, 2026-11-15:** The human PI accepted the concrete
issue #17 [BioIR/FIR rejection suite](../conformance/rejections/README.md) and its
independent Python/Julia evidence at reviewed revision
`b9bb961e7293c00c5728e8dd374fb4ef7a15b7ef` on
[PR #56](https://github.com/DRAGGON-Lab/FENIX/pull/56). The catalog is now APPROVED
for the 207 registered cases and fixed expectations. **Negative capability
fixtures are not exhaustive.** This acceptance does not establish complete
coverage of unsupported capabilities or malformed inputs, approve native package
APIs or change P01/P02/P03 scientific rules. See the
[acceptance record](verification/ep01-rejections.md#human-pi-acceptance-recorded)
for the explicit approval, reviewed artifact identity and refreshed evidence.


**Ratified contract, 2026-11-16:** [ADR-P04 — M0 ODE execution](../spec/execution/proposals/ADR-P04.md).
The human PI explicitly accepted reviewed revision `67820aec4f47b69434390b5b346726f00de608f6`
on PR #62, including strict negative sampled-count rejection even for mathematically
well-posed simulations, bounded numerical agreement instead of byte-identical
trajectories, and required native sampling/failure/identity tests. The historical
SciPy experiment and seven existing CI jobs do not establish native executor
correctness. Implementation review, #29 and #22/P07 retain separate gates. See the
[ratification record](../spec/execution/proposals/ADR-P04.md#human-pi-ratification-record).

**Ratified contract and accepted bounded expectations, 2026-11-16:**
[ADR-P07 — M0 source-linked ODE results and run manifests](../spec/results/proposals/ADR-P07.md).
The human PI explicitly accepted the revised proposal, schemas and bounded
candidate reference expectations at reviewed revision
`bc662d3e9778dc7977de39041f8a44cba314851e` on PR #64. Reviewed ADR SHA-256:
`cb45714cc685bdd182655d14794dfc9f5ba2dc1cc6ffde7c2ac022af018facef`;
reviewed RunManifest schema SHA-256:
`8e1c9236f33801ff81a12900d386c531295830ebca22ad2f09b9deb007d6264d`.
The human did not claim to have independently recomputed every raw-byte hash;
agent verification confirmed the reviewed identities. This accepts the revised
language-neutral core, Python/SciPy backend profile, producer identification and
bounded candidate expectations, without approving a native implementation,
exhaustive validation, Julia functionality, execution authenticity or biological
validity. #22 implementation review, #29 and #42 retain separate gates. See the
[explicit ratification evidence](verification/ep02-p07-ratification.md).

## Current integration addendum — 2026-11-16

The [PI-directed #22 closure](https://github.com/DRAGGON-Lab/FENIX/issues/22#issuecomment-6929801138) followed bounded implementation review while PR #65 was unmerged. PR #65 subsequently merged as `32acf4f4b51e257c7efed65203360e5e9ee83598`, with [seven successful post-merge jobs](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581). This updates implementation availability; it does not enlarge any historical ratification or supply independent scientific/release acceptance. P07 hashes and exact source links establish bounded consistency, not execution authenticity, authorship, biological validity or exact numerical replay.

## Approved live-status correction — 2026-11-17

The repository user explicitly approved the documentation correction at reviewed
revision `e9b227a5ed55559d5082ac114a84d4804f4c0ee7` on
[PR #67](https://github.com/DRAGGON-Lab/FENIX/pull/67), instructing in this conversation:

> I approve this, please record the desicion and update the PR

Decision: retain the corrected live status in README.md, ARCHITECTURE.md,
PRODUCT.md and this decision register. [EP-02 #4](https://github.com/DRAGGON-Lab/FENIX/issues/4)
records explicit PI acceptance on 17 November 2026 of the bounded native Python
M0 implementation milestone. Julia uncommitted M0 content is available; Julia
committed-document integrity, compilation and native numerical execution,
independent cross-language scientific conformance and broader whole-project
release authorization retain their separate gates.

This approval covers the documentation correction. It changes no scientific
contract, API, approved fixture or historical verification record, and does not
authorize a merge, issue closure or release. The source is the explicit user
instruction above; no independent GitHub review is inferred from this record.

## Accepted Julia committed-document implementation — 2026-11-17

The human PI explicitly accepted the bounded [issue #24](https://github.com/DRAGGON-Lab/FENIX/issues/24)
implementation at reviewed revision
[`bdedab963342c0e666bbe00b1e341e4c20ccb0a2`](https://github.com/DRAGGON-Lab/FENIX/commit/bdedab963342c0e666bbe00b1e341e4c20ccb0a2)
on [PR #68](https://github.com/DRAGGON-Lab/FENIX/pull/68), instructing in this conversation:

> I approve this, please record the desicion and update the PR

Decision: accept native Julia strict P01 parsing, direct JCS content digests,
immutable committed Design/Experiment documents, exact local verified Design
references, trusted expected-digest checks, predecessor-relative revision checks
and metadata amendments within the reviewed M0 scope. The accompanying
[implementation evidence](verification/ep03-julia-documents.md) records 660 native
assertions, all 92 original P01 cases, the overlapping 97-case P01 rejection
subset, 27 binary64 JCS vectors, standalone operation without Python and Python
regression/reference checks. Those executed results retain their original source
identity; this approval does not assert exhaustive validation.

This records explicit human implementation acceptance under unchanged ADR-P01;
it introduces no scientific rule, fixture or API change. Julia FIR compilation,
native numerical execution, independent cross-language scientific conformance,
stronger provenance, EP-03 acceptance and broader release authorization retain
separate gates. Merge and issue-state changes are separate actions. The approval
source is the PI instruction above, not an inferred GitHub review or CI result.
Historical verification receipts are unchanged.


## Accepted Julia FIR/compiler implementation — 2026-11-17

The human PI explicitly accepted the bounded [issue #25](https://github.com/DRAGGON-Lab/FENIX/issues/25)
implementation at reviewed revision
[`da13860b78e08928276009fb7e386e98ef271be0`](https://github.com/DRAGGON-Lab/FENIX/commit/da13860b78e08928276009fb7e386e98ef271be0)
on [PR #69](https://github.com/DRAGGON-Lab/FENIX/pull/69), instructing in this conversation:

> I approve this, record this desicion and push it to the PR

Decision: accept native Julia M0 BioIR-to-FIR compilation, immutable validated
FIR values, exact P02 template/unit/capability and source-correspondence checks,
P03 binary64 parsing, normalization and wrapped canonical identity within the
reviewed scope. The [implementation evidence](verification/ep03-julia-compiler.md)
records 207 rejection cases, 84 canonicalization cases, nine approved producer
controls, ten compiler/oracle input triples and 40 fixed samples at 512/1024 bits,
standalone operation without Python and regression/reference checks. Catalog
sets overlap. [Hosted CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/44098146298)
passed all seven jobs for the reviewed implementation. These are bounded
results, not exhaustive input validation or empirical biological validation.

This records human implementation acceptance under unchanged ADR-P01/P02/P03;
it changes no scientific contract, fixture, API or package version. Native
numerical execution, SSA, independent cross-language scientific acceptance,
stronger provenance, parent EP-03 acceptance and broader release authorization
retain separate gates. Merge and issue-state changes are separate actions.
The approval source is the explicit PI instruction above, not an inferred GitHub
review or CI result. Historical verification receipts retain their reviewed
source identities and original pending-acceptance observations.


## Approved Julia ODE implementation — 2026-11-17

The human PI approved the bounded [issue #26](https://github.com/DRAGGON-Lab/FENIX/issues/26)
implementation at reviewed revision
[`34a092ee1c559b8325cd45e2139789126c06bfb0`](https://github.com/DRAGGON-Lab/FENIX/commit/34a092ee1c559b8325cd45e2139789126c06bfb0)
on [PR #70](https://github.com/DRAGGON-Lab/FENIX/pull/70), instructing in this conversation:

> I approve this to be implemented

Decision: approve the completed native Julia M0 direct SciML ODE adapter,
immutable explicit execution settings/trajectories, requested-time sampling,
RHS budgets, capability checks and strict numerical failure handling within the
reviewed P02/P04 scope. The [implementation evidence](verification/ep03-julia-ode.md)
records 212 execution assertions, both Tsit5/Rodas5P methods on all 40 approved
samples at three predeclared settings (240 comparisons), stiff/failure controls,
standalone operation without Python and regression/reference checks.
[Hosted CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/44127661293) passed
all seven jobs for the reviewed revision, including the locked native numerical
matrix, environment-integrity check and uploaded report.

This approval applies to the bounded implementation already supplied on PR #70;
it does not claim independent human recomputation, exhaustive validation or
empirical biological validity. It changes no scientific contract, fixture,
mathematical semantics, package version or API. Portable results/manifests,
independent cross-language acceptance (#29), SSA, parent EP-03 acceptance and
broader release authorization retain separate gates. Merge and issue-state
changes are separate actions. The approval source is the explicit human
instruction above, not an inferred GitHub review submission or CI result.
Historical verification receipts retain their original source identities and
pending-acceptance observations.
