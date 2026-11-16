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
- `multi-observables.experiment.json` and `multi-observables.fir.json` are new
  hand-prepared **proposed** source/expected-model artifacts, separate from all
  approved fixtures. They declare `z_amount, a_amount, m_amount` in that order,
  each directly observing the existing one-state production/decay model. The
  matching result orders columns `a_amount, m_amount, z_amount` under unchanged
  P03 rules, with corresponding `x` mappings and `molecule` units. Its two state
  samples reuse the approved baseline oracle's roundings at 1 and 10 seconds;
  it introduces no new numerical expectation. Independent external serializers
  check the candidate source-content and normalized FIR digests.
- Each matching `*.manifest.json` is a **synthetic illustration**: counters,
  environment versions and timestamps were chosen to exercise the contract and
  do not assert that an execution occurred. The large zero-only work budget
  tests exact integer preservation. DOP853 and Radau options are represented;
  implementation testing must actually execute both methods later.
  Revised manifests use `backend.profile = python-scipy-ode/0.1.0` and core
  `producer` identification. The original three have null build IDs. The multi
  example's `candidate:p07-multi-observable-v1` is an explicitly synthetic build
  label, illustrating a non-null string; it does not identify an actual package
  build, source commit or execution.
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

The revised [ECMAScript audit](../review_p07_refinements.js), adapted from the
retained independently authored [initial audit](../review_p07.js), runs from the
repository root with `node spec/results/proposals/review_p07_refinements.js`.
It cross-checks all eleven candidate hashes, four result hashes/normalized FIR
identities and ordered observable mappings, the multi-source digest and eight
binary64 probes. It is a bounded reference check, not a general JSON decoder,
integer-field validator or native FENIX normalizer. In particular, JavaScript's
ordinary JSON.parse is not used to establish exact large manifest integers.

The original audit/checksum receipts remain unchanged as historical evidence
for revision `908997e`. Use the new
[refinement record](../../../../docs/verification/ep02-p07-refinements.md) and
its separate receipts for the revised schemas/examples.
