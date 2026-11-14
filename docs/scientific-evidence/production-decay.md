# Production–decay analytical oracle — approved

Issue [#15](https://github.com/DRAGGON-Lab/FENIX/issues/15), under the ratified
[ADR-P02 M0 model](../../spec/fir/proposals/ADR-P02.md). The human PI accepted this derivation and the concrete
[reference catalog](../../conformance/production_decay/catalog.json) at revision
`1982357b3deed88e8e0cd8f745effd5c3bd960b3`; see the
[acceptance record](../verification/ep01-production-decay-oracle.md#human-pi-acceptance-recorded).
**Current status: APPROVED.** P04 solver thresholds remain a separate decision.

## Model, units and assumptions

For time \(t\ge0\) in seconds,

\[
 x'(t)=\alpha-\beta x(t),\qquad x(0)=x_0.
\]

The state is expected molecular count per representative cell (`molecule`),
including fractional expected counts. Production \(\alpha\) has unit `molecule/s`
and first-order loss \(\beta\) has unit `1/s`. Inputs \(\alpha,\beta,x_0,t\) are
finite and nonnegative. Rates are constant; volume is fixed, conditions are
well mixed, and there are no interventions. No concentration or population
conversion is implied. This is a deterministic mathematical reference: it
makes no SSA eligibility, random-trajectory or empirical biological-validity claim.

P02 constants denote their represented binary64 values. In particular the
binary64 commonly written `0.1` is exactly
`0.1000000000000000055511151231257827021181583404541015625`.
Replacing it with decimal-real `0.1` changes the mathematical problem.

## Integrating-factor derivation and checks

Multiply by \(e^{\beta t}\):
\((e^{\beta t}x)'=\alpha e^{\beta t}\). Integrating from zero to \(t\) yields

\[
 x(t)=x_0e^{-\beta t}+\frac{\alpha}{\beta}(1-e^{-\beta t})
       \quad(\beta>0).
\]

For \(\beta=0\), integrate \(x'=\alpha\) directly:
\(x(t)=x_0+\alpha t\). This branch is taken before any division by \(\beta\).
Both expressions give \(x(0)=x_0\). For positive decay, differentiation gives
\(x'=(\alpha-\beta x_0)e^{-\beta t}=\alpha-\beta x\); the zero-decay branch
also satisfies the equation. The difference of any two solutions with the
same initial value obeys \(y'=-\beta y, y(0)=0\), hence is zero (uniqueness).

For positive decay set \(q=\alpha/\beta\). Then
\(x=q+(x_0-q)e^{-\beta t}\), a convex combination of \(x_0\) and \(q\).
It stays nonnegative and between those endpoints, increases if \(x_0<q\),
decreases if \(x_0>q\), and is constant at equilibrium if \(x_0=q\).
The approach to \(q\) as \(t\to\infty\) is monotonic. Pure decay
(\(\alpha=0\)) gives \(x=x_0e^{-\beta t}\). Zero initial count with zero
production gives the exact zero solution. For zero decay, production is linear;
if production also vanishes the solution is constant.

At fixed finite \(t\), \(e^{-\beta t}\to1\) and
\((1-e^{-\beta t})/\beta\to t\), so \(x\to x_0+\alpha t\) as
\(\beta\to0^+\). More quantitatively,

\[
 0\le (x_0+\alpha t)-x(t)
 \le \beta(x_0t+\alpha t^2/2).
\]

This follows from \(1-e^{-u}\le u\) and
\(x(t)=x_0e^{-\beta t}+\alpha\int_0^t e^{-\beta s}\,ds\).
The limit is at fixed time; it does not interchange the long-time and
zero-decay limits.

## Candidate scope and independent evaluation

The [catalog guide](../../conformance/production_decay/README.md) defines exact
input bits, the case matrix, publication format and report checks. Coverage is
bounded to these cases; it is not a guarantee for all finite binary64 inputs.
Expectations were prepared outside FENIX and outside both shipped evaluators
using exact rational Taylor sums of the solution, then checked independently
by both tools. See the [provenance and executed evidence](../verification/ep01-production-decay-oracle.md).
There is no shipped expectation-regeneration command.
The [retained rational auditor](../../conformance/production_decay/audit_rational.py)
now reconstructs that documented preparation calculation as a read-only check.
It uses exact rational half-even rounding of the Taylor enclosure endpoints,
so its publication check does not depend on finite-precision decimal arithmetic.
This bounded rational enclosure is separate evidence from the two evaluators'
observed precision stability; it does not certify solver error or all finite inputs.

Python evaluates the integrating-factor expression with `Decimal` at 100 and
200 decimal digits. Binary64 decoding precedes
[`Decimal.from_float`](https://docs.python.org/3.12/library/decimal.html#decimal.Decimal.from_float),
which preserves the represented value exactly. Julia evaluates the equivalent
\(x_0e^{-\beta t}+\alpha[-\operatorname{expm1}(-\beta t)]/\beta\)
with `BigFloat` at 512 and 1024 bits;
[`expm1`](https://docs.julialang.org/en/v1/base/math/#Base.expm1) avoids subtracting
nearby exponentials. Neither evaluator imports a FENIX package or calls the other.

## Draft numerical error budget

| Contribution | Interpretation and current evidence |
|---|---|
| Input interpretation | Exact binary64 bits are lifted to multiprecision; no decimal-real substitution. Input interpretation contributes zero representation change. |
| Reference arithmetic | Four evaluations must agree after half-even rounding to 70 significant decimal digits. Observed precision stability is evidence, not a certified interval bound. |
| Publication | Nonzero expected values are rounded half-even to 50 significant digits. For decimal exponent \(k=\lfloor\log_{10}|x|\rfloor\), the rounding bound is \(0.5\times10^{k-49}\) `molecule`. Zero is explicitly `"0"`. |
| Eventual binary64 output | A correctly rounded normal result adds at most half a binary64 ulp; subnormal absolute spacing is \(2^{-1074}\) `molecule`. Overflow/underflow and execution failure policy belong to P04. No solver output is tested here. |
| Integration | Global integration error must be assessed independently against this oracle. No integration method, step size or acceptance threshold is selected. |
| Interpolation | Dense-output/sample interpolation can add error beyond integration at internal steps. It needs separate evidence at requested times under P04. |

A future comparison may use
\(|x_{\mathrm{num}}-x_{\mathrm{ref}}|\le a+r|x_{\mathrm{ref}}|\), with absolute
tolerance \(a\) dimensioned in `molecule` per representative cell and
relative tolerance \(r\) dimensionless. Near zero, the absolute term is essential.
P04 must set solver thresholds, allocation between error sources and failure
policy. Fifty published digits do not imply fifty-digit binary64 solver accuracy.
