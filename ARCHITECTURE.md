# FENIX architecture — approved v0.1 design baseline

**Status:** Architectural intent approved; ADR-P01, ADR-P02 and ADR-P03 ratify the M0 BioIR, mathematical FIR/capability and canonicalization contracts. Scientific implementation and remaining fixture gates are pending; the bounded canonicalization references have [human PI acceptance](docs/verification/ep01-canonicalization-vectors.md#human-pi-acceptance-recorded). Neither Python, Julia nor historical LOICA 2 code is normative. Ratified mathematical specifications, ADRs and independently reviewed oracles control scientific behavior.

## Information and runtime boundaries

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

**Before compiler development:** ADR-P01 is ratified for the M0-compatible BioIR subset, with its fixture-catalog acceptance gate still outstanding. ADR-P02 FIR schema/capabilities and ADR-P03 canonicalization rules are ratified for M0; the bounded canonicalization reference vectors are accepted, while independent FIR semantic validation and native implementation approval remain outstanding. Later: P04 ODE tolerances, P05 restricted SSA mathematics, P06 package/version compatibility, P07 results/provenance.

Only a human-approved ADR may change biological mathematics, contract meaning, units, capabilities, canonical hashes or golden references. Agents implement scoped, independently testable changes; passing smoke tests cannot be described as biological conformance. See [docs/approved-decisions.md](docs/approved-decisions.md).
