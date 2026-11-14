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

One resolved state `x` represents nonnegative expected molecular count per
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
S_production,x = +1
S_decay,x      = -1
x'(t)          = alpha - beta * x(t),    x(0) = x0
```

`r` denotes deterministic molecular-count flux per representative cell per
second; `S` is dimensionless molecular stoichiometry. Molecular count is the
state quantity, not concentration. This describes the intended model and units;
[issue #15](https://github.com/DRAGGON-Lab/FENIX/issues/15) must independently
derive and evaluate its analytical reference, including `beta = 0` and limits.
This proposal contains no solver tolerance or numerical accuracy claim.

The M0 compiler will bind its only species to mathematical symbol `x`, and its
production/decay parameter roles to `alpha`/`beta`. These are FIR-local symbols,
not source Design identifiers. Source labels and revision digests are provenance.
References are explicitly typed as state or parameter; an unqualified string
must not be resolved by guessing between namespaces. Reaction identifiers are
`production` and `decay`. Direct observable IDs retain the scientific observable
IDs from the Experiment and therefore remain part of the mathematical interface.

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

Committed FIR mathematics is immutable. Different provenance records can describe
the same mathematical model identity. A requested execution profile or solver
change does not create a different FIR model; altered resolved mathematics does.
Integrity and author authentication remain distinct, as in P01.

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
the same mathematics. A semantic validator must reject disagreement rather than
choosing one as authoritative at runtime. Dimensional consistency requires each
flux/RHS to have unit `molecule/s`, using the declared parameter/state units.
Source function/port resolution must already satisfy P01; this FIR does not
carry unresolved source ports or repair an invalid Design/Experiment.

This is exact template recognition, not a promise of general algebraic equivalence.
Reassociated, commuted or differently encoded expressions are not silently
simplified; any additional accepted encoding requires an approved contract.
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
| Request different execution settings separately | Preserve eventual FIR model identity; check supported capabilities separately |
| [Unsupported SSA declaration](examples/invalid-ssa.json) | Reject this subset's capability declaration |
| [Broken RHS state reference](examples/invalid-reference.json) | Reject unresolved mathematical state reference; schema structure alone may pass |
| Wrong unit, unknown namespace or duplicate local IDs | Reject with field path; never convert or repair |
| Missing/repeated reaction role or conflicting equation | Reject semantic consistency |
| Negative/nonfinite parameter or initial value | Reject quantity; raw Unicode/number handling must follow a separately explicit applicable parser contract |
| Solver/profile/time grid inserted into `model` | Reject misplaced execution configuration |

Schema/semantic fixtures must be separately reviewed and executed by independent
Python and Julia validators after ratification. The larger normative rejection
catalog is #17 work. P03 must define the FIR raw-input/numeric contract explicitly;
this proposal does not inherit every P01 lexical restriction without that review.

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
