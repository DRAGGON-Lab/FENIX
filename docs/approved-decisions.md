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

**Remaining engineering gates:** ADR-P01, ADR-P02 and ADR-P03 are ratified for the M0 BioIR, mathematical FIR and canonicalization contracts; independent fixture and implementation acceptance gates remain open. P04 ODE tolerance, P05 SSA math/stats, P06 package/version governance, P07 run provenance/results remain to be ratified for their release gates.

**Scientific source of truth:** ratified ADR/specification and independent reference evidence, not the current source code or test behavior. Human scientific approval is required for revisions.

**Ratified contract, 2026-11-14:** [ADR-P01 — M0-compatible BioIR subset](../spec/bioir/proposals/ADR-P01.md). The human PI approved reviewed revision `35805663e3912f8858bbfbe0c178cf009c5454e2` in this conversation, with the added [fixture-catalog gate](../conformance/README.md#parser-and-validator-fixture-catalog-gate) before parser/validator implementation approval. This does not close #12 or approve golden fixtures; independent native validation and fixture evidence remain outstanding.

**Implementation review candidate:** [P01 fixture catalog and independent runners](../conformance/bioir/README.md), with [executed evidence](verification/ep01-p01-reference.md).
Both native reports are available for review; fixture and implementation approval
remain human decisions before the issue #12 PR can merge. P03 and the wider
EP-01 fixture issues remain separate gates; P02 contract ratification does not
approve fixtures or implementations.

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
Independent reference-vector and implementation approval remain pending; the
catalog stays REVIEW_REQUIRED. See the [ratification record](verification/ep01-p03-proposal.md#human-pi-ratification-recorded).
This approval does not close #14 or merge PR #53.
