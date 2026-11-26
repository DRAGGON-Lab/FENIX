# Language-neutral scientific specifications

The [M0-compatible BioIR subset](bioir/README.md), version `0.1.0`, is ratified
under ADR-P01. The [M0 mathematical FIR/capability subset](fir/README.md) is
ratified under ADR-P02. The [FIR canonicalization contract](canonicalization/README.md)
is ratified under ADR-P03. Independent P01 reference validators and the
[approved 92-case catalog](../conformance/bioir/README.md) provide bounded
reference expectations. Native implementations, exhaustive validation, compiler
correctness, solver correctness and future BioIR semantics are not approved by
that reference acceptance. Both native packages now implement the bounded M0 document, FIR compiler,
ODE execution and P07 results path. The native FIR/ODE scientific gates and
bounded M0 repository alpha have their own accepted evidence; see the
[current architecture](../ARCHITECTURE.md) and
[decision register](../docs/approved-decisions.md). The earlier
[EP-02 audit](../docs/verification/ep02-status-governance.md) retains its historical
observations rather than defining the current implementation state.

New or changed normative rules require human PI approval. Independent references
and reviewed positive/negative fixtures remain mandatory. In particular,
parser/validator implementation approval requires the
[language-neutral fixture catalog and independent Python/Julia reports](../conformance/README.md#parser-and-validator-fixture-catalog-gate).
Ratifying P01, P02 or P03 does not approve golden fixtures or waive those follow-on gates.

The [issue #17 rejection references](../conformance/rejections/README.md) exercise
P01 raw input, P02 mathematical/source checks and P03 numeric input policy with
independent Python/Julia reports. The human PI accepted the bounded suite; its
catalog is APPROVED. Negative capability fixtures are not exhaustive. The ratified
schemas and accepted canonicalization artifacts are unchanged; package
implementation approval remains separate. See the
[acceptance record](../docs/verification/ep01-rejections.md#human-pi-acceptance-recorded).

The [P04 M0 ODE execution contract](execution/README.md) is **RATIFIED** by the
human PI on 2026-11-16 at reviewed revision `67820ae`. It establishes sampling,
accuracy and failure policies; native solver implementation approval is separate.

The [P07 M0 result/manifest contract](results/README.md) is **RATIFIED** for #22
at reviewed revision `bc662d3`, including its revised schemas and bounded
candidate reference expectations. Native implementation approval remains
separate; see the [ratification record](../docs/verification/ep02-p07-ratification.md).

The [M1 community contract](community/ADR-P08.md) has PI approval at reviewed
revision `186cfb3` for #31. Its further independent reference, complete wire-format
and numerical-evidence gates remain applicable before native M1 implementation.

The [repressilator benchmark contract](oscillators/ADR-P09.md) for #84 has bounded
PI ratification at reviewed revision `e84ff5b`: equations, units/bases and
numerical-domain policy for one six-state intracellular oscillator and one
18-state oscillator assembled from one NOT gate per strain with explicit signal
exchange. Candidate parameters/thresholds, independent references, complete wire
formats and native implementation remain separate gates; see the
[ratification record](../docs/verification/p09-math-ratification.md).

The [P10 oscillator wire design](oscillators/ADR-P10.md) is **PROPOSED** for #84.
It makes version, role-binding, FIR identity and multi-state result choices
reviewable without changing existing contracts or native capabilities. Its
[review plan](oscillators/wire-review-plan.md) is not a frozen fixture catalog;
complete schemas, independent identity/rejection evidence and PI ratification
remain required before native implementation.
