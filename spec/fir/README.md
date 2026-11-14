# FIR mathematical schema — M0 subset ratified

[ADR-P02](proposals/ADR-P02.md) and its [structural schema](proposals/fir-m0.schema.json),
version `0.1.0`, were ratified by the human PI on 2026-11-14 at reviewed revision
`86450affca4470d7540d04f04bdc6d3d07e1a60d`. The drafting-era paths and schema
identifier remain unchanged for stable references; the ADR's ratification record
determines their status.

The M0 contract defines abstract count-space mathematics, named observable
identity, exact reaction/equation agreement, source state/parameter mappings,
and compiler/source parameter, initial-count and observable correspondence.
Provenance and display labels do not enter FIR identity. ODE validity alone
never implies SSA support.

The [examples](proposals/examples/README.md) remain illustrative, not approved
golden fixtures. Independent fixture/rejection review, native semantic validation
and implementation approval remain outstanding. P01 fixture/implementation
acceptance is separate; P03 must ratify FIR normalization, bytes and hashes.
No native FIR compiler or solver is implemented by this ratification.
