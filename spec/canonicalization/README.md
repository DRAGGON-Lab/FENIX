# Canonicalization — ADR-P03 ratified, reference vectors approved

The [ADR-P03 contract](proposals/ADR-P03.md) defines M0 FIR pre-normalization,
RFC 8785/JCS exact bytes and a versioned SHA-256 identity preimage. The human PI
ratified P03 on 2026-11-14 at reviewed revision `fdee54e5ebc5226c0a83810872311cc8cbbec3fd`.
The drafting-era ADR path and contract bytes remain unchanged.

The [catalog and independent serialization checks](../../conformance/canonicalization/README.md)
are now **APPROVED** following human PI acceptance of issue #16 on PR #55 at
reviewed revision `a58ea8345f0e2f641ba152b065ee3fa6d9dc0625`. See the
[acceptance record](../../docs/verification/ep01-canonicalization-vectors.md#human-pi-acceptance-recorded)
for the decision and exact artifact identity. The catalog maps all nine issue
requirements to executable IDs and auditable Python/ECMAScript byte reports.

FIR identity checks serialize supplied expected normalized objects. Native FIR
normalization, semantic validation, idempotence and end-to-end round trips remain
NOT RUN, as do all 17 contract_only outcomes. Native parser/normalizer/compiler
implementation approval remains separate; P01 BioIR hashing is unchanged.
