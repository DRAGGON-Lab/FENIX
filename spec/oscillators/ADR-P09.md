# ADR-P09 — Candidate single-cell and three-strain repressilator benchmarks

**Status: mathematical equations, units/bases and numerical-domain policy
RATIFIED on 2026-11-26 at reviewed revision `e84ff5b`.** Candidate parameters,
feasibility thresholds, independent references, wire formats and native
implementation retain their separate gates. No new native profile or golden
reference is approved. See the [bounded ratification record](../../docs/verification/p09-math-ratification.md).

Requested in [#84](https://github.com/DRAGGON-Lab/FENIX/issues/84). The user selected
mRNA/protein NOT gates and explicit intracellular signal pools in all three
strains, exchanging with shared-medium pools. These selections establish the
requested architecture; they do not ratify the equations, parameter choices,
wire formats or numerical thresholds below. Subsequent explicit PI approval
ratified the bounded mathematical scope stated above. Root and scoped AGENTS.md
gates apply.

The classical intracellular motif follows [Elowitz and Leibler (2000), Box 1](https://doi.org/10.1038/35002125):
three transcriptional repressors form a negative ring with separate transcript
and protein dynamics. The distributed construction below is a proposed
phenomenological model for this request, not an experimentally validated
reproduction of that intracellular circuit.

## Proposed scope and quantity conventions

Use deterministic ODEs, fixed positive cell populations and constant positive
volumes. Time is seconds, volume litres, intracellular expected molecular
counts are per representative cell, and each medium signal count is a total.
There is no implicit concentration conversion. Indices are modulo three and
`prev(i) = (i + 2) mod 3`; output i represses gate i+1.

The single-cell model has transcripts m_i and repressor proteins p_i (six states).
The distributed model has one transcript m_i and signal-synthase protein p_i in
each strain i, intracellular signal a_jk for signal k in strain j, and medium
total E_k (18 states). Synthase p_k produces signal k in strain k only. Each
strain contains exactly one NOT gate, sensing the previous signal; it contains
no complete intracellular repressilator. Three distinct signal identities have
no sensor cross-talk in this candidate. All signals can exchange with all three
strains. Medium and intracellular pools are explicit; sensing consumes no signal.
Receptor binding is represented by the response function, not additional states.

For nonnegative density c define repression

    G_i(c) = 1 / (1 + (c / K_i)^n_i).

K_i has unit molecule/L; n_i is an integer in 1..4. Evaluate using ratios no
greater than one (and the reciprocal expression above K), avoiding overflowing
powers. Rates and counts are finite and nonnegative, K and volumes strictly
positive. No growth, spatial gradients, stochastic propensity or biological
prediction is granted by this proposed benchmark.

## Proposed equations and rate bases

For both examples:

    m_i' = b_i + h_i G_i(c_i) - gamma_m,i m_i
    p_i' = beta_i m_i - gamma_p,i p_i.

b_i and h_i are transcript molecule/s per cell; gamma_m and gamma_p are 1/s.
beta is a protein-production rate per transcript (protein molecules per
transcript molecule per second), represented with rate unit 1/s and an explicit
translation role. Transcript is a catalyst for production and is not consumed
by translation. The single-cell sensor density is c_i = p_prev(i) / v_cell.

For the distributed example:

    c_i = a_i,prev(i) / v_i
    J_jk = k_out,jk a_jk - k_in,jk v_j E_k / V_e
    a_jk' = indicator(j=k) sigma_k p_k - gamma_a,jk a_jk - J_jk
    E_k' = sum_j N_j J_jk - gamma_e,k E_k.

Both exchange constants have unit 1/s. sigma is signal production per synthase
(signal molecules per synthase molecule per second), with rate unit 1/s and an
explicit catalytic-production role. Signal synthesis does not consume protein.
Each J_jk is an outward per-cell net flux; implementations must retain separate
nonnegative outward and inward reactions and the signed population multipliers.
Transport changes intracellular count by -J_jk and medium total by +N_j J_jk.

For each signal k the exact weighted balance is

    M_k = sum_j N_j a_jk + E_k
    M_k' = N_k sigma_k p_k - sum_j N_j gamma_a,jk a_jk - gamma_e,k E_k.

With synthesis and signal losses zero, each M_k is conserved. Reading a signal
adds no sink. N_j affects medium flux weighting, not a per-cell export rate.

## Candidate feasibility protocol

The complete inputs live in `conformance/oscillators/cases.json`; the accompanying
study must not import FENIX. Candidate runs use literal illustrative count-space
parameters and declare every unit/basis. They are not calibrated biological
measurements or accepted reference values. Their full-file hash identifies the
observed study inputs, not a ratified mathematical oracle.

The proposed baseline uses 0.01/s transcript loss, 0.05/s translation/protein
loss, 216 transcript molecule/s induced production, 0.01 transcript molecule/s
basal production, Hill exponent 2, K=1e17 molecule/L and 1e-15 L cells. The
community uses 100 cells per strain, 1e-12 L medium, 0.1/s bidirectional exchange,
0.01/s signal losses and 0.154/s catalytic signal synthesis. These are explicit
illustrative choices; they are not claimed to be the original paper's parameter
set. Non-symmetric initial expression counts avoid a perfectly symmetric invariant
trajectory being mistaken for absence of an oscillatory regime.

Compare DOP853 and Radau at baseline/refined settings, retaining failures. Check
oscillation after a declared transient and extend the horizon to distinguish
sustained cycles from damped transients. Record periods, amplitudes and relative
phases rather than promising equal periods between these different models.
Use peaks bracketed by earlier and later peaks so partial cycles at window
boundaries do not bias amplitudes. Require stable cycle midpoints as well as
amplitudes and periods; constant-amplitude waves on a drifting baseline are not
sustained-cycle evidence. All candidate thresholds and two analysis windows are
explicit in the catalog; none is an approved native conformance tolerance.
A low-cooperativity control and a broken-communication control must be reported.
The latter disables one signal's synthesis and sets all pools of that signal to
zero, giving an exactly invariant absent channel rather than a residual reservoir.

The candidate numerical domain permits finite real intermediate values for
linear terms, but each nonlinear sensor density must be nonnegative. Returned
counts must be finite and nonnegative. Reject undefined/nonfinite evaluations;
never clip, silently change methods or substitute analytical output. This policy
and method feasibility require PI review before native adoption.

## Native implementation and acceptance gates

The studies in this proposal are feasibility observations. They neither execute
new native FENIX profiles nor certify a future native implementation. Existing
M0, P08, independent fixture and package-installation obligations remain intact.

Before native semantic changes, the PI must review and ratify the exact model
and numerical-domain policy, then accept independent reference definitions.
Complete versioned BioIR/FIR/result wire schemas, role/binding rules, normalized
identity vectors and rejection catalogs must be frozen at reviewed revisions.
Profile/version choices remain pending that wire review; no existing version is
silently extended. Scientific FIR identity must include all model state, rate,
geometry, population and sensing semantics while excluding provenance/execution.

Required native evidence will include both languages, exact FIR parity per
model, source-linked readback, independent trajectory/oscillation checks,
weighted signal balance, invalid binding/domain failures and all M0 regressions.
The single-cell and distributed models have different mathematical identities.
Plots alone, two solvers in one backend, or Python/Julia agreement alone do not
satisfy independent scientific acceptance. This issue remains open until the
requested native examples and their gates are delivered.
