# Proposed P07 examples — not execution receipts

**PROPOSED; reference acceptance and human-PI ratification are pending.**
All JSON files include their final newline in their checksum. Results were
written by hand, without `fenix`, NumPy, SciPy or a production serializer.

- `late-first.result.json` uses the approved `baseline-zero` analytical oracle's
  samples at 1, 10 and 100 seconds, manually entered as round-trip binary64
  decimal spellings. It starts from the baseline Experiment at zero even though
  its first requested sample is later. It is a candidate transport/reference
  example, not observed output from either method.
- `zero-only.result.json` uses that same source pair and the exact initial count.
  Its negative-zero time tests bit-preserving grid transport. The returned state
  is positive zero; P03 does not create a distinct model for zero's sign.
- `empty-observables.result.json` uses the existing no-observables Experiment
  and the same zero initial count. Empty rows remain aligned to the one time.
- Each matching `*.manifest.json` is a **synthetic illustration**: counters,
  environment versions and timestamps were chosen to exercise the contract and
  do not assert that an execution occurred. The large zero-only work budget
  tests exact integer preservation. DOP853 and Radau options are represented;
  implementation testing must actually execute both methods later.
- `numeric-tokens.json` is **transport-only**, not a result or manifest. Its
  explicit binary64 words describe signed zero, finite boundary values and
  different decoding of a large integer in sample versus counter fields.
  It does not claim all such values occur in one valid M0 trajectory.

Sources are the existing [baseline Design](../../../bioir/proposals/examples/design.json),
[baseline Experiment](../../../bioir/proposals/examples/experiment.json) and
[no-observables Experiment](../../../fir/proposals/examples/sources/no-observables-experiment.json).
The named-result FIR digest is the approved P03 `fir-base` identity preimage's
SHA-256; the empty-observable digest is independently serialized from the existing
P02 no-observables example using external RFC 8785, outside native FENIX code.
This adds no new mathematical rule or numerical golden oracle.

[checksums.json](checksums.json) freezes candidate artifact byte identities.
[review_p07.py](../review_p07.py) checks them without writing files, validates
schema structures and selected rejection mutations, compares samples to the
approved analytical decimals, and checks IEEE binary64 nearest/ties-even rounding
with exact rational arithmetic. Python hashlib and the independent system
`shasum -a 256` audit the same bytes. These are bounded contract-evidence checks;
they are not native parser/source resolver/executor validation.

The independently authored [ECMAScript audit](../review_p07.js), run from the
repository root with `node spec/results/proposals/review_p07.js`, cross-checks
all seven candidate hashes, all three result hashes/normalized FIR identities
and all eight binary64 probes. It is a bounded reference check, not a general
JSON decoder, integer-field validator or native FENIX normalizer.
