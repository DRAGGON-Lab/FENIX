# P08 execution feasibility — approved bounded completion scope

**PI approved alternative 1 on 2026-11-27 at reviewed revision
`6964014efd9e869bc98337eb3cece3c6ea837f1b`.** The
[acceptance record](../../docs/verification/m1-completion-scope-acceptance.md)
preserves the explicit instruction, artifact hashes and bounded scope.
Complete executable-profile and native implementation approval remain separate.
Refs #31 and #34, [ADR-P08](ADR-P08.md), and the approved delivery plan's
instruction to return a documented proposal when feasibility raises a domain
or bound question.

## Evidence and uncertainty

P08 rejects negative extracellular sensing stages without clipping. Its
requested-grid/work-limit discipline permits positive finite maximum steps,
but does not establish a positivity-preserving internal-stage guarantee for
DOP853, Radau, Tsit5 or Rodas5P. Local error tolerances do not provide that
guarantee either.

The [numerical investigation](../../conformance/community/feasibility/README.md)
compares SciPy directly with existing analytical laws. The recorded bounded
matrix passes the proposed state and derived closed-balance bounds. A separate
long-tail control with unchanged driven-n1 rates/counts, grid `[0,1000]` seconds
and maximum step 10 seconds attempts negative sensed stages for **both SciPy
methods at both proposed settings**. Its exact extracellular solution stays
strictly positive. The failure is an internal-stage diagnostic, not a negative
analytical solution or an accepted returned sample. The report retains the
first offending state, time and work count. No accepted reference changes.

This does not disprove P08's domain policy: rejecting the attempt is consistent
with that policy. It does show that unrestricted completion of valid nonnegative
mathematical inputs cannot be promised from these controls alone. The PI has
accepted explicit stage-domain failures within this bounded completion scope.
Julia stage feasibility remains unmeasured.

## Alternatives and impact

1. **Retain strict sensing-domain rejection and bound success claims explicitly.**
   Valid requests may fail with a stage-domain diagnostic. After complete
   four-method evidence, accept only reviewed cases/settings as bounded success
   evidence. Keep the proposed state bound and derive conservation bounds from
   population weights and initial representation error. Mathematics and failure
   policy remain intact; the completion limit must be documented clearly.
2. **Specify tighter executable-domain restrictions.** Investigate a reviewed
   rate/step/horizon/control envelope or positivity-preserving strategy. One
   smaller step that happens to work cannot prove a universal guarantee. New
   restrictions, methods or retries need explicit contract text and independent
   controls before native adoption.
3. **Define an extension for negative sensing stages.** This changes numerical
   domain semantics. Signed Hill continuation can have singularities for odd
   exponents and does not represent physical negative counts. Clipping changes
   the evaluated equations. Neither is authorized here; either requires a
   PI-ratified ADR and independent edge/accuracy evidence.

Approved direction: retain strict failure (alternative 1) and record its bounded
completion scope. Do not silently change sensing or reject otherwise valid
source documents to hide the integration boundary. If broader completion is
required, investigate alternative 2 before implementation.

## Recorded decision and remaining gate

The PI has chosen alternative 1 at the exact reviewed revision above. Approval
of unfinished wire/identity/rejection artifacts is not inferred. The complete
executable contracts and bounded evidence still need exact-revision acceptance.
The complete M1 review packet still requires:

- Finished version-specific source/FIR normalization and result/backend schemas.
- Independent literal positive, rejection, normalized-model, canonical-byte and
  digest catalogs, including numeric-token, owner/scope and source-binding cases.
- Acceptance of the existing ten cases/30 samples at an exact revision.
- Julia method-stage feasibility, full numerical settings and reviewed state and
  weighted-balance bounds frozen before native comparison.

Until those artifacts and decisions are accepted, native #32/#33, integration
#35, epic #7 closure and downstream #84 native work remain gated. Passing this
investigation alone supplies no PI acceptance; the recorded scope decision does
not approve a complete M1 packet.
M0 and accepted oscillator references retain their own identities and scope.
