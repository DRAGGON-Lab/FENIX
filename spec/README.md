# Language-neutral scientific specifications

The [M0-compatible BioIR subset](bioir/README.md), version `0.1.0`, is ratified
under ADR-P01. The [M0 mathematical FIR/capability subset](fir/README.md) is
ratified under ADR-P02. The [FIR canonicalization contract](canonicalization/README.md)
is ratified under ADR-P03. Independent P01 reference validators and the
[approved 92-case catalog](../conformance/bioir/README.md) provide bounded
reference expectations. Native implementations, exhaustive validation, compiler
correctness, solver correctness and future BioIR semantics are not approved by
that reference acceptance. Native Python document validation, FIR compilation,
ODE execution and P07 results are now implemented on main; Julia remains a
scaffold. Independent native cross-language conformance and final scientific/
release acceptance remain separate; see the
[current audit](../docs/verification/ep02-status-governance.md).

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
