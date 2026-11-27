# Proposed M1 literal wire catalog

**PROPOSED; not approved fixtures or native implementation evidence.**
Refs #31 and #34. The [executable profile proposal](../executable-profile-proposal.md)
defines the exact review scope and remaining PI gate. The catalog contains 13
positive source/FIR/result packets, 56 single-defect rejection witnesses and 17
raw-number/Unicode/JSON parser projections. Each rejection declares its category
and JSON Pointer. Raw projections isolate lexical policy, not full document
acceptance. No precedence among simultaneously invalid documents is specified.

Ten packets map the unchanged independent analytical cases to canonical state
IDs. Three controls cover consistent source renaming, source/FIR declaration
permutation and empty observables. Each positive folder retains literal Design,
Experiment, FIR, normalized model, exact model/identity JCS bytes, SHA-256 digest,
zero/positive-time analytical result and illustrative Python/Julia manifest.
The analytical matrices are direct binary64 roundings of 160-digit Decimal laws.
They are independently compared by state ID, never by an unlabeled column order.
Manifest producer/environment/work fields explicitly identify these as
illustrations: they do **not** claim that a native backend ran. Internal
consistency, numerical comparison and execution authentication are separate.

Rejected result witnesses include a separately serialized manifest with a
matching checksum so each scope/owner/observable defect reaches its intended
check. Checksum failure has its own literal witness. Tests never repair a
rejected document before validation. Source digest failures are distinguished
from correctly recomputed but stale/mismatched cross-document bindings.

The writers are review conveniences and refuse to regenerate a catalog whose
status is no longer PROPOSED. They are not independent certification and must
not be used to replace accepted expectations. Existing M0/community reference
artifacts and the accepted completion-scope receipt remain unchanged.

Audit without calling any writer or native package:

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s spec/community -v
uv run --project packages/python --locked --offline python spec/community/review_wire.py --report artifacts/m1-wire-review.json
node spec/community/identity_audit.cjs
```

The Python auditor revalidates exact source maps, finite templates, scoped
transport and expected normalized objects/bytes/digests. The independent
ECMAScript auditor derives normalized models directly from the original FIR,
then uses ECMAScript binary64 number formatting and UTF-16 key ordering to
check source/model/identity bytes. Scalar serialization controls cover signed
zero, subnormal and decimal/exponential cutovers. Schema success and agreement
between these tools do not supply scientific approval or exhaustive validation.

Coverage tests additionally differentiate all rate/count/volume/population
identities, verify fresh/idempotent normalization, check reaction/equation ASTs
against independent Decimal balance laws at all 30 reference times and
asymmetric open-system/threshold probes, and reject malformed UTF-8/UTF-16.
Future generated-input campaigns and native immutable-buffer/solve-once/
offline-readback checks remain implementation/integration work.
