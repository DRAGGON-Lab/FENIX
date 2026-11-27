# P08 M1 executable wire and evidence packet

**PROPOSED for exact-revision PI acceptance; native implementation is gated.**
Refs #31 and #34. This finishes a concrete executable review candidate for the
P08 mathematics, not a native package implementation. The PI's
[bounded completion-scope approval](../../docs/verification/m1-completion-scope-acceptance.md)
remains binding: valid inputs can fail at a negative sensing stage; no clipping,
signed sensing continuation, automatic method substitution or universal success
guarantee is introduced. Passing these tools does not ratify this packet.

## Version and representation choices

| Artifact | Proposed discriminator |
|---|---|
| Community Design / Experiment / mathematical FIR | `schema_version: "0.2.0"` |
| Community FIR template | `community.exchange.hill.v1` |
| Community FIR canonicalization | `0.2.0` with the M1-specific rules below |
| Scoped ODEResult / RunManifest | `schema_version: "0.2.0"` |
| SciPy backend | `python-scipy-community-ode/0.1.0` |
| SciML backend | `julia-sciml-community-ode/0.1.0` |

These are wire-profile proposals, not published package versions or P06 policy.
M0 0.1.0 rules, identities and backend labels remain unchanged. Oscillator
0.3.0 models and their backend labels remain distinct. Canonicalization 0.2.0
dispatch is explicitly model-version/template-specific: M1 has three sortable
collections; the separate proposed oscillator format has six. A reader rejects
unknown or mismatched version/template/backend pairs without migration.

## Complete source and FIR shape

The existing closed [BioIR](bioir-m1.schema.json) and [FIR](fir-m1.schema.json)
schemas specify the finite member sets, fixed parameter/state roles, units and
reaction/equation ASTs. The review packet preserves those draft shapes. Source
envelopes contain exactly `content` and `digest`; there is no community metadata,
callback, general function expression, intervention or implicit resolver field.
Immutable revision construction follows P01; this finite wire profile neither
changes M0 constructors nor introduces a new predecessor serialization field.

Source counts/rates are finite nonnegative binary64, K and volumes strictly
positive. Population values are integral 1..9007199254740991; Hill exponents
are integral 1..4. As in P01 schema integer semantics, exact `3`, `3.0` and `3e0`
population values are permitted; bools are not numbers. This differs from P10's
separately proposed population-token restriction and does not alter it.
P01's safe integer-token restriction applies to source numeric tokens; real
tokens decode to binary64, rejecting nonzero underflow and overflow. FIR numbers
instead use P03 binary64 decoding, including integer-form rounding before domain
checks. UTF-8 is strict, BOM/duplicate decoded keys/unpaired surrogates fail,
and Unicode scalar sequences retain their original normalization form.

Design owner IDs are globally unique; roles sender/receiver/env occur once.
Species IDs are owner-local and port IDs species-local, so repeated local IDs
under different owners are valid. Each strain has one signal; receiver also has
one reporter. Signal ports are exactly inward/outward transport; env signal
also has one density output; reporter has exactly one sensor input. Every kind
occurs once in its species. Full owner/species/port tuples resolve all five
required connections. Alias-only references, reversed kinds, duplicate/missing
edges, cross-strain shortcuts, wrong quantity and sensor writes fail. Roles
resolve mathematical quantities; display strings never resolve endpoints.

Experiment binds the exact local Design ID/revision/content digest. It assigns
all 13 parameter roles, all four initial counts and both populations exactly
once through closed objects. Observables are unique named direct state copies;
empty observables are allowed. Compilation independently verifies every role,
unit, value, volume, population, binding and observable. FIR provenance contains
the exact Design/Experiment digests and exhaustive canonical-role-to-source
owner/species maps. Provenance is excluded from mathematical identity, but must
agree with the supplied sources in a producer record. A self-consistent digest
is not authentication, and mathematical identity never permits stale source
substitution.

All ten reactions remain present at zero rates. The existing schema enumerates
their exact flux ASTs and signed updates, including population factors in medium
updates and zero signal consumption for sensing/reporter production. All four
equation ASTs are exact ordered templates. Unsupported operations, free symbols,
changed operand order, reassociation or alternate equivalent expressions fail;
there is no general algebraic-equivalence claim.

## Canonical identity

Validate complete structure, role coverage, bindings, domains and the finite
mathematical template before normalization. Canonicalization 0.2.0 for this M1
template sorts reactions/observables by unique `id` and equations by unique
`state`, in UTF-16 code-unit order. Preserve every other array and every AST
operand. Role-indexed counts/rates/geometry are JCS objects. Normalization is
fresh and idempotent; it never edits validated input.

```text
model_bytes = JCS(normalized_model)
identity_bytes = JCS({"domain":"fenix.fir",
                      "canonicalization_version":"0.2.0",
                      "model":normalized_model})
digest = SHA256(identity_bytes)
```

