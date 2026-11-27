# ADR-P08 — Fixed-population two-strain community

**PI approved the reviewed contract revision `186cfb3024d64f3d0a227f16dddc6fbc0095fe05`
for [#31](https://github.com/DRAGGON-Lab/FENIX/issues/31), merged through PR #77.**

The PI stated “I approved it annd merged it, please continue with the work”.
The approved revision retains explicit follow-on gates for complete wire formats,
independent identity/trajectory/rejection catalogs and numerical-domain evidence.
Those gates apply before native M1 implementation.

## Design and Experiment

A community Design fixes a single well-mixed environment, sender and receiver roles,
and a constant positive volume in litres for each representative cell and the environment.
Each strain owns an intracellular signal species. The receiver also owns a reporter.
The extracellular signal belongs to the environment. A species address is the tuple
(owner ID, species ID). A port address adds a species-local port ID. Local identifiers
use P01's identifier grammar. Role assignments and endpoints are explicit.
Different owners can reuse a species or port ID. Display names never resolve a reference.

Each strain has one outward and one inward signal connection to the shared pool.
Transport pairs an output and input of the same signal identity across the declared
strain/environment boundary. A separate read-only density port on the extracellular
pool supplies the receiver's sensor input. A sensing edge has zero stoichiometry.
Require exactly these five edges. Reject a reversed direction, wrong quantity, alias-only
address, missing endpoint, cross-strain shortcut, duplicate role, or write through a sensor.

A separate committed Experiment names the exact Design ID, revision and content digest.
It assigns initial counts, populations and kinetic parameters by role. Require finite,
nonnegative binary64 counts and rates, strictly positive finite volumes and K, fixed
integer cell counts from 1 through 2^53−1 and an integer Hill exponent from 1 through 4.
Reject unknown fields, missing assignments, implicit conversions, interventions and growth.

## Resolved deterministic profile

The resolved state IDs are sender.signal (s), receiver.signal (r), env.signal (E)
and receiver.reporter (y). Intracellular values are expected molecules per representative
cell. E is the total extracellular count. Time is seconds. Each rate has an explicit
basis. For strain i with intracellular count a_i, export is k_out,i a_i and import is
k_in,i v_i E/V_e, both molecules per cell per second. Both rate constants have unit
1/s. Source p_s and reporter rates alpha_0 and alpha_H have per-cell molecule/s basis.
All first-order decay constants have unit 1/s.

    J_s = k_out,s s − k_in,s v_s E/V_e
    J_r = k_out,r r − k_in,r v_r E/V_e
    s' = p_s − d_s s − J_s
    r' = −d_r r − J_r
    E' = N_s J_s + N_r J_r − d_e E
    y' = alpha_0 + alpha_H H(c) − beta_y y
    c = E/V_e
    H(c) = c^n / (K^n + c^n)

K is expressed in molecules per litre. No Avogadro conversion is involved.
Reporter production consumes no signal. For fixed populations the signed balance is

    M = N_s s + N_r r + E
    M' = N_s p_s − N_s d_s s − N_r d_r r − d_e E.

The transport terms cancel pairwise. Closed transport conserves M. Changing populations
would introduce additional derivative terms and is outside this profile. At equilibrium
of a single exchange pair export equals import. Distinct rate constants need not give
equal densities.

## FIR, identity and execution

Propose a separate BioIR/FIR 0.2.0 community profile. Preserve the immutable P01
content identity rule (direct JCS over content, preserving array order) and separate envelopes, exact Design linkage and separate mathematical FIR. M0 readers reject
the new version. M0 documents retain their original identities. Use explicit role IDs
for states, fluxes, parameters and observables. Include the populations, volumes,
basis, rates, typed transport and Hill response in mathematical identity. The
producer verifies exact source coverage, role bindings and units for every term.
Only this declared equation template is supported. Use declarative typed operations
and reject executable expressions. The capability is deterministic ODE only.

The proposed [BioIR schema](bioir-m1.schema.json) and [FIR producer schema](fir-m1.schema.json)
encode this finite profile. FIR carries the typed flux AST, signed updates and
equation AST explicitly. Export updates extracellular signal by +N_i per unit of
per-cell export. Import updates it by −N_i. A reporter reaction has no signal
update. A flux reference resolves by reaction ID. Positive transfer rates remain
separate reactions even when the net rate is zero. The FIR schema enumerates the
exact templates and requires complete unique declarations. The profile identifier
and explicit payload must agree.

For this profile, sort reactions and observables by unique ID, and equations by
state ID in UTF-16 code-unit order. Role-indexed objects have fixed keys.
Preserve AST operand order. Apply P03 numeric/Unicode rules and the existing
P03 domain/version wrapper to the normalized model. Carry the new
model schema version inside the identity preimage. Exclude display labels, source maps,
producer, execution settings and results. Source renaming must preserve the mathematical
identity when the resolved model and named observable interface remain identical.

Solve coupled states with explicit native methods under the existing requested-grid
and work-budget discipline. For nonnegative c, evaluate H using (c/K)^n when c ≤ K
and the reciprocal expression 1/(1+(K/c)^n) above K. For c>0 its derivative with
respect to E is n H(1−H)/E. At E=0 use 1/(K V_e) for n=1 and zero otherwise.
The other Jacobian entries follow from the constant coefficients above, including
−beta_y on the reporter diagonal. Reject undefined stages, nonfinite arithmetic
and negative returned counts with an explicit diagnostic. Never clip. Success
requires all requested times and columns. A zero-only grid returns all initial states
after validation. Numerical feasibility across the approved cases needs independent review.

Version the result/manifest profiles to carry the ordered multi-state and observable
IDs, units and scope, run settings, exact source and FIR references, and result-byte
checksum. Reload by explicit ID correspondence. Reject duplicate, missing or
misaligned columns, wrong scope, or stale references.

## Evidence and review boundary

The [candidate catalog](examples/cases.json) and [exact arithmetic check](review.py)
exercise signed population weighting, direction and binding, volume scaling and
nonconsumptive sensing. Run `uv run --project packages/python --locked --offline python spec/community/review.py` at repository root.
These examples describe abstract count accounting and have candidate status.

Before native implementation, freeze the complete wire schemas, identity vectors,
numerical-domain behavior and supported method evidence at reviewed revisions.
Issue #34 must independently derive trajectory and sensing expectations, check
precision refinement, and fix state and weighted-balance thresholds before testing
native results. The proposed per-state bound is 1e−9 + 1e−8 |reference|. Derive
the closed-balance bound by weighting individual errors and accounting for any
represented initial-state discrepancy. Proposed values require independent evidence.

The separate [execution-feasibility decision](execution-feasibility-proposal.md)
retains bounded SciPy comparisons and long-tail stage-domain failures. The PI
approved strict failure and bounded completion scope at reviewed revision
`6964014efd9e869bc98337eb3cece3c6ea837f1b`; see the
[acceptance record](../../docs/verification/m1-completion-scope-acceptance.md).
It changes no ratified equation or failure policy and does not complete the
executable-profile gates above.

## Review questions for the PI

The [executable wire/evidence packet](executable-profile-proposal.md) now supplies
concrete source/FIR identity, scoped result/backend schemas, literal positive and
rejection catalogs and independent identity/method review tools. It is PROPOSED
and requires exact-revision acceptance; existing mathematical and completion-scope
approvals do not automatically approve it.

1. Review the proposed population-valued signed update coefficients. They extend
   P02's fixed M0 stoichiometry so that a per-cell transfer flux also updates the
   total extracellular state in the same reaction.
2. Review the binding and source profile: each owner role occurs once, owner IDs
   are unique, species IDs are unique within their owner, and ports are unique
   within their species. Every declared port has exactly the role implied by its
   species and owner. Only the five declared connections are permitted.
   Experiment observable IDs are unique. The FIR owner and species map must agree
   with the exact verified Design. Role-keyed parameters and initial counts must
   match the Experiment exactly. The producer schemas are structural checks;
   enumerating every cross-document rejection is a separate conformance task.
3. Review the domain policy for internal solver stages and tolerances against
   numerical evidence before approving the executable profile. With E = 0 use
   H = 0 directly. A negative intermediate E is outside the proposed sensing
   domain. If supported methods require a wider stage domain, specify and test it
   before implementation. Multi-state result and manifest wire schemas and independent
   byte, trajectory and rejection catalogs require further review.
