# ADR-P01 proposal examples

These documents illustrate the proposed BioIR wire format. They are **not
approved fixtures** and must not be used as normative expectations by either
native package. Read the [proposal](../ADR-P01.md) before reviewing them.

`design.json` describes one molecular species in a representative cell, with
constitutive production and first-order loss. `experiment.json` assigns fixed
rates and a zero initial count and references that exact candidate Design.

Their example digests were calculated with external Python `rfc8785` 0.1.4 and
`hashlib.sha256`, then cross-checked independently with ECMAScript primitive
serialization, UTF-16 key sorting and Node's SHA-256 implementation. This checks
the examples only; it does not validate general FENIX canonicalization or ratify
the proposed digest policy. No canonicalization golden vectors are published.

Before #12 can be completed, the human PI must ratify ADR-P01 and independent
native semantic validators must check revision integrity, references, units,
uniqueness and capability limits. The larger rejection suite remains #17 work.
