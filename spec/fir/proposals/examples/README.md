# ADR-P02 illustrative examples — PROPOSED

These are review illustrations, not approved golden fixtures or compiler output.
The [ADR](../ADR-P02.md) and [candidate schema](../fir-m0.schema.json) remain
PROPOSED. No FIR canonical bytes or hashes are provided before P03.

## Identity and source traceability

[production-decay.json](production-decay.json) retains the exact source digests
of P01's existing [Design](../../../bioir/proposals/examples/design.json) and
[Experiment](../../../bioir/proposals/examples/experiment.json), adding a map
from FIR `x` to source species `x`, species-scoped port `amount`, compartment
`cell`. Those P01 documents and fixtures are unchanged.

| FIR illustration | Exact P01-compatible source pair | Identity comparison |
|---|---|---|
| [GFP](production-decay-gfp.json) | [Design](sources/gfp-design.json), [Experiment](sources/gfp-experiment.json) | Complete `model` equals the base and LacI models |
| [LacI](production-decay-laci.json) | [Design](sources/laci-design.json), [Experiment](sources/laci-experiment.json) | Distinct BioIR identities and provenance; same M0 FIR identity |
| [Observable renamed](observable-renamed.json) | Standalone mathematical FIR; no claimed BioIR source | Only `amount_x` becomes `protein_amount`; different semantic identity |

The new source pairs are P02-local illustrations of P01's existing contract,
not additions to its approved fixtures. Their source content digests use P01's
direct RFC 8785/JCS rule, prepared with external Python `rfc8785` and SHA-256;
independent P01 validation checks them in Julia. These are BioIR source digests,
not FIR digest vectors. Species IDs are illustrative biological labels: shared
mathematics establishes neither biological equivalence nor interchangeability.

Each compiler-produced envelope must contain both source digests and complete
state and parameter maps. General standalone FIR can omit provenance, so a
structurally accepted partial envelope is not evidence of compiler completeness. There is no origin
flag. A supplied map structurally requires exactly one entry for `x`, all four
entry fields, and the qualifying `design_digest`.

A supplied map also requires two parameter entries covering `alpha` and `beta`
exactly once in either order. Each entry names the FIR parameter, BioIR parameter,
BioIR function ID and BioIR function kind. Source parameter names need not match
the fixed M0 symbols: [renamed parameters](production-decay-renamed-parameters.json)
has the same complete `model` as the base, using a new P02-local
[Design](sources/renamed-parameters-design.json) and
[Experiment](sources/renamed-parameters-experiment.json). Its `k_prod`/`k_loss`
parameters and `synthesis`/`degradation` functions map to `alpha`/`beta`.
All older source documents and their digests are preserved.

Observable IDs remain part of the semantic output interface. Optional labels
belong in `provenance.display_labels.observables`, keyed by those IDs. The
[label A](display-label-a.json) and [label B](display-label-b.json) envelopes
differ only in display text; their complete models and remaining provenance
are identical. Compare the observable-renaming example, whose model differs.
Labels may be Unicode strings, including empty strings; empty label collections
are allowed. Keys must resolve to declared observables in a separate provenance
check, and labels cannot supply scientific fields or appear inside `model`.

After ratification, separate provenance validation must verify both source
digests against the exact supplied P01 content and resolve the Experiment's
Design reference. It must resolve the mapped species, then its own port, then
its compartment, checking compartment equality and molecular-count port kind.
Unknown species/port/compartment or a map from another Design must be rejected
even if structurally valid. Relevant paths are
`/provenance/design_digest`, `/provenance/experiment_digest` and
`/provenance/symbol_map/states/0/{bioir_species_id,bioir_port_id,bioir_compartment_id}`.
The braces here abbreviate three paths, not a JSON Pointer syntax extension.
No provenance check may supply or repair mathematical fields.

Parameter provenance validation must resolve each parameter and function in the
exact Design, verify the function's parameter, kind and mapped species/port
target, and check `alpha`/production and `beta`/decay roles and units. The exact
Experiment's corresponding assignment must agree in value and unit with the
already resolved FIR parameter. These checks are specified, not implemented.

## Isolated negative examples

Every negative starts independently from `production-decay.json`. Mathematical
negatives preserve provenance; mapping negatives preserve the complete model.
Paths use zero-based JSON Pointer indices. These are proposed semantic rejection
reasons, not a frozen diagnostic API or precedence rule.

| Example | Only changed path(s) | Structural result | Required semantic rejection |
|---|---|---|---|
| [Unsupported SSA](invalid-ssa.json) | `/model/capabilities/ssa` | Reject | Unsupported M0 capability |
| [Broken RHS reference](invalid-reference.json) | `/model/equations/0/rhs/right/right/id` | Accept | State `missing` is unresolved; reaction flux still references `x` |
| [Reversed production sign](invalid-production-sign.json) | `/model/reactions/0/stoichiometry/x` | Accept | Production requires `+1`; unchanged equation disagrees with `S*r` |
| [Swapped rate references](invalid-rate-references.json) | `/model/reactions/0/flux/id`, `/model/reactions/1/flux/left/id` | Accept | Production uses `beta`, decay uses `alpha*x`; references resolve but roles and flux dimensions are wrong and disagree with the unchanged RHS |
| [Conflicting RHS](invalid-equation.json) | `/model/equations/0/rhs/left`, `/model/equations/0/rhs/right` (subtrees swapped) | Accept | `beta*x - alpha` has valid references and `molecule/s` units but disagrees with the unchanged reactions and required RHS |

Additional isolated cases:

| Example | Only changed path | Structural result | Required rejection |
|---|---|---|---|
| [Reversed decay sign](invalid-decay-sign.json) | `/model/reactions/1/stoichiometry/x` | Accept | Decay requires `-1`; unchanged equation disagrees with `S*r` |
| [Wrong production role](invalid-production-role.json) | `/model/reactions/0/flux` (subtree) | Accept | `beta*x` has valid references and flux units but violates the production role and disagrees with the equation |
| [RHS missing decay](invalid-equation-missing-decay.json) | `/model/equations/0/rhs` (subtree) | Accept | `alpha` has valid references and derivative units but omits decay from the unchanged reactions |
| [Missing mapped parameter](invalid-parameter-map-reference.json) | `/provenance/symbol_map/parameters/0/bioir_parameter_id` | Accept | Separate provenance rejection: source parameter `missing` does not exist |
| [Wrong mapped function](invalid-parameter-map-role.json) | `/provenance/symbol_map/parameters/0/bioir_function_id` | Accept | Separate provenance rejection: existing `decay` function has the wrong kind and parameter for `alpha` |

All six consistency negatives must pass structural validation and later fail
semantic validation. Template recognition, role/reference/unit checks and exact
stoichiometry establish M0 agreement; numerical sampling and general symbolic
algebra are not substitutes. No semantic validator is implemented here.

## Reproducible structural review

From the repository root, using the locked development environments:

```sh
uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py
julia --project=conformance/julia spec/fir/proposals/review_examples.jl
```

These independent structural review scripts check all FIR examples, P01 source
schema structure, complete-model equality, observable-only inequality, isolated
mutations, mapping cardinality, required fields and standalone permissiveness.
They do not resolve FIR source maps or validate FIR mathematics. See the
[review evidence](../../../../docs/verification/ep01-p02-proposal.md) for executed
commands, source fingerprint, separate P01 checks and remaining gates.
