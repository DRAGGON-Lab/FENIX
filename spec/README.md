# Language-neutral scientific specifications

The [M0-compatible BioIR subset](bioir/README.md), version `0.1.0`, is ratified
under ADR-P01. FIR/capability and FIR-specific canonicalization contracts remain
pending ADR-P02 and ADR-P03. Independent P01 reference validators and a
[candidate catalog](../conformance/bioir/README.md) are available for review;
native compilers and modeling-package validators are not implemented.

New or changed normative rules require human PI approval. Independent references
and reviewed positive/negative fixtures remain mandatory. In particular,
parser/validator implementation approval requires the
[language-neutral fixture catalog and independent Python/Julia reports](../conformance/README.md#parser-and-validator-fixture-catalog-gate).
Ratifying P01 does not approve golden fixtures or waive those follow-on gates.
