# P10 proposed wire review and verification plan

Refs [#84](https://github.com/DRAGGON-Lab/FENIX/issues/84),
[PROPOSED ADR-P10](ADR-P10.md). This is a review checklist and test design,
**not** an accepted fixture catalog. Literal inputs, exact paths/categories,
independent byte/numerical expectations and human acceptance remain to be
supplied before native implementation. Existing P01/P02/P03/P04/P07/P08/P09
artifacts remain authoritative in their own reviewed scopes.

## Concrete workflows to represent in both languages

1. Author the six-state single-cell Design and separate Experiment from the
   reviewed illustrative study; commit, compile and compare independent FIR
   bytes. Run both approved native methods only after eligibility approval;
   capture/read back exact sources and compare explicit state IDs to references.
2. Author the 18-state community with one gate per strain, nine intracellular
   signals and three medium totals. Require all eighteen directed transport
   edges. Map reference columns explicitly: the canonical a/e/m/p order differs
   from the study's m/p/a/e order. Compare cycle observations and exact weighted
   signal-balance definitions without conflating per-cell and total counts.
3. Rename owner/species/port/parameter/function source IDs consistently, reorder
   declarations and advance exact revisions. Resolved mathematics and named
   observables retain FIR identity; source identities/maps change. An old run
   cannot be rebound to the new sources solely because the FIR digest matches.
4. Use accepted analytical component cases: driven repression n=1..4,
   catalytic translation, heterogeneous closed transport and equilibrium.
   Require the component's exact disabled reactions/initial conditions and
   source-role map; native/reference agreement cannot be inferred from labels.
5. Exercise broken-channel and Hill-one controls with exactly the reviewed
   changes, keeping the independent reference definitions separate from native
   implementation. Retain complete traces and explicit nonoscillation outcomes.
6. Replicate populations and medium volume together while scaling medium totals.
   Per-cell dynamics can remain unchanged while the complete model identity
   changes. Independently test each strain's population/volume and each signal's
   asymmetric rates so symmetric examples cannot conceal wrong owner binding.

## Required positive/negative matrix

Each row becomes multiple literal fixtures as necessary. Expectations below
describe proposed rules; they do not report executed parser/validator outcomes.
Use single-defect witnesses to fix a diagnostic category/path. Multiply invalid
documents must not accidentally impose a new cross-language error precedence.

| Area | Positive controls | Negative controls / independent evidence |
|---|---|---|
| Version isolation | Existing M0 unchanged; each new template has its declared version pair | New documents in old readers; old nonlinear backend token; unknown versions; template/version disagreement |
| Raw input | Whitespace/key permutations; Unicode metadata; permitted signed zero/subnormals and numeric spellings | Duplicate decoded keys, escaped aliases, malformed UTF-8/surrogates, nonzero underflow, overflow, bool-as-number, source integer-token overflow |
| Population tokens | Exact integer-form 1 and 9007199254740991; matching typed assignments | 0, negative, fractional/exponent tokens, bool, above-safe values, missing/extra owner, medium population |
| Source identity | Separate immutable revisions, metadata-only changes, explicit predecessor, full exact local Design reference | Stale/recomputed-but-untrusted digest distinction, same revision changed content, wrong ID/revision/digest, implicit resolver fetch |
| Owner/species/port namespaces | Repeated local species/port IDs under different owners; unique roles | Duplicate IDs in the applicable namespace, alias-only endpoints, wrong owner, wrong port kind, missing/extra species/ports |
| Gates and sensing | Exactly three role-bound gates; p_prev single-cell or a_i,prev community; read-only input | Missing/duplicate gate, successor input, medium input, cross-strain sensor, wrong transcript/protein pair, added sensing sink |
| Parameter roles | All 21/54 roles with exact units/bases; zeros and finite nonnegative counts | Swapped beta/decay or synthesis roles despite equal units; K<=0; n outside 1..4; negative/nonfinite values; missing/extra/unused assignment |
| Catalytic production | Translation consumes no mRNA; synthesis consumes no synthase and targets only a_kk | Transcript/catalyst sink, wrong strain/signal target, swapped synthesis source, invented reaction |
| Transport | All j/k export/import pairs, distinct asymmetric rates, exact N_j medium coefficients | Reversed direction, duplicate/missing edge, cross-strain shortcut, signal substitution, unweighted/wrong-owner/wrong-sign medium updates |
| FIR templates | Full 15/48 reactions including zero rates; exact ordered equation/flux AST | Dropped zero reaction, reordered operands, reassociated expression, free variable, unsupported op, flux cycle, reaction/equation disagreement |
| Scientific identity | Independent JCS bytes; six collection permutations; idempotence and readback | Changes to every rate/count/volume/population, scope, sensing, observable ID/target or version must alter identity or reject; no algebraic/isomorphic equivalence assumption |
| Source correspondence | Exact exhaustive owner/state/parameter/reaction maps, source assignment values | Correct standalone math with stale sources, wrong map, wrong role/value/unit, omitted/extra observable; FIR-only comparison insufficient |
| Multi-state results | Explicit canonical IDs with owner/scope/unit arrays and direct observable copies; empty observables | a/e/m/p permutation, missing/duplicate column, scope/owner swap, per-cell/total substitution, wrong unit, missing metadata, misaligned samples |
| Execution domains | Requested grids including late first time and zero-only; supported methods; signed linear stages under P09 | Negative nonlinear sensor stage, nonfinite arithmetic, negative returned count, incomplete grid, exhausted budget, silent clipping or method substitution |
| Nonlinear backend profiles | Exact derivative dimensions; independent Jacobian checks; each profile's own counters/options | M0 constant-Jacobian label, wrong derivative entry, wrong option, Julia nw relabelled as nlu, unsupported profile/method |
| Transport numerics | P07 signed-zero-preserving values; exact large budget/counter integers; opaque producer/build/environment preservation | JCS-normalized results, float/coerced counters, source/FIR numeric policy applied to result transport, invented runtime identity |
| Capture/readback | Capture solves once; load recompiles exact supplied sources without solving/network; immutable/fresh exports | Arbitrary trajectory attachment, solver/network during load, same-FIR source substitution, mutable buffer alias, stale result/manifest checksum |
| Trust limits | Trusted exact-byte expectations detect replacement; independent numerical checks assess samples | Plausible altered positive-time values with all checksums recomputed may remain internally consistent; never claim readback proves execution or science |
| Regression and installation | Independent Python wheel and Julia archive; all M0/M1 gates preserved | Cross-language runtime dependency, fixture-dependent installed package tests, new profile leaking into old version dispatch |

## How completion will be established

For each literal fixture, retain raw inputs, the ratified rule, stage/category/
JSON Pointer, expected normalized/source identity artifacts where relevant,
reference state IDs and human review status. Retain replay coordinates and exact
witnesses for generated follow-ups. Never regenerate accepted expectations from
the native compiler/solver under test.

Independent reference validators must separately process the original raw
documents. Expected ASTs, canonical byte artifacts and mathematical references
must not be sourced solely from the proposal generator or Python/Julia parity.
Schema success alone cannot establish raw-token policy, typed bindings,
mathematical validity, exact source correspondence or numerical accuracy.

The [literal candidate audit](examples/README.md) now checks four closed structural
schemas and twelve source/FIR/zero-grid artifacts. Its structural and bounded
binding/identity/zero-grid checks and corruption controls are separate from a
general parser or scientific conformance suite. Candidate writers share shape
construction; reproduction alone is not independent mathematical evidence.

The [independent equation audit](equation-audit.md) now checks fifteen mapped
P09/proposed definitions at two precisions, reaction/RHS/reference agreement and
exact transport cancellation. Its asymmetry controls expose wrong role bindings
that symmetric primary values can hide. This is proposed evidence, requiring
acceptance and further coverage rather than an exhaustive mathematical proof.

Independent P10 raw-input/identity/rejection reports, accepted equation/reference
mapping coverage, positive-time result examples, native oscillator
execution/parity, installed native examples and human P10 ratification remain
**NOT RUN / pending**. Existing nonlinear reference CI is separate evidence.
