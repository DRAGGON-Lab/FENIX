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
The human PI accepted all 92 registered [P01 reference expectations](../../conformance/bioir/README.md),
including outcomes, canonical serialization, binary64 bit patterns and declared
diagnostics. Native FENIX implementations, exhaustive validation, compiler or
solver correctness and future BioIR semantics remain outside that decision.
See the [acceptance record](../../docs/verification/ep01-p01-reference.md#human-pi-acceptance-recorded).
The [M0 FIR contract](../fir/README.md) is ratified under ADR-P02; the
[FIR canonicalization contract](../canonicalization/README.md) is ratified under
ADR-P03; its bounded [reference vectors](../../conformance/canonicalization/README.md)
have separate human PI acceptance.
