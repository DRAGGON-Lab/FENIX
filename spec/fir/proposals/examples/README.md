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

Each compiler-produced envelope must contain both source digests and the state
map. General standalone FIR can omit provenance, so a structurally accepted
partial envelope is not evidence of compiler completeness. There is no origin
flag. A supplied map structurally requires exactly one entry for `x`, all four
entry fields, and the qualifying `design_digest`.

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

## Isolated negative examples

Every negative starts independently from `production-decay.json`; provenance
is identical. Paths use zero-based JSON Pointer indices. These are proposed
semantic rejection reasons, not a frozen diagnostic API or precedence rule.

| Example | Only changed path(s) | Structural result | Required semantic rejection |
|---|---|---|---|
| [Unsupported SSA](invalid-ssa.json) | `/model/capabilities/ssa` | Reject | Unsupported M0 capability |
| [Broken RHS reference](invalid-reference.json) | `/model/equations/0/rhs/right/right/id` | Accept | State `missing` is unresolved; reaction flux still references `x` |
| [Reversed production sign](invalid-production-sign.json) | `/model/reactions/0/stoichiometry/x` | Accept | Production requires `+1`; unchanged equation disagrees with `S*r` |
| [Swapped rate references](invalid-rate-references.json) | `/model/reactions/0/flux/id`, `/model/reactions/1/flux/left/id` | Accept | Production uses `beta`, decay uses `alpha*x`; references resolve but roles and flux dimensions are wrong and disagree with the unchanged RHS |
| [Conflicting RHS](invalid-equation.json) | `/model/equations/0/rhs/left`, `/model/equations/0/rhs/right` (subtrees swapped) | Accept | `beta*x - alpha` has valid references and `molecule/s` units but disagrees with the unchanged reactions and required RHS |

The three consistency negatives must pass structural validation and later fail
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