Version and template remain inside mathematical identity. Source IDs, source
declaration order and provenance can change while a fully resolved model and
named observable interface retain FIR identity. Every count, rate, population
and volume affects identity. Observable renaming/removal changes the interface
and identity. No source graph-isomorphism inference is promised.

The [literal candidate catalog](wire-candidates/catalog.json) contains independent
input artifacts, explicit normalized objects, exact model/identity byte files
and digest text. Python uses rfc8785; a separately authored
[ECMAScript audit](identity_audit.cjs) derives normalized models directly from
raw candidate FIR and verifies bytes and source hashes using JSON.stringify.
Writers construct proposed candidates, never accepted expectations. Audits do
not import native FENIX or the candidate writers. Existing Decimal/BigFloat laws
supply the numerical examples; an AST audit independently checks both serialized
equation representations against those laws and asymmetric open-system probes.
This is bounded independent evidence, not exhaustive input or mathematical proof.

## Scoped results and backend manifests

The closed [result](ode-result-m1.schema.json) and
[manifest](run-manifest-m1.schema.json) schemas retain P07's core payload plus
the four required owner/scope arrays. Canonical state columns are explicitly
`env.signal, receiver.reporter, receiver.signal, sender.signal`. Owners are
canonical roles `env, receiver, receiver, sender`; scopes are
`environment_total, representative_cell, representative_cell, representative_cell`.
Units are molecule and time is seconds. This order differs from reference
columns; compare through explicit IDs. Observable IDs sort canonically and all
parallel metadata follows the mapped state. Values are sample-major, direct
observable copies are bit-identical including signed zero, and zero-time
counts match the model numerically. Empty observables have empty arrays/rows.

Result/manifest transport preserves signed zero and exact integer-form budgets,
work counts and counters; it is not JCS-normalized. The literal budget
9007199254740993 demonstrates transport beyond the scientific safe-integer
policy. Fraction/exponent tokens are invalid for integer counters even if their
value is integral. Preserve original bytes, output SHA-256, optional externally
trusted manifest checksum and opaque observed runtime/producer fields. Do not
look up a host Git/runtime identity or fetch a source during readback.

SciPy uses DOP853 or Radau with the P07 options and tolerance floor. Radau
declares `state_dependent_exact`; DOP853 `not_supplied`. Julia uses Tsit5 or
Rodas5P, full in-place exact state-dependent Jacobian, four-dimensional
autonomous-zero time derivative, P07-Julia options and signed 64-bit maxiters
9223372036854775807. Counters retain their backend meanings: Julia `nw` is not
SciPy `nlu`. `save_start` agrees with whether the first requested time is zero.
No method fallback occurs. Zero-only grids validate first and skip integration,
with all work counters zero. Success requires complete finite nonnegative output
at the requested grid; exhaustion, invalid stages or incomplete output fail.

Capture validates, compiles and solves once. Readback revalidates exact local
sources, recompiles and checks identity, source maps, bytes, backend options,
grids, dimensions, owner/scope arrays, observable copies and counters without
solving/network access. Internal consistency is not execution authentication or
numerical accuracy. The positive-time candidate manifests are explicitly marked
analytical illustrations, with synthetic environment/work fields, **not observed
native runs**. They exist to review wire relations and cannot establish a solve.

## Frozen numerical proposal and acceptance request

Retain the original ten analytical cases/30 samples and both independent
evaluators unchanged. The [SciPy investigation](../../conformance/community/feasibility/README.md)
and new independent Julia probe use baseline rtol=1e-9/atol=1e-11, refined
rtol=1e-11/atol=1e-13, maximum step 1 second and 200000 RHS calls per bounded
run. Each method has 60 four-state sample comparisons. State comparison remains
`b_i(t)=1e-9+1e-8|reference_i(t)|`. Closed-balance bounds are
`sum_i w_i b_i(t)+|M_num(0)-M_ref(0)|`, with weights `(N_s,N_r,1,0)` in reference
order. Open-system and read-only-sensing evidence retains the exact independent
balance checks. Jacobians are checked against high-precision differentiation at
asymmetric, zero and threshold probes; no native comparison chooses thresholds.

The SciPy long-tail control is retained unchanged. Julia observes the same
physical tail under its two settings; neither trajectory equality nor SciPy's
failure outcome is imposed on Julia. Explicit failures remain within the PI's
approved completion policy. Reports retain the actual outcomes and work counts.

Before #32/#33, the PI must accept this complete packet at its reviewed revision:
the finite schemas/binding/numeric rules, normalization/version choice, literal
positive/rejection/byte catalogs, unchanged ten-case/30-sample independent
reference definitions and frozen bounded numerical criteria. Review must include
the hosted Julia feasibility result; **a missing or failed result is not PASS**.
Full native implementation, clean installations, integration #35, empirical
validity and parent/release acceptance remain subsequent distinct gates.
