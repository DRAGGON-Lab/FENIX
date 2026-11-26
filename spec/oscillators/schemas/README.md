# Proposed P10 closed structural schemas

All four Draft-07 schemas are **PROPOSED**, under
[ADR-P10](../ADR-P10.md). They are standalone: every `$ref` is local, and `$id`
URNs identify documents without requiring network retrieval. They do not extend
an existing ratified schema in place.

| Schema | Bounded structure |
|---|---|
| [BioIR](bioir-oscillator.schema.json) | Separate Design/Experiment envelopes; exact finite source roles/units/bases; typed endpoint shapes and complete role cardinalities |
| [FIR](fir-oscillator.schema.json) | Both template/version branches; fixed state owners/scopes; exact flux/equation AST sets including zero rates and population-valued updates; complete symbol-map shape |
| [ODEResult](ode-result-oscillator.schema.json) | New result version, exact canonical state-ID order, per-state owner/scope/unit arrays, sample-major count matrices and direct-observable metadata shapes |
| [RunManifest](run-manifest-oscillator.schema.json) | New source/FIR/result version references and nonlinear Python/Julia backend profiles; profile-specific Jacobian/counter fields and existing P07 core shapes |

Every defined scientific object rejects unknown fields. Source metadata remains
an optional descriptive object under P01. Collection role coverage uses exact
cardinality plus `contains` requirements; exact reaction/equation enums require
complete unique template entries, preserving operand order. These structural
rules do not replace semantic reference resolution or raw parsing.

The result/manifest construction copies the ratified P07/P07-Julia shapes and
changes only the P10-proposed versions, multi-state metadata and nonlinear
backend derivative declarations. The original files remain untouched. Backend
environment/counters retain their distinct meanings; Julia `nw` is not SciPy
`nlu`. The old M0 profiles remain valid only in their old version-specific scope.

Run the [literal example audit and controls](../examples/README.md). Reproduction
uses `candidate_schemas.py --check`; writing requires a new output directory.
Shared construction code is not independent scientific evidence. Raw-token,
cross-artifact, mathematical-reference, canonical byte and PI acceptance gates
remain separate, as listed in the ADR and example instructions.
