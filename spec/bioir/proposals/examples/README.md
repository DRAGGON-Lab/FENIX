# ADR-P01 proposal examples

These documents illustrate the proposed M0-compatible BioIR subset. They are **not
approved fixtures** and must not be used as normative expectations by either
native package. Read the [proposal](../ADR-P01.md) before reviewing them.

`design.json` describes one molecular species in a representative cell, with
constitutive production and first-order loss. `experiment.json` assigns fixed
rates and a zero initial count and references that exact candidate Design.
Execution requests are separate; the Experiment has no `profile` field. Removing
that field during proposal revision changes the illustrative Experiment digest;
the unchanged Design content and its digest remain the same. No approved
fixture or committed scientific revision is being migrated by this draft edit.

The narrow schema does not define BioIR's full representational scope. Later
versions must support nested systems through reviewed compatibility and migration
rules. Additional species are outside this subset, not globally invalid BioIR.

The digest covers scientific content only, not envelope metadata. It checks
integrity against a trusted reference and does not authenticate the author.
Metadata audit records and storage snapshot identities remain ADR-P07 work.

Their example digests were calculated with external Python `rfc8785` 0.1.4 and
`hashlib.sha256`, then cross-checked independently with ECMAScript primitive
serialization, UTF-16 key sorting and Node's SHA-256 implementation. This checks
the examples only; it does not validate general FENIX canonicalization or ratify
the proposed digest policy. No canonicalization golden vectors are published.

Before #12 can be completed, the human PI must ratify ADR-P01 and independent
native semantic validators must check revision integrity, references, units,
uniqueness and capability limits. The larger rejection suite remains #17 work.
