# ADR-P09 — Bounded mathematical ratification

On 2026-11-26 the human PI in this Codex conversation reviewed
[ADR-P09 on PR #85](https://github.com/DRAGGON-Lab/FENIX/blob/e84ff5b0507f60ce68bedf99831e6a2fd4f108fd/spec/oscillators/ADR-P09.md)
at commit `e84ff5b0507f60ce68bedf99831e6a2fd4f108fd` and stated:

> yes I approve ADR-P09

The question explicitly requested ratification of proposed equations,
units/quantity bases and numerical-domain policy, while retaining independent
references, wire/identity/rejection catalogs and native implementation approval
as separate gates. That question bounds this acceptance; approval is not inferred
from solver agreement, CI, the modeling-preference selections or a GitHub review.

The reviewed raw ADR blob has SHA-256
`04e4e0f93caee618d333e1aa86ff3a6a692994378b7e419319dd4b335dfa26da`.
The agent recomputed this from `git show e84ff5b:spec/oscillators/ADR-P09.md`.
This records the agent's mechanical check; it makes no claim that the human
independently recomputed the hash or numerical evidence.

## Accepted scope

- Six-state intracellular three-gate transcript/repressor model.
- Eighteen-state distributed model with one transcript/synthase NOT gate per
  strain, nine intracellular signal pools and three shared-medium total pools.
- Count-space equations, ring direction, catalytic translation/signal synthesis,
  read-only sensing and explicit population-weighted membrane flux balance.
- Seconds/litres, expected counts per representative cell versus medium totals,
  explicit sensor-density conversion and finite nonnegative parameter domains.
- Stable Hill evaluation, permitted signed linear intermediate stages,
  nonnegative nonlinear sensor densities, finite nonnegative returned samples
  and explicit failure without clipping or silent method substitution.

## Gates retained

Illustrative parameter sets and feasibility thresholds are not accepted golden
fixtures or native tolerances. Candidate studies remain observations. Complete
versioned wire formats, role bindings, normalized identity vectors, rejection
catalogs and independent reference definitions still require review and
acceptance before native implementation. The new math is ratified; neither
package currently supports native oscillator execution. No empirical biological
validation, SSA, growth/spatial behavior, native implementation acceptance,
release, merge or issue closure is recorded. Issue #84 remains open.

The mathematical body of the reviewed ADR and all candidate catalog, evaluator,
test, lock and report bytes are preserved. This follow-up adds governance/status
annotations and this decision record. Original PROPOSED wording in the immutable
reviewed snapshot and candidate studies retains its historical meaning.

Local checks for this documentation record: **PASS** raw reviewed-blob SHA-256,
unchanged mathematical body/candidate source bytes, repository checker, six
harness tests and `git diff --check`. Native oscillator execution remains
**NOT RUN — unsupported profile**; no approval is inferred from that status.
