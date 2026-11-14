# Language-neutral scientific specifications

The [M0-compatible BioIR subset](bioir/README.md), version `0.1.0`, is ratified
under ADR-P01. The [M0 mathematical FIR/capability subset](fir/README.md) is
ratified under ADR-P02. The [FIR canonicalization contract](canonicalization/README.md)
is ratified under ADR-P03. Independent P01 reference validators and a
[candidate catalog](../conformance/bioir/README.md) are available for review;
native compilers and modeling-package validators are not implemented.

New or changed normative rules require human PI approval. Independent references
and reviewed positive/negative fixtures remain mandatory. In particular,
parser/validator implementation approval requires the
[language-neutral fixture catalog and independent Python/Julia reports](../conformance/README.md#parser-and-validator-fixture-catalog-gate).
Ratifying P01, P02 or P03 does not approve golden fixtures or waive those follow-on gates.

The [issue #17 rejection references](../conformance/rejections/README.md) exercise
P01 raw input, P02 mathematical/source checks and P03 numeric input policy with
independent Python/Julia reports. Expectations remain REVIEW_REQUIRED; the ratified
schemas and accepted canonicalization artifacts are unchanged.
