# Generated M0 interaction checks (#59)

This development-only suite investigates combinations left outside the fixed
P01/P02/P03 catalogs. It exercises the delivered native Python parser, committed
sources and compiler; it does not introduce scientific semantics, execute an ODE,
approve fixtures or supply M1/SSA/release acceptance. Existing independent fixed
references and Python/Julia/Node checks remain required.

The generator uses Python's standard library, the installed FENIX package and
Node 24. No testing framework or package dependency is added. The
[CI workflow](../../.github/workflows/generated-m0.yml) runs two fixed seeds,
256 scenarios each, the replay controls, approved native document/FIR tests and
independent serializer checks. Runtime packages remain independent of Node.

## What is checked

Expectations follow ratified [P01](../../spec/bioir/proposals/ADR-P01.md),
[P02](../../spec/fir/proposals/ADR-P02.md) and
[P03](../../spec/canonicalization/proposals/ADR-P03.md), with the unchanged
approved rejection/source fixtures and normalized `fir-base` reference as seeds.
The runner verifies their catalog-recorded file hashes before using them.
Expected model structure is copied from the independent reference and changed
only at the generated rate, initial-count and named-observable locations; no
native compiler output supplies the expected model.

The existing independent ECMAScript RFC 8785 serializer computes expected source
bytes, digests and FIR identity bytes. It shares neither Python's native parser
nor its rfc8785 serializer. Approved fixed P01 and RFC/P03 vectors continue to
check this serializer; agreement alone is not biological validation. These are
bounded generated expectations, not new approved golden fixtures.

| Example / use case | Required behavior |
| --- | --- |
| Different member order, whitespace, escaped Unicode and author metadata | Exact content identity persists; composed/decomposed metadata text is preserved. |
| Swapped declaration arrays, misleading renamed parameters/functions, explicit revisions | BioIR content identity changes; role-resolved FIR mathematics stays identical. |
| Zero, negative zero, fractional rates, subnormal, maximum finite, large integral floats, four cell volumes | Represented bits survive transport/compilation; counts are never rescaled by M0 volume. |
| Decimal/exponent aliases for one, extreme-exponent exact zero | Accepted input spelling does not alter canonical represented mathematics. |
| Bare out-of-range integer in BioIR vs integer rounding in FIR | P01 rejects before rounding; P03 accepts the represented binary64 value. |
| Changed source with a recomputed digest and unchanged revision | Self-consistency alone accepts; trusted predecessor/digest checks reject it. |
| Exact Design among stale candidates; missing Design or wrong revision/digest | Resolve the exact reference only; check declared diagnostic category and path. |
| Stale Experiment envelope and missing Design | Reject the envelope digest before source lookup. |
| Six FIR declaration collections permuted separately/together | Canonical bytes persist, normalization is idempotent, canonical readback succeeds. One-state/equation reversals are necessarily no-ops in M0. |
| Reversed expression operands | Reject the unsupported template; never infer algebraic equivalence. |
| Stale provenance, mismapped state, swapped function role, wrong source value or invented observable | Standalone mathematical validity never substitutes for exact producer/source checks. |
| Changed rates or named observable interface | Scientific identity changes; bytes remain checked against independent expectations. |
| Invalid numeric tokens, Boolean/negative quantities, escaped duplicate keys, malformed UTF-8 and lone surrogates | Reject with the specified category and JSON Pointer while retaining the other generated features. |

Every seed begins with coverage of all 15 numeric atoms in each quantity role;
further cases choose numeric triples independently. A seeded eight-bit mask
combines declaration reversals, transport formatting and source renaming. The
report records every scenario, three identities, runtime versions, native/tool
source hashes and reference-catalog hashes. Coverage is finite; correlations and
unexplored inputs remain. These checks do not establish solver behavior,
exhaustive validation, global revision history or authenticated execution.

## Run, inspect and replay

From the repository root, install the locked environment following the
[development workflow](../../docs/DEVELOPMENT_WORKFLOW.md). Output directories
must be new; paths inside the checkout must resolve under `artifacts/`.

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/generated_m0 -v
uv run --project packages/python --locked --offline python conformance/generated_m0/run.py --seed 5901 --cases 256 --save-examples --output-dir artifacts/generated-m0-5901
uv run --project packages/python --locked --offline python conformance/generated_m0/run.py --seed 5902 --cases 256 --output-dir artifacts/generated-m0-5902
```

Inspect `report.json` for individual scenarios and input/model identities.
`--save-examples` also saves the first 15 passing source/FIR examples under
`examples/case-NNNN/`: committed `design.json` and `experiment.json`, observed
`fir.json` and independently specified `expected-model.json`. These include all
numeric atoms in each role, and can be loaded through the public native APIs to
inspect exact source references and compare the model with its expectation.

A failing property exits nonzero and additionally saves `failure.json`, minimized
`design.json`, `experiment.json`, and `expected-model.json`. Negative-check
failures retain their exact raw witness (hex for malformed bytes) in `failure.json`. All generated artifacts
are observations for investigation; the runner never rewrites fixed fixtures.

```sh
uv run --project packages/python --locked --offline python conformance/generated_m0/run.py --replay artifacts/generated-m0-5901/failure.json --output-dir artifacts/generated-m0-replay
```

The reducer resets scenario coordinates and removes individual mask bits only
when the **same named property** still fails. The result is locally minimal under
those moves, not a claim of globally minimal JSON. Replay uses the recorded
coordinates directly; it does not rely on a later generator producing the same
random stream. Compare recorded source hashes when replaying across revisions.
Unexpected native diagnostics/exceptions are also captured for investigation.
The control tests inject a compiler regression, verify capture and reduction,
reproduce its failure, then remove the regression and require that exact replay
to pass. A separate injected source-map corruption must also be detected.

Passing these checks strengthens the evidence for #19/#20 while preserving their
bounded acceptance and the existing fixed catalogs. It neither reverses previous
acceptance nor completes later milestone gates.
