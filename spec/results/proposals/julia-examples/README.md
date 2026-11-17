# Proposed Julia/SciML examples — synthetic, not execution receipts

**PROPOSED; PI acceptance PENDING.** These four manifests reuse the matching
approved result files in [the P07 examples](../examples/README.md) by exact bytes;
no result, approved schema, fixture catalog or historical receipt is changed.

Both Tsit5 and Rodas5P configurations occur. Late sampling starts integration
at zero. Zero-only and empty-observable cases skip integration; multi-observable
columns retain normalized `a_amount, m_amount, z_amount` order despite source
order. Source references, FIR digests and analytical sample expectations are
inherited unchanged from the original bounded examples.

Version strings, counters and timestamps are synthetic choices and do not claim
an installed environment or solver execution. The zero-only manifest includes
`max_nfev` and `maxiters` above 64-bit Int: it exercises portable readback and
cannot be produced by #26's native Int configuration. Its grid retains `-0.0`.
All capture build IDs are null under the proposed current installed-metadata policy.

[checksums.json](checksums.json) freezes exact new manifest and referenced result
bytes, including final newlines. The transport-only numeric probes remain the
unchanged [P07 vectors](../examples/numeric-tokens.json). Independent Python and
Julia audits add midpoint-rounding probes and profile/numeric rejection controls.
They are bounded evidence, not general production readers, solver verification,
#29 conformance, or human acceptance.
