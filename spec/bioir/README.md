# BioIR Design and Experiment — M0-compatible subset ratified

[ADR-P01](proposals/ADR-P01.md) ratifies the M0-compatible BioIR subset `0.1.0`
and its [JSON Schema](proposals/bioir-m0.schema.json), approved by the human PI
on 2026-11-14. The drafting-era paths and schema identifier remain unchanged for
stable references; the ADR's ratification record determines their status.

This subset is an initial milestone; BioIR's architectural scope includes nested
biological systems beyond current execution support. The ADR requires a
versioned extension and migration strategy without rewriting existing identities.

The paired documents remain illustrative examples, not approved golden fixtures.
Parser/validator implementation approval requires the reviewed
[language-neutral fixture catalog and independent native reports](../../conformance/README.md#parser-and-validator-fixture-catalog-gate).
A [P01-only review candidate](../../conformance/bioir/README.md) now exercises
raw parsing, structure, reference integrity, units, revisions and content digests
independently in Python and Julia. Passing it does not self-approve its fixtures.
FIR and FIR-specific canonicalization contracts remain pending ADR-P02/P03.
