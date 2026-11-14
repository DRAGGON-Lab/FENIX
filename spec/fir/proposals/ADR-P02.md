# ADR-P02 — M0 mathematical FIR and capability contract

**Status: PROPOSED — human PI ratification pending. Not a normative contract.**

Issue: [#13](https://github.com/DRAGGON-Lab/FENIX/issues/13); dependency:
[#12](https://github.com/DRAGGON-Lab/FENIX/issues/12) and ratified
[ADR-P01](../../bioir/proposals/ADR-P01.md). Approved architectural authority:
D02–D04, D06–D09, D14–D15 and D26–D29 in the
[decision index](../../../docs/approved-decisions.md).
This proposal prepares the next review while P01's reference implementation and
fixture acceptance are reviewed separately. It does not bypass those gates.

## Decision requested

Ratify the [candidate FIR schema](fir-m0.schema.json), version `0.1.0`, and the
semantic checks below for the M0 production/degradation subset. FIR's broader
architecture remains extensible; nested/community mathematics, event handling
and SSA eligibility are not defined by this first subset.

No compiler, mathematical interpreter, solver, propensity implementation or
normative byte/digest fixture is authorized by this proposal. Those require the
applicable ratified contracts, independent evidence and implementation review.
ADR-P03 will define FIR normalization, canonical bytes, digest scope encoding
and edge vectors. P01's BioIR hashing rule does not silently define FIR hashing.

## Scientific model and namespaces

M0 `x` is an abstract mathematical state, not a biological species identity.
This one resolved state represents nonnegative expected molecular count per
representative cell. Time is seconds. Its initial value `x0` is finite and
nonnegative; fractional expected counts are permitted for deterministic execution.
The resolved production parameter `alpha` is finite/nonnegative in `molecule/s`;
the resolved first-order loss parameter `beta` is finite/nonnegative in `1/s`.
No concentration, population multiplier or implicit unit conversion is involved.
Resolved numeric constants denote their finite binary64 values. Independent
high-precision references must use those represented parameter values rather
than silently substituting different decimal-real constants. P03 must separately
settle the admissibility of raw numeric tokens and canonical serialization.

The proposed governing mathematics is:

```text
r_production(x) = alpha
r_decay(x)      = beta * x
S_x,production = +1
S_x,decay      = -1
x'(t)          = alpha - beta * x(t),    x(0) = x0
```

The reaction–equation invariant is
\(\dot{\mathbf{x}}=S\mathbf{r}(\mathbf{x},\boldsymbol{\theta})\).
Here `x` in bold is the state vector, `theta` is the resolved parameter vector,
`r` is the vector of deterministic molecular-count fluxes per representative
cell per second, and `S` is the dimensionless stoichiometry matrix. Rows of `S`
are paired with explicit state IDs and columns with explicit reaction IDs;
array position alone must not establish that pairing. For this M0 model, the
state row is `[x]`, the reaction columns are `[production, decay]`, the parameter
vector is `[alpha, beta]`, `S = [+1, -1]`, and `r = [alpha, beta*x]`.
These are explanatory orderings, not P03 canonical array-order rules.
Molecular count is the state quantity, not concentration. This describes the intended model and units;
[issue #15](https://github.com/DRAGGON-Lab/FENIX/issues/15) must independently
derive and evaluate its analytical reference, including `beta = 0` and limits.
This proposal contains no solver tolerance or numerical accuracy claim.

The M0 compiler will bind its only species to mathematical symbol `x`, and its
production/decay parameter roles to `alpha`/`beta`. These are FIR-local symbols,
not source Design identifiers. This deliberately abstracts biological species
identity into a generic mathematical symbol for M0. Source species identities,
labels and revision digests belong to provenance.
References are explicitly typed as state or parameter; an unqualified string
must not be resolved by guessing between namespaces. Reaction identifiers are
`production` and `decay`. Direct observable IDs retain the scientific observable
IDs from the Experiment and therefore remain part of the semantic output interface.

## Payload and identity boundaries

The envelope contains `model` and optional `provenance`. Every field under
`model` is semantic. Every field under `provenance` is nonsemantic. No field can
supply missing mathematics through provenance, author metadata or runtime state.

| Field | Classification and meaning |
|---|---|
| `model.schema_version` | Semantic FIR contract version, independent of package versions |
| `model.time_unit` | Semantic, exactly `s` |
| `model.states[]` | Semantic local state ID, quantity, scope, unit and initial value |
| `model.parameters[]` | Semantic local parameter ID, resolved value and explicit unit |
| `model.reactions[]` | Semantic reaction ID, signed stoichiometry and deterministic flux AST |
| `model.equations[]` | Semantic state reference, derivative unit and RHS AST |
| `model.observables[]` | Semantic unique observable ID, referenced state and output unit |
| `model.assumptions[]` | Semantic scope assumptions stated explicitly below |
| `model.capabilities` | Semantic mathematical capability declarations, not installed backend availability |
| `provenance.design_digest` | Nonsemantic exact source Design content reference |
| `provenance.experiment_digest` | Nonsemantic exact source Experiment content reference |
| `provenance.compiler` | Nonsemantic compiler name/version record |
| `provenance.symbol_map.states[]` | Nonsemantic mapping from FIR state to Design-qualified species, port and compartment |
| `provenance.symbol_map.parameters[]` | Nonsemantic mapping from FIR parameters to Design-qualified parameters and function roles |
| `provenance.display_labels.observables` | Nonsemantic display text keyed by semantic observable ID |

States have `quantity: molecular_count`, `scope: representative_cell`,
`unit: molecule`. The initial value is mathematical experiment data, not solver
configuration. In this subset, fixed cell volume has no factor in the resolved
count equations; its source Design record remains traceable through provenance.
A future model in which volume changes mathematics must represent that effect
explicitly in the semantic payload under an approved contract.

Assumptions are exactly `single_representative_cell`, `well_mixed`, `fixed_volume`,
`constant_rates`, and `no_interventions`. They describe this subset, not all FIR.
Their order and other array normalization rules remain an explicit P03 decision;
validators must not sort or rewrite scientific input to make it acceptable.

The FIR model digest will cover only normalized canonical `model`, never the
provenance envelope or an ExecutionSpec. P03 must ratify the exact normalization,
version/domain encoding and bytes before any implementation emits normative FIR
digests. Examples intentionally contain no claimed FIR digest. Do not substitute
a BioIR digest, Python serializer output or another compiler's output as an oracle.

FIR identity is resolved mathematics **plus its named observable interface**.
Equal kinetics alone are insufficient: initial quantities, units, scope,
assumptions, capabilities, observables and all other semantic fields must also
agree. In particular, renaming only observable `amount_x` to `protein_amount`
changes semantic model identity even if its state, units and kinetics are equal.
P03 normalization and hashing must preserve this distinction.

Optional display labels are presentation text, separate from the semantic output
interface. `provenance.display_labels.observables` maps observable IDs to strings
(including Unicode text); every key must refer to a declared observable. Changing
or removing labels never changes FIR identity. Labels cannot replace IDs, resolve
mathematical references or appear under `model`. Label-reference resolution is a
separate provenance check; the schema checks only key/value structure. Empty
label collections and empty strings are permitted. This subset defines labels
for observables only, not a general annotation system.

GFP and LacI Designs may share M0 FIR identity when their complete semantic
payloads match. Their BioIR identities and provenance remain distinct. Shared
FIR identity establishes neither biological equivalence nor interchangeability.
This M0 binding establishes no general variable-renaming or network-isomorphism
rules for future models.

Committed FIR mathematics and its named interface are immutable. Different
provenance records can describe the same model identity. A requested execution
profile or solver change does not create a different FIR model; altered semantic
payload does. Integrity and author authentication remain distinct, as in P01.

## Source mapping and producer contract

Standalone mathematical FIR may omit `provenance`. A BioIR compiler-produced
envelope must include `provenance.design_digest`, `provenance.experiment_digest`
and a complete `provenance.symbol_map` with both `states` and `parameters`.
This is a producer obligation checked against the supplied source documents,
not a self-declared origin flag. The general
schema intentionally accepts standalone envelopes without those fields; schema
acceptance alone does not establish compiler-output completeness.

Each state-map entry contains `fir_state_id`, `bioir_species_id`, `bioir_port_id`
and `bioir_compartment_id`. A supplied M0 map must cover `x` exactly once, with no
extra state entries. The map is qualified by `provenance.design_digest`, which
is required whenever a map is supplied. Validate both digests against the exact
supplied Design and Experiment content under P01, including the Experiment's
exact Design reference; resolve
the species in that Design, the port within that species (not globally), and
the compartment in that Design. Require the species' compartment to match the
mapped compartment and the port to be its P01 molecular-count port. Reject
unresolved or inconsistent mappings; do not search other revisions or Designs.

Each parameter-map entry requires `fir_parameter_id`, `bioir_parameter_id`,
`bioir_function_id` and `bioir_function_kind`. A supplied map must contain both
complete sections: exactly one state entry for `x` and exactly one parameter
entry each for `alpha` and `beta`, in either order. These are fixed M0 symbols;
the word canonical does not establish P03 normalization or general renaming.
All source IDs are qualified by the exact Design digest, not guessed from their
spelling. The parameter and function must exist in their Design namespaces;
the function's parameter must match `bioir_parameter_id`, its kind must match
`bioir_function_kind`, and its target must match the mapped species and port.
`alpha` must bind to `constitutive_production` with unit `molecule/s`, and `beta`
to `first_order_decay` with unit `1/s`. Check the exact Experiment's assignment
for each mapped source parameter, including its unit and resolved value, against
the corresponding FIR parameter. Reject unresolved or wrong-role bindings,
including bindings to an existing but inappropriate function. The source values
must not substitute for absent resolved FIR values.

For compiler-produced FIR, check every state's `initial` value and `unit`
against the initial-count assignment for its mapped BioIR species in the exact
Experiment qualified by `provenance.experiment_digest`. Require one matching
assignment, equal represented numeric values and identical unit tokens (M0:
`molecule`); reject missing assignments or value/unit mismatches. Do not apply a
tolerance, convert units, use a default initial value or repair either document.
For example, source initial count 5 and FIR initial value 0 must be rejected.

Compiler-produced FIR must also have an exhaustive one-to-one correspondence
between the exact Experiment's observables and `model.observables`. Match by
unique observable ID, not array position or display label: no invented, omitted,
renamed or duplicate observable is permitted. Resolve each source observable's
species and species-scoped port through the validated state map; its FIR state
must equal that mapped state. Require its FIR output unit to equal the mapped
state unit and the source port's quantity unit (P01 molecular-count ports use
`molecule`; the Experiment does not serialize a separate observable unit).
Reject wrong targets or units. If the Experiment declares no observables, the
FIR collection must be empty; do not synthesize a default observable. These
correspondence checks establish source agreement, not P03 array normalization.
The standalone observable-renaming illustration has no compiler-source claim
and remains valid as a distinct mathematical output interface.

These are separate provenance checks and cannot supply missing mathematics or
repair invalid `model` fields. All mapping fields, including their qualifying
Design digest, are excluded from mathematical identity. Future hierarchical or
additional-symbol mappings require versioned contract extensions; this map does
not define mappings for arbitrary networks, additional symbols or reactions.

## Portable expressions and consistency checks

The candidate schema represents only typed `parameter`/`state` references,
binary `multiply`, and binary `subtract` nodes. No string expressions, callbacks,
code loading, `eval`, user functions or implicit coercions are permitted.
Parameters and states resolve only within their declared FIR namespaces.

The subset requires production flux to reference `alpha`; decay flux to be
`multiply(parameter(beta), state(x))`; and the derivative to be
`subtract(parameter(alpha), multiply(parameter(beta), state(x)))`.
Exactly one reaction of each required role and exactly one equation for `x`
must exist. Stoichiometry is respectively `+1` and `-1` for `x`.

Reactions and equations deliberately provide two inspectable representations of
the same mathematics and must satisfy the invariant above. Validate typed
references, exact role coverage, stoichiometric signs, flux templates and the
RHS template together. A semantic validator must reject disagreement; neither
representation may silently override or repair the other. Dimensional consistency
requires each flux/RHS to have unit `molecule/s`, using the declared parameter
and state units.
Source function/port resolution must already satisfy P01; this FIR does not
carry unresolved mathematical inputs or repair an invalid Design/Experiment.
Source port IDs in provenance are traceability references, not mathematical inputs.

This is exact template recognition, not a promise of general algebraic equivalence.
Reassociated, commuted or differently encoded expressions are not silently
simplified; any additional accepted encoding requires an approved contract.
No numerical spot checks or general symbolic algebra may substitute for these
exact M0 checks. Future multi-species contracts must specify derivative
construction from reactions, state/reaction ordering, permitted comparison rules
and negative fixtures before implementation.
The schema checks node structure only. It does not prove expression references,
units, exact role coverage or reaction/equation agreement.

## Capability and execution separation

The candidate M0 declaration is `capabilities: {"ode": true, "ssa": false}`.
`ode: true` means the mathematics satisfies this deterministic contract; it does
not assert that a solver is installed or that all trajectories can be computed
without numerical overflow. Numerical failure reporting and tolerances belong
to the ODE execution contract/ADR-P04, not FIR identity.

`ssa: false` means no SSA eligibility is ratified for this subset. It does not
claim that birth/death mathematics can never admit a discrete model. The flux
expressions above are not automatically approved stochastic propensities.
No SSA simulator may infer a supported profile from ODE validity alone.

An ExecutionSpec separately requests a profile and settings; capability validation
must explicitly reject an unsupported request. It must not mutate the FIR or its
capabilities to accommodate a requested backend. BioIR Experiment identity also
remains unchanged when only the execution request changes.

D27's shared ODE/SSA identity applies to the same fully specified mathematical
FIR with both profiles supported under their ratified contracts. A later P05
must establish propensity mathematics, initial-count admissibility and eligibility
before a schema/profile may declare SSA support. A future semantic version adding
that meaning must specify compatibility/migration, not retroactively alter old
M0 FIR payloads or digests. This proposal does not settle that later version.

## Examples, invalid cases and acceptance

The [production/degradation example](examples/production-decay.json) is a
proposal illustration with `alpha=10`, `beta=0.1` and `x0=0`. It is not an
approved golden fixture or numerical solution. The candidate schema and examples
are marked proposed until human scientific review and ratification.

| Review case | Expected result if this proposal is ratified |
|---|---|
| Resolved production/degradation example | Accept M0 mathematical structure and exact semantic template |
| Zero production, zero decay, fractional nonnegative initial value | Accept deterministic mathematics; no implied SSA support |
| Change compiler/source digests in provenance only | Preserve eventual FIR model identity under P03 |
| [GFP and LacI source pair](examples/README.md) with identical complete `model` objects | Preserve M0 FIR identity; keep distinct BioIR identities and provenance |
| [Rename only the observable](examples/observable-renamed.json) | Different semantic identity; P03 must preserve the named interface |
| Request different execution settings separately | Preserve eventual FIR model identity; check supported capabilities separately |
| [Unsupported SSA declaration](examples/invalid-ssa.json) | Reject this subset's capability declaration |
| [Broken RHS state reference](examples/invalid-reference.json) | Reject unresolved mathematical state reference; schema structure alone may pass |
| [Reversed production sign](examples/invalid-production-sign.json) | Structurally accept; semantically reject stoichiometry/equation disagreement |
| [Swapped rate references](examples/invalid-rate-references.json) | Structurally accept; semantically reject role/unit/consistency failure |
| [Conflicting RHS](examples/invalid-equation.json) | Structurally accept; semantically reject equation disagreement despite valid references and units |
| [Reversed decay sign](examples/invalid-decay-sign.json) | Structurally accept; semantically reject decay stoichiometry/equation disagreement |
| [Wrong production role](examples/invalid-production-role.json) | Structurally accept; semantically reject `beta*x` production despite valid references and flux units |
| [RHS omits decay](examples/invalid-equation-missing-decay.json) | Structurally accept; semantically reject `alpha` RHS despite valid references and units |
| [Unresolved parameter map](examples/invalid-parameter-map-reference.json) or [wrong mapped function](examples/invalid-parameter-map-role.json) | Structurally accept; reject separate provenance validation; mathematics is unchanged |
| [Display label A](examples/display-label-a.json) versus [B](examples/display-label-b.json) | Preserve complete semantic payload and eventual identity |
| [Source initial count 5, FIR 0](examples/invalid-initial-count.json) | Structurally accept; reject compiler/source initial-count mismatch |
| [Invented](examples/invalid-observable-invented.json), [missing](examples/invalid-observable-missing.json), [renamed](examples/invalid-observable-renamed.json) or [wrong-target observable](examples/invalid-observable-target.json) | Structurally accept; reject compiler/source observable correspondence |
| Wrong unit, unknown namespace or duplicate local IDs | Reject with field path; never convert or repair |
| Missing/repeated reaction role or conflicting equation | Reject semantic consistency |
| Negative/nonfinite parameter or initial value | Reject quantity; raw Unicode/number handling must follow a separately explicit applicable parser contract |
| Solver/profile/time grid inserted into `model` | Reject misplaced execution configuration |

Schema/semantic fixtures must be separately reviewed and executed by independent
Python and Julia validators after ratification. The larger normative rejection
catalog is #17 work. P03 must define the FIR raw-input/numeric contract explicitly;
this proposal does not inherit every P01 lexical restriction without that review.
The [example review notes](examples/README.md) identify each isolated defect's
paths and the separate structural, producer and source-resolution checks.

## Alternatives and review tradeoffs

- **Explicit reaction plus equation representation (proposed):** easy scientific
  walkthrough and future profile extension; requires consistency validation of
  deliberately redundant mathematics.
- **Equation-only payload:** smaller deterministic implementation, but reaction
  structure needed for later supported stochastic profiles is not explicit.
- **Backend-native representations:** convenient solver integration, but violates
  independent language-neutral FIR and risks leaking execution settings into identity.

The first contract remains a narrow FIR subset, with versioned extension rather
than pretending unsupported community/hierarchical mathematics is already defined.
Public native APIs and solver choices are not frozen by this schema proposal.

## Human ratification record

- Decision: **PENDING**
- Ratifying human PI, reviewed revision, date and approval source: **not recorded**
- Independent fixture/rejection review: **PENDING**

Review must explicitly cover namespaces and role binding, expression semantics,
count/unit interpretation, redundant representation consistency, assumptions,
semantic/provenance classification and capability scope. Do not mark #13 complete
or implement these new mathematical contracts before the required approval.
