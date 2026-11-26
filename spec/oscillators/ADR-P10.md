# ADR-P10 — Proposed oscillator wire contracts and identity

**Status: PROPOSED design for human review; not a ratified wire format.**

Refs [#84](https://github.com/DRAGGON-Lab/FENIX/issues/84). The equations,
quantity bases and numerical-domain policy come from
[ADR-P09](ADR-P09.md), ratified at `e84ff5b`. The PI subsequently accepted the
11 analytical component cases/33 samples at `6ab3dd4`, recorded in
[PR #89](https://github.com/DRAGGON-Lab/FENIX/pull/89).
The PI separately accepted the bounded
[nonlinear numerical reference definitions](../../conformance/oscillators/nonlinear/README.md)
at `0ee6b42`, recorded in [PR #92](https://github.com/DRAGGON-Lab/FENIX/pull/92).
That decision does not ratify the P10 wire design or choose native tolerances.

This ADR proposes the serialization and binding choices missing between that
mathematics and native authoring/compilation/capture/readback. It changes no
native package, accepted fixture, existing schema, version constant or digest.
It deliberately exposes version, binding, normalization and profile choices for
PI review before implementation. The accompanying
[closed structural schemas](schemas/README.md) and
[twelve literal source/FIR/zero-grid artifacts](examples/README.md) are proposed
candidates. Complete raw/binding/identity/rejection catalogs, independent
mathematical/byte evidence and explicit PI ratification remain required; passing
the bounded example audit does not satisfy those gates.

## Scope, alternatives and compatibility

The two templates are one six-state intracellular three-gate ring and one
18-state ring with exactly one transcript/synthase gate per strain. No growth,
events, SSA, spatial effects, density-valued source states, arbitrary circuits,
executable expressions, registry publication or package-version policy is added.
All serialized amounts remain molecular counts under P09.

Proposed discriminators:

| Artifact | Proposed version or identifier |
|---|---|
| BioIR Design/Experiment | `schema_version: "0.3.0"` |
| FIR mathematical model | `schema_version: "0.3.0"` |
| FIR canonicalization | `canonicalization_version: "0.2.0"` |
| Single-cell scientific template | `repressilator.single_cell.v1` |
| Three-strain scientific template | `repressilator.three_strain.v1` |
| ODEResult/RunManifest | `schema_version: "0.2.0"` |
| Python execution backend | `python-scipy-oscillator-ode/0.1.0` |
| Julia execution backend | `julia-sciml-oscillator-ode/0.1.0` |

These numbers are proposals for bounded wire contracts, not published package
versions or a resolution of P06 governance. Version 0.3.0 avoids claiming that
P08's proposed community 0.2.0 format already covers oscillators. A new
canonicalization version explicitly scopes the extension beyond P03's M0-only
approval, although its six collection-ordering rules are reused. The PI may
choose different numbers before schema/vector freeze; changing them then changes
candidate identities and requires renewed review.

Alternatives: extending M0 in place would reinterpret immutable versioned
contracts; using P08's sender/receiver template would misrepresent the requested
three-gate topology. A completely general circuit schema adds unsupported
binding/execution choices. The proposed finite templates keep the next native
scope explicit while leaving wider BioIR representation for later contracts.

Old readers reject these new versions and backend profiles. New readers retain
the exact old version-specific rules. There is no implicit migration, repair,
profile fallback or reinterpretation of an old source/FIR/result. Original M0
source/model identities, package installations and every M0/M1 scientific gate
remain unchanged. Migrated content, if separately specified later, is a new
revision and cannot silently retarget an Experiment.

## Source documents and raw input

Keep separate immutable Design and Experiment envelopes with exactly `content`,
`digest` and optional `metadata`. Apply P01's raw JSON, source-number, Unicode,
identifier, content-JCS, exact Design-reference and explicit predecessor rules.
In particular, BioIR arrays remain identity-significant, metadata cannot supply
science, integer tokens retain the source safe-integer restriction, and neither
digest self-consistency nor a matching local pair authenticates origin.

New population assignments are proposed to require integer-form JSON tokens,
from 1 through 9007199254740991, excluding booleans and fraction/exponent forms.
This lexical restriction is an explicit new wire choice, not inferred from
P09's integer-valued populations. The PI must review it with the raw-input
fixtures. Gate Hill exponents retain integer-valued 1..4 semantics; their source
quantity fields otherwise follow P01 numeric decoding. Initial counts/rates are
finite nonnegative binary64, volumes/K strictly positive. No implicit unit,
population, count/density or scope conversions are accepted.

### Exact Design field set

`content` has exactly `kind`, `schema_version`, `id`, `revision`, `template`,
`owners`, `parameters`, `gates`, `signal_synthesis`, `signal_losses`, `transport`.
`kind` is `Design`. Every collection is required; single-cell signal-specific
collections are empty. `template` identifies scientific structure, not a solver
or execution request. No new general-purpose callback or expression language is
introduced in BioIR.

Owners contain exactly `id`, `role`, `volume`, `species`; volume is
`{"value": number, "unit": "L"}`. Owner IDs are unique. Single-cell owner role
is `cell`; community roles are `strain1`, `strain2`, `strain3`, `medium`, each
occurring exactly once. Arbitrary source IDs follow P01 and never resolve by
display name or declaration position.

Species contain exactly `id`, `role`, `ports`. Species IDs are unique within
their owner; their roles are the canonical mathematical state roles below and
occur once in the whole Design. A port has exactly `id`, `kind`; IDs are unique
within their species. Every species has one `molecular_count` amount port.
Single-cell proteins also have one `density_out` port. Community intracellular
signals each have one `density_out`, one `transport_out` and one `transport_in`;
medium signals have `transport_out` and `transport_in` but no density sensor
port in this template. Other ports are rejected. A density port supplies a
read-only derived density of that same intracellular pool; it adds no state,
stoichiometric sink or binding dynamics.

An endpoint is exactly `{"owner": source_owner_id, "species": source_species_id,
"port": source_port_id}`. Resolve the full tuple in that namespace; repeated
species/port IDs under different owners are valid. Reject aliases, unresolved
tuples, wrong port kinds and owner/role disagreement.

| State role | Single-cell owner | Community owner | Quantity basis |
|---|---|---|---|
| `m1`, `m2`, `m3` | `cell` | corresponding `strain1..3` | expected count/cell |
| `p1`, `p2`, `p3` | `cell` | corresponding `strain1..3` | expected count/cell |
| `a11`..`a33` | absent | first index selects strain | expected count/cell |
| `e1`, `e2`, `e3` | absent | `medium` | total count |

Exactly six or eighteen species are required. In the single cell p_i is a
repressor; in the community it is that strain's signal synthase. Each source
species role maps to exactly one mathematical state and its declared owner.

### Parameters and typed functions

Each parameter declaration contains exactly `id`, `role`, `unit`, `basis`.
IDs and canonical roles are individually unique, with exactly 21 single-cell or
54 community parameters. No unused or extra declarations are accepted.

| Canonical role, i/j/k in 1..3 | Unit | Exact proposed basis token |
|---|---|---|
| `b_i`, `h_i` | `molecule/s` | `per_representative_cell` |
| `gm_i`, `gp_i`, `ga_jk`, `ge_k`, `out_jk`, `in_jk` | `1/s` | `first_order` |
| `beta_i` | `1/s` | `protein_per_transcript` |
| `sigma_i` | `1/s` | `signal_per_synthase` |
| `K_i` | `molecule/L` | `density` |
| `n_i` | `1` | `dimensionless` |

Subscripts denote literal concatenation, without underscores: e.g. `b1`, `gm2`,
`ga23`, `out31`, `K1`. Roles `sigma`, `ga`, `ge`, `out`, `in` are community-only.
Explicit basis tokens preserve catalytic meanings despite identical `1/s` units.
The tokens and cardinalities are proposed wire choices, requiring fixture review.

Each of three gates has exactly `id`, `role`, `transcript`, `protein`, `sensor`,
`parameters`. Gate IDs are unique; roles are exactly `g1`, `g2`, `g3` once each.
Transcript/protein endpoints use their amount ports, map to m_i/p_i and share
the prescribed owner. The sensor is a density endpoint: p_prev(i) in the single
cell; a_i,prev(i) in the community, with prev(1)=3, prev(2)=1, prev(3)=2. Sensing
the medium, a different strain, the successor or the synthase is rejected.

Gate `parameters` has exactly `basal`, `induced`, `mrna_decay`, `translation`,
`protein_decay`, `threshold`, `hill_n`, each a source parameter ID matching the
corresponding canonical role and exact unit/basis. A gate denotes repressed
transcription, transcript degradation, catalytic translation and protein
degradation with exactly the P09 equations. It is not a complete oscillator in
one community strain.

Community `signal_synthesis` has three entries, each exactly `id`, `catalyst`,
`target`, `rate`: p_k amount catalyzes a_kk production using sigma_k. Community
`signal_losses` has twelve entries, each exactly `id`, `target`, `rate`: all nine
a_jk and three e_k amount pools use ga_jk/ge_k. IDs in each function collection
are unique. These operations consume neither catalyst nor transcript.

Community `transport` has exactly eighteen directed entries, each exactly `id`,
`source`, `target`, `rate`. For every j,k, export connects a_jk's transport_out to
e_k's transport_in with out_jk; import connects e_k's transport_out to a_jk's
transport_in with in_jk. Rates are per-cell first-order constants. Signal k must
remain signal k across the membrane. Duplicate edges, reversed kinds, missing
directions, cross-strain shortcuts and signal substitutions are rejected. Each
parameter/function must participate in exactly its assigned template role.

### Exact Experiment field set

`content` has exactly `kind`, `schema_version`, `id`, `revision`, `design`,
`populations`, `parameters`, `initial_counts`, `observables`, `interventions`.
`kind` is `Experiment`; `design` is the exact P01 ID/revision/digest reference
to a supplied local 0.3.0 Design. `interventions` is required and empty.

`populations` is an empty array for the single cell, or exactly three
`{"owner": source_owner_id, "value": integer}` assignments for the strain
owners. No medium population or implicit single-cell population is introduced.
`parameters` has one `{"parameter": source_parameter_id, "value": number,
"unit": unit}` assignment for each declared parameter. `initial_counts` has
one `{"target": amount_endpoint, "value": number, "unit": "molecule"}` per
declared species. Require uniqueness/exhaustive coverage and exact units.

Observables are zero or more `{"id": observable_id, "target": amount_endpoint}`
with unique P01 IDs. Multiple observable IDs may target the same state. They are
direct molecular-count observations, with owner/basis derived from the exact
target; concentration observations remain unsupported. Solver, tolerance, grid,
randomness and display metadata do not belong in scientific Experiment content.

## Resolved FIR and exact producer correspondence

The proposed FIR envelope has exactly `canonicalization_version`, `model`,
`provenance`. Provenance is null for standalone mathematical FIR; a producer
must supply the complete non-null source record below. The mathematical model
has exactly `schema_version`, `template`, `time_unit`, `geometry`, `populations`,
`states`, `parameters`, `reactions`, `equations`, `observables`, `assumptions`,
`capabilities`. Time unit is `s`; capabilities are exactly
`{"ode":true,"ssa":false}`. These declarations grant no native support until
the wire, reference, implementation and acceptance gates pass.

`geometry` is a role-keyed object of explicit litre quantities, with exactly
`cell` or exactly the three strain roles plus `medium`. `populations` is an
empty object for the single cell or a role-keyed object of the three exact
positive integer-valued binary64 populations. Every count, rate, geometry,
population and sensing choice enters mathematical identity.

State entries have exactly `id`, `owner`, `quantity`, `scope`, `unit`, `initial`.
IDs are the state roles in the table; owner is its canonical owner role.
Quantity is `molecular_count`, unit `molecule`; scope is `representative_cell`
for intracellular states and `environment_total` for e_k. Initial values must
correspond to the exact source amounts. Parameter entries have exactly `id`,
`value`, `unit`, `basis`, using the canonical roles/units/bases above. Volumes
and populations are not duplicated as rate parameters.

Observable entries have exactly `id`, `state`, `owner`, `scope`, `unit`; preserve
the source observable ID, map to its canonical state and derive its owner,
scope and molecule unit. Renaming an observable changes the mathematical
interface and its identity. An empty source observable array yields an empty
FIR observable array.

### Finite typed mathematical templates

Use leaf nodes `{"op":"parameter|state|volume|population|flux","id": role}`
with one literal op token, never the pipe-separated shorthand shown here.
Use binary `add`, `subtract`, `multiply`, `divide` nodes with exactly `op`,
`left`, `right`. Volume leaves resolve `geometry`, population leaves resolve
`populations`, and flux leaves resolve reaction IDs. No free variable, cycle,
arbitrary expression, numeric string, `eval` or serialized callback is allowed.

The only nonlinear node is

```json
{"op":"hill_repression","sensor":{"op":"divide","left":{"op":"state","id":"p3"},"right":{"op":"volume","id":"cell"}},"threshold":{"op":"parameter","id":"K1"},"exponent":{"op":"parameter","id":"n1"}}
```

That is gate 1's single-cell node. Other nodes substitute the exact P09 sensor,
owning volume, threshold and exponent roles. It denotes G(c)=1/(1+(c/K)^n),
with P09's stable reciprocal evaluation and nonnegative sensor domain. It has
no propensity, signal consumption or stochastic interpretation.

Let `P(r)`, `X(s)`, `V(o)`, `N(o)`, `F(r)` abbreviate the corresponding leaves,
and `+(a,b)`, `-(a,b)`, `*(a,b)`, `/(a,b)` the ordered binary nodes. These are
metanotation, not serialized strings. Reaction entries have exactly `id`,
`flux`, `stoichiometry`:

| Reaction ID | Exact flux template | Nonzero updates |
|---|---|---|
| `basal_i` | P(b_i) | m_i:+1 |
| `repressed_i` | *(P(h_i), G_i) | m_i:+1 |
| `mrna_decay_i` | *(P(gm_i), X(m_i)) | m_i:-1 |
| `translation_i` | *(P(beta_i), X(m_i)) | p_i:+1 |
| `protein_decay_i` | *(P(gp_i), X(p_i)) | p_i:-1 |
| `synthesis_k` | *(P(sigma_k), X(p_k)) | a_kk:+1 |
| `signal_decay_jk` | *(P(ga_jk), X(a_jk)) | a_jk:-1 |
| `medium_decay_k` | *(P(ge_k), X(e_k)) | e_k:-1 |
| `export_jk` | *(P(out_jk), X(a_jk)) | a_jk:-1, e_k:N(strainj) |
| `import_jk` | *(P(in_jk), *(V(strainj), /(X(e_k), V(medium)))) | a_jk:+1, e_k:*(literal -1, N(strainj)) |

IDs substitute the indices directly, e.g. `basal1`, `signal_decay23`,
`export31`. Exactly 15 single-cell or 48 community reactions are required,
including zero-rate reactions. Stoichiometric values are literal +1/-1 or a
population leaf for export; import uses the dedicated coefficient object
`{"op":"negative_population","id":"strain1"}` with the corresponding strain.
The last table row's negative product is explanatory metanotation, not a general
numeric-literal AST extension. This coefficient denotes -N_j exactly and
requires separate schema/semantic review; it is not an SSA jump size.

Equation entries have exactly `state`, `unit`, `rhs`, with unit `molecule/s`.
Require the following exact ordered expressions, independently checking that
reaction updates and equations agree:

    m_i: -(+(F(basal_i), F(repressed_i)), F(mrna_decay_i))
    p_i: -(F(translation_i), F(protein_decay_i))
    a_jk, j=k: -(+(F(synthesis_k), F(import_jk)),
                  +(F(export_jk), F(signal_decay_jk)))
    a_jk, j!=k: -(F(import_jk), +(F(export_jk), F(signal_decay_jk)))
    e_k: -(+(+(N(strain1)*F(export_1k), N(strain2)*F(export_2k)),
                 N(strain3)*F(export_3k)),
            +(+(+(N(strain1)*F(import_1k), N(strain2)*F(import_2k)),
                    N(strain3)*F(import_3k)), F(medium_decay_k)))

Every infix product in the last expression expands to an ordered `multiply`
node. No operand commutation, reassociation, cancellation or zero-rate removal
is accepted as the same template. Distinct expressions are not automatically
declared algebraically equivalent. Population weighting occurs on medium
updates; no intracellular flux is multiplied by population.

Required assumptions are `constant_rates`, `fixed_volume`, `no_interventions`,
`read_only_sensing`, `well_mixed`, plus `single_representative_cell` or
`fixed_populations` and `three_strain_ring` respectively. They are exact unique
string tokens; additional assumptions require a later contract.

### Source record

Non-null provenance has exactly `design`, `experiment`, `symbol_map`. Source
references contain schema version, ID, revision and digest. The map has exactly
`owners`, `states`, `parameters`, `reactions`: one entry per FIR owner/state/
parameter/reaction, with no extra or duplicate FIR key. Owner entries bind the
canonical role to the source owner ID; state entries bind canonical state ID to
the full source amount endpoint; parameter entries bind canonical parameter ID
to source parameter ID. Reaction entries bind canonical reaction ID to source
collection, source function ID and its exact role within that function (e.g.
`basal`, `induced`, `translation`, `mrna_decay`, `protein_decay`). Source collections are `gates`,
`signal_synthesis`, `signal_losses`, `transport` only. These symbolic fields and
the exact proposed member names are encoded in the schema:

| Map | Closed entry fields |
|---|---|
| `owners` | `fir_owner`, `source_owner` |
| `states` | `fir_state`, `source_endpoint` |
| `parameters` | `fir_parameter`, `source_parameter` |
| `reactions` | `fir_reaction`, `source_collection`, `source_function`, `source_role` |

Gate source roles are `basal`, `induced`, `mrna_decay`, `translation`,
`protein_decay`; synthesis/loss roles are `synthesis`/`loss`; transport roles are
`export`/`import`. These exact names remain proposed until reviewed schema and
fixture acceptance.

A producer revalidates both committed documents and exact Design linkage, then
derives every state, value, geometry, population, role, reaction and observable
from those sources. A mathematically valid standalone model can still fail
producer correspondence. Reusing a same-FIR digest with different sources does
not excuse stale source digests, wrong maps, units, initial values or bindings.
No network resolver, display-label lookup or trusted-map shortcut is allowed.

## Normalization and mathematical identity

Validate structure, numerical domains, uniqueness, role coverage and the entire
template before normalization. Apply P03's FIR binary64/Unicode raw rules, not
P01's source integer-token rule. Semantic population/Hill constraints are checked
on represented values; a rounded population outside the safe-integer domain
is still rejected. Producer-source agreement is checked separately.

For proposed canonicalization 0.2.0, sort exactly `states`, `parameters`,
`reactions`, `observables` by unique `id`; `equations` by unique `state`; and
`assumptions` by complete string. Use UTF-16 code-unit order. Geometry/population
objects are JCS objects, not extra sortable declaration arrays. Preserve every
other array and AST operand. No biological graph-isomorphism normalization is
promised. N is idempotent and does not mutate the validated input.

Model bytes are `JCS(N(model))`. Identity bytes are JCS of exactly

```json
{"domain":"fenix.fir","canonicalization_version":"0.2.0","model":"<the normalized object, not a serialized string>"}
```

The mathematical digest is SHA-256 over those identity bytes. Envelope version,
provenance, producer, execution, timing and result samples do not enter model
identity; the wrapper's canonicalization version and model schema/template do.
Changing volume/population changes identity even when a special trajectory is
unchanged. A consistent source-ID renaming or declaration permutation can change
source digests/maps while preserving FIR when the fully resolved model and named
observable interface are identical. The two templates have distinct identities.

Canonical state declaration order is `m1,m2,m3,p1,p2,p3` for the single cell and
`a11,a12,a13,a21,a22,a23,a31,a32,a33,e1,e2,e3,m1,m2,m3,p1,p2,p3` for the community.
This differs from the feasibility study's mRNA/protein-first vector order.
Future native/reference comparisons must map explicit IDs, never compare
unlabelled columns by position. Canonical bytes may need a separate lossless
transport representation under the unchanged P01/P03 distinction.

## Execution, results and verified readback

Propose extending P04's requested-grid, work-count, zero-only-grid and explicit
failure discipline to these templates, with P09's stage and returned-count
domain. Validate finite nonnegative strictly increasing sample times, positive
finite controls and explicit method selection before any solver call. Preserve
signed zero in result/manifest transport, not in JCS identity. No clipping,
retry with another method or analytical substitution is allowed.

The new backend profiles retain their respective P07 payloads and token rules,
except for new discriminators and the explicitly multi-state derivative options:

- Python: DOP853 or Radau, existing SciPy options/floor; Radau declares
  `jacobian: "state_dependent_exact"`, DOP853 `not_supplied`.
- Julia: Tsit5 or Rodas5P, P07-Julia options; both declare
  `jacobian: "state_dependent_exact_inplace"` and
  `time_derivative: "autonomous_zero_inplace"`. The zero derivative has exactly
  the model's state dimension. Retain `njev`/`nw` meanings and exact integer
  transport; never relabel W-matrix counts as LU counts.

Exact state-dependent Jacobians follow P09 and require independent
finite-difference/reference evidence before native adoption. Existing M0 backend
profiles retain their exact original derivative options and scope. An old profile
cannot be used to claim a nonlinear oscillator run.

Proposed ODEResult 0.2.0 retains every P07 result field, adding exactly
`state_owners`, `state_scopes`, `observable_owners`, `observable_scopes` as required
parallel arrays. Each agrees exactly with normalized FIR declarations. States
and observables are sample-major count matrices; direct observables are
bit-identical copies of their mapped state columns, including signed zero.
Zero-time samples match initial counts numerically. Empty observables retain
empty rows and metadata arrays. Medium totals and per-cell counts remain
distinguishable even when units and numeric values coincide.

Proposed RunManifest 0.2.0 retains P07's exact core field set, with the new source,
FIR, result and backend version references. Preserve exact result-byte SHA-256,
optional trusted exact manifest-byte checksum, original transport bytes,
observed environment/build IDs/counters/timing, and deterministic no-RNG record.
No host-version match or runtime Git/network lookup is required for readback.

Capture revalidates the exact source pair, compiles and solves once. Readback
revalidates sources and recompiles, but never solves. Verify all source fields,
FIR identity/version pair, backend options, grids, counters, dimensions,
IDs/owners/scopes/units, observable mapping/copies and byte checksums. Reject
every mismatch without repair. Success records cannot attach arbitrary supplied
trajectories to digest strings. Mutable input/output buffers must not expose
mutable state inside an accepted record.

Internal consistency does not establish execution authenticity or numerical
correctness. Plausible positive-time samples with recomputed checksums can pass
readback; independently trusted checksums or mathematical reference comparison
provide different evidence. Local solver tolerances are not global error bounds.
M0's accepted analytical bound must not be silently reused as an oscillator
threshold. Oscillator reference and acceptance definitions require their own
explicit human decision.

## Evidence gates and review decisions

The [review plan](wire-review-plan.md) lists positive/negative obligations and
cross-feature examples. It is a test plan, not a frozen fixture catalog or an
executed native suite. The separate [equation audit](equation-audit.md) now
supplies proposed P09-law, reaction/RHS, precision and exact weighted-transport
evidence without importing the schema/example builders. Its finite-probe results
require review and do not replace syntax, identity or native conformance checks.
Before implementation, provide and independently review:

1. Independently review the accompanying closed BioIR/FIR/result/backend schemas
   and twelve source/FIR/zero-grid examples for both templates. Supply additional
   positive-time reference/result examples and a complete literal case catalog.
2. Language-neutral raw-input, binding, identity and rejection catalogs with
   literal witnesses, expected categories and JSON Pointer paths. Include numeric
   token/Unicode boundaries and no general error-precedence inference.
3. Independently derived normalized objects/model bytes/identity bytes/digests,
   checked in separate Python and Julia/ECMAScript tools without native FENIX.
   Candidate generators alone cannot certify their own expected output.
4. Accepted independent component and nonlinear reference definitions, numerical
   domain/method evidence, agreed comparison/oscillation/weighted-balance
   thresholds and a source-role-to-reference-state map.
5. Explicit PI ratification of the exact wire revision and acceptance of those
   bounded reference artifacts. Any scientific changes require renewed review.

After those gates, implement independent native languages in separate focused
PRs, then run exact FIR parity, source-linked capture/readback, independent
trajectory/cycle/balance checks, clean installations and all original M0/M1
regressions. Native and scientific implementation acceptance remain separate
from contract approval; no merge, issue closure or release follows automatically.

PI review choices include version identifiers; fixed template/source-role
representation; explicit unit/basis and population token policy; population-valued
signed FIR updates; canonicalization scope/ordering; multi-state scope transport;
and new nonlinear backend discriminators/options. No choice here becomes binding
merely because an example or repository test passes.
