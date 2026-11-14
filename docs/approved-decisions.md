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

**Blocking engineering ADRs:** P01 BioIR schemas; P02 FIR/capabilities; P03 JCS normalization and edge vectors (all before compiler work). P04 ODE tolerance, P05 SSA math/stats, P06 package/version governance, P07 run provenance/results remain to be ratified for their release gates.

**Scientific source of truth:** ratified ADR/specification and independent reference evidence, not the current source code or test behavior. Human scientific approval is required for revisions.

**Proposal under review (not ratified):** [ADR-P01 — M0 BioIR Design and Experiment](../spec/bioir/proposals/ADR-P01.md).
