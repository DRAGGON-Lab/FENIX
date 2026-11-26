# P09 component-reference acceptance — 2026-11-26

The human PI accepted the bounded component references on
[PR #87](https://github.com/DRAGGON-Lab/FENIX/pull/87) at reviewed commit
`6ab3dd41a072af02ffef516139390e6d710cec2c` in this Codex conversation.
The question identified 11 analytical component-reference cases (33 samples),
independent Decimal/BigFloat derivations and passing comparison controls, and
explicitly retained nonlinear-cycle references, wire/identity contracts and
native implementation approval as pending. The PI selected:

> Accept the bounded component references

This explicit instruction supplies acceptance; CI, agent review and agreement
between solvers do not supply it. No independent human recomputation is claimed.

## Reviewed artifacts and accepted scope

The [component-reference definitions](../../conformance/oscillators/references/README.md)
specify every input, state position, unit, quantity basis, sample time and
analytical law. Acceptance covers the exact 11 definitions and their 33 samples:
eight driven-repression cases (single-cell and community, Hill n=1..4), catalytic
translation, a balanced community equilibrium and closed heterogeneous community
transport. It includes the independent high-precision reference derivations and
their initial-condition, equation-residual and precision-refinement checks.

The agent recomputed these SHA-256 values from the reviewed Git blobs:

| Artifact | SHA-256 |
|---|---|
| `conformance/oscillators/references/cases.json` | `071615af6915854cb9ebb53990d44eafad967b88221bccfca285dcdc610d2355` |
| `conformance/oscillators/references/reference.py` | `497127a82add2992da5cc9c101dc5cec0c9e9447774a4864d67d5b57abb380aa` |
| `conformance/oscillators/references/reference.jl` | `3c1c96857f4d27caee89bf36a39306ed845ec9a11ad186702923b812bdd51755` |

The immutable reviewed commit identifies the remaining tests and comparison
code. Both evaluators pin the complete raw catalog before trusting report hashes.
This record preserves all catalog, evaluator, test, comparison and lock bytes.

## Evidence and limits

**PASS:** nine local analytical/comparison control tests, including catalog and
sample corruptions, wrong laws/source rates and weighted conservation. The
unchanged study also passes all 828 comparisons against these component laws.
The reviewed revision's hosted
[independent analytical job](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45902227976/job/140190500766)
passed the 33 Decimal/BigFloat samples and Julia negative controls.
Julia execution is **NOT RUN locally** because the runtime is unavailable.

The accepted references isolate components; they do not establish nonlinear-cycle
accuracy over the 80,000-second study. The feasibility parameter sets, oscillation
criteria and candidate SciPy comparison bound remain study choices, not accepted
native ODE tolerances. Complete versioned wire schemas, role bindings, normalized
identity vectors and rejection catalogs still require review and acceptance.
Native oscillator execution remains **NOT RUN — unsupported profile**.

The bounded mathematical ratification of ADR-P09 remains recorded
[separately](p09-math-ratification.md). Neither this acceptance nor that
ratification establishes empirical biological validity, native capability or
implementation acceptance. Existing M0 and M1 gates remain intact. Issue #84,
merge, release and broader reference acceptance remain separate.

Historical PROPOSED labels in the reviewed snapshot and generated reports
retain their original meaning; this subsequent explicit decision governs only
the component scope above.
