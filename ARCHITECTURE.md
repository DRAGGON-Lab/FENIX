# FENIX architecture — approved v0.1 design baseline

**Current implementation status:** Python implements the ratified M0 production–degradation path: typed content authoring, verified committed Design/Experiment documents, native FIR compilation and P03 identity, SciPy DOP853/Radau execution, and P07 source-linked results/manifests. All five EP-02 child implementation issues (#18–#22) are closed, and PR #65 merged at `32acf4f4b51e257c7efed65203360e5e9ee83598`; [post-merge CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581) passed seven jobs. [EP-02](https://github.com/DRAGGON-Lab/FENIX/issues/4), the bounded native Python M0 implementation milestone, was completed following explicit PI approval on 17 November 2026. Julia M0 content builders, strict committed Design/Experiment documents, canonical content digests, exact local references and native BioIR-to-FIR compilation with P03 identity are implemented; the human PI accepted the bounded issue #25 implementation at `da13860` on 17 November 2026 (see the [acceptance record](docs/verification/ep03-julia-compiler.md#human-pi-implementation-acceptance--2026-11-17)). Native numerical execution, independent cross-language scientific conformance (#28/#29), and broader whole-project release authorization remain separate gates. P06 version governance, stronger provenance/archive work (#42) and generated-input investigation (#59) retain separate scopes. Implementation completion and passing CI do not establish complete M0 or stable-core acceptance, biological validity or authenticated execution. Scientific authority remains the ratified language-neutral contracts and independent approved references, not either implementation. See the [integration/governance audit](docs/verification/ep02-status-governance.md).

## Target architecture: information and runtime boundaries

```text
Python BioIR Design + Experiment -> native Python compiler --+
                                                             +--> canonical FIR --> capability validation --> native solver
Julia BioIR Design + Experiment  -> native Julia compiler ----+                                         \--> results + run manifest
         ^                                       ^
         +---------- shared versioned specification and independent scientific conformance -----------+
```

- **BioIR Design:** reusable biological components, typed functions, identities, nested compartments and immutable committed revisions. Can represent biology beyond initially supported mathematical profiles.
- **BioIR Experiment:** immutable scenario referencing an exact design revision/digest. Includes parameters, initial conditions, media, interventions and semantic observables.
- **FIR:** immutable resolved mathematical model (states, rates, reactions, propensities where supported, equations, units, assumptions, interventions, observables, capabilities). ODE/SSA share one FIR model identity. Nonsemantic author metadata and execution settings are excluded.
- **ExecutionSpec:** solver, tolerances, time grid, randomness, replicates and limits; does not affect FIR identity.
- **RunManifest and typed results:** lightweight, versioned execution/provenance record for every run, plus optional archival bundles.
- **Optional post-core interfaces:** standards export, data binding/inference, biological/parameter optimization, sensitivity and spatial/hybrid/individual-cell profiles.

## Normative constraints

- Time seconds, volume litres, molecular count-space; intracellular deterministic counts are **per representative cell**, extracellular counts are **totals**. No implicit count/concentration/population conversion.
- FIR digest is SHA-256 over **FENIX-normalized RFC 8785/JCS** canonical semantic JSON, subject to ratified numeric/Unicode/order rules.
- Do not promise general algebraic equivalence of differently encoded expressions. Do not serialize executable Python/Julia callbacks.
- Explicitly reject unsupported biological capabilities; do not silently approximate.
- Python SciPy and direct Julia SciML ODE target M0. Restricted direct SSA follows deterministic parity and requires a separately approved eligibility profile; statistical, not bitwise, parity.
- Scientific verification: schemas/types, analytical/mathematical evidence, numerical tests, and empirical evidence when predictive biological claims are made.

## Boundaries

Two standalone packages in one monorepo. Python must not import Julia; Julia must not require Python. Mandatory standards dependencies, a GUI, database, hosted backend, Catalyst or Docker Compose are explicitly out of scope. Scaffolding package identifiers are provisional until package ADR-P06.

## Governance and current risks

**Historical contract and pre-implementation gates:** ADR-P01 is ratified for the M0-compatible BioIR subset, and the human PI accepted its [92 registered reference expectations](docs/verification/ep01-p01-reference.md#human-pi-acceptance-recorded). That bounded fixture decision does not approve native implementations, exhaustive input validation, compiler/solver correctness or future BioIR semantics. ADR-P02 FIR schema/capabilities and ADR-P03 canonicalization rules are ratified for M0; the bounded canonicalization reference vectors are accepted, while independent FIR semantic validation and native implementation approval remain outstanding. P04 ODE sampling/tolerances/failures are ratified for M0; native solver implementation review remains separate. P07 M0 source-linked results/manifests and bounded candidate expectations are ratified at reviewed revision `bc662d3`; [native implementation approval remains separate](docs/verification/ep02-p07-ratification.md). Later: P05 restricted SSA mathematics, P06 package/version compatibility and broader #42 provenance.

Only a human-approved ADR may change biological mathematics, contract meaning, units, capabilities, canonical hashes or golden references. Agents implement scoped, independently testable changes; passing smoke tests cannot be described as biological conformance. See [docs/approved-decisions.md](docs/approved-decisions.md).
