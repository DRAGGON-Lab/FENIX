# Proposed P10 source/FIR/zero-grid candidates

These twelve literal JSON artifacts make
[ADR-P10](../ADR-P10.md) reviewable for
[issue #84](https://github.com/DRAGGON-Lab/FENIX/issues/84). They are **PROPOSED**,
not accepted golden fixtures, native package output or execution receipts.
They use the exact reviewed P09 primary case inputs, pinned by complete raw
catalog SHA-256 in the candidate writer. Accepted mathematical/numerical reference
definitions do not ratify these new serialization/binding choices.

Each `single-cell/` and `three-strain/` directory contains:

- `design.json`: explicit source owners, species/ports, gate/sensor bindings,
  parameter units/bases, and community synthesis/loss/transport functions.
- `experiment.json`: separate exact Design reference, complete parameter/count/
  population assignments and direct observables.
- `fir.json`: resolved six/18-state count model, all 21/54 parameters and 15/48
  reactions, ordered equation ASTs, population coefficients and source maps.
- `zero-grid.result.json`: synthetic zero-time initial-state/observable copies
  with explicit canonical state IDs, owners, scopes and units.
- `zero-grid.python.manifest.json` and `zero-grid.julia.manifest.json`:
  illustrative new backend profiles and result-byte checksums. Producer and
  environment strings explicitly state that they are unobserved/not executed.

Intracellular and extracellular signal IDs are source-scoped; each strain and
the medium reuse local signal names. Compilation must resolve full endpoint
tuples and canonical roles rather than display names or positions. The community
FIR/result uses a/e/m/p canonical order, while P09 study vectors use m/p/a/e.
The explicit source-role/initial-count mapping avoids silently swapping pools.
Observables include synthases/repressors and community intracellular/medium
signals, exposing different scopes even though all sample units are molecules.

## Review and reproduce offline

Use the existing locked Python development environment, without adding runtime
dependencies or importing native FENIX:

```sh
uv run --project packages/python --locked --offline python spec/oscillators/candidate_schemas.py --check
uv run --project packages/python --locked --offline python spec/oscillators/candidate_examples.py --check
uv run --project packages/python --locked --offline python -m unittest discover -s spec/oscillators -p 'test_wire*.py' -v
uv run --project packages/python --locked --offline python spec/oscillators/review_candidates.py --output /tmp/p10-wire-audit.json
```

The output file must be new. Candidate writers also support `--output-dir` to a
**new** directory for review; they refuse an existing directory. They do not
overwrite checked-in candidates or accepted scientific fixtures. `--check` is
read-only reproduction, not an independent oracle. All construction helpers are
proposal tooling under `spec/`; none is a native compiler or public API.

The standalone Draft-07 [schemas](../schemas/README.md) have no external `$ref`
resolution or network requirement. Finite reaction/equation enums represent the
exact proposed ASTs, with no dynamically executable callbacks or general
expression evaluator. The candidate builders share `wire_shapes.py`; agreement
between their schemas/examples is consequently **not independent mathematical
evidence**. A schema/fixture generator cannot approve its own expected output.

The read-only audit consumes literal examples without importing the builders.
It checks source content-JCS digests, exact Design/FIR source references,
endpoint and parameter roles, transport directions/signals, geometry/populations,
source-map/value/initial/observable correspondence, normalized example order,
candidate FIR wrapper hashes, and zero-grid result/manifest consistency. It
uses the same external Python `rfc8785` serializer as existing Python tooling;
its hash agreement is not an independent JCS implementation check.

The CI context `Candidate P10 wire structure (not native conformance)` runs
reproduction, structural/binding controls and the audit. Its receipt fingerprints
all four schemas, twelve literal artifacts and review scripts. Existing package,
mathematical, reference, installation and numerical jobs remain enabled.

## Evidence boundaries and remaining gates

Tests include wrong owner/scope/order, catalytic sinks, population signs/weights,
operand/AST changes, missing roles/functions, old backend profiles/constant
Jacobians, and wrong source bindings after recomputing digests/checksums. Those
controls demonstrate bounded detection, not exhaustive conformance.

JSON Schema cannot enforce raw numeric-token spelling, binary64 rounding,
duplicate raw keys or Unicode decoding, trusted predecessor history, bit-level
transport correspondence or all numerical/producer requirements. Tests expressly
show that structural validation accepts population token `100.0` and counter
token `0.0`, which the proposed raw-token rules reject. The bounded audit is
not a general raw parser or portable RunRecord loader.

Still required before native implementation: complete literal raw/binding/
identity/rejection catalogs with expected categories/paths; independent
Python–Julia/ECMAScript canonical byte/vector checks; independent validation of
the proposed AST equations/source-to-reference mapping; positive-time numerical
result examples; agreed native accuracy/oscillation/balance criteria; and human
PI ratification/fixture acceptance at exact reviewed revisions. Native oscillator
execution remains **NOT RUN — unsupported profile**. No release or issue closure
follows from passing this candidate audit.
