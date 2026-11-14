# Candidate production–decay mathematical oracle

**Status: REVIEW_REQUIRED.** Issue [#15](https://github.com/DRAGGON-Lab/FENIX/issues/15).
The [derivation and error budget](../../docs/scientific-evidence/production-decay.md)
follow ratified [ADR-P02](../../spec/fir/proposals/ADR-P02.md). The human PI must
accept the concrete numerical fixtures separately; P04 solver thresholds remain
unratified. This directory adds no native modeling API, solver or FIR extension.

## Fixed candidate catalog

[catalog.json](catalog.json) follows [catalog.schema.json](catalog.schema.json).
The root contract and units apply to every case and sample. Case IDs are stable;
each has a rationale. A sample is identified by `(case ID, time_bits)`. Duplicate
IDs and numerically duplicate times within a case are rejected. Only finite
nonnegative parameters and times are admitted, including signed binary64 zero.

| Case ID | `(alpha, beta, x0)` | Times in seconds |
|---|---|---|
| `baseline-zero` | `(10, 0.1, 0)` | `0, 1, 10, 100` |
| `baseline-five` | `(10, 0.1, 5)` | `0, 1, 10, 100` |
| `decreasing` | `(2, 0.5, 8)` | `0, 1, 2, 20` |
| `equilibrium` | `(2, 0.5, 4)` | `0, 1, 2, 20` |
| `fractional-decay` | `(0, 0.5, 0.5)` | `0, 1, 2, 20` |
| `zero-solution` | `(0, 0.5, 0)` | `0, 1, 2, 20` |
| `linear-production` | `(2, 0, 0.5)` | `0, 0.5, 1, 10` |
| `constant` | `(0, 0, 0.5)` | `0, 0.5, 1, 10` |
| `small-decay-20` | `(2, 2^-20, 0.5)` | `0, 0.5, 1, 10` |
| `small-decay-40` | `(2, 2^-40, 0.5)` | `0, 0.5, 1, 10` |

Parameters and times use exactly 16 lowercase hexadecimal digits for IEEE 754
binary64 bits, most significant byte first. Decode these bits before lifting to
multiprecision. The table's `0.1` denotes bits `3fb999999999999a`, not a decimal-real
constant. Nonzero expectations use one leading digit, 49 fractional digits, `E`
and a signed decimal exponent, rounded half-even to 50 significant digits.
Zero is explicitly `"0"`. These are reference-artifact encodings, not FIR syntax.
Coverage is bounded to this case matrix; no guarantee covers every finite input.

Expectations were prepared using an exact rational Taylor sum outside the two
shipped evaluators and all FENIX packages. They are fixed review candidates;
neither evaluator rewrites them and no regeneration command is shipped.

## Execute independently

Use the existing locked environments; no new dependencies are needed. From root:

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v
uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --report artifacts/production-decay-python.json
julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=conformance/julia conformance/production_decay/tests/test_oracle.jl
JULIA_PKG_OFFLINE=true julia --project=conformance/julia conformance/production_decay/review_oracle.jl --report artifacts/production-decay-julia.json
uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --compare artifacts/production-decay-python.json artifacts/production-decay-julia.json
```

The Python CLI uses only the standard library; its tests also validate the catalog
with the already locked `jsonschema`. Julia uses its locked reference environment.
Neither evaluator imports a FENIX package or invokes the other language. Each
checks its computations against fixed expectations before writing a report.
Python uses `Decimal` with 100/200 decimal digits and the integrating-factor
expression; Julia uses `BigFloat` with 512/1024 bits and `expm1`.

Reports contain decimal-string values for every computation, precision and its
unit, implementation/runtime/library identity, SHA-256 of exact catalog bytes,
and evaluator-source SHA-256. Checksums identify artifacts; they do not authenticate
who executed them. Row order is immaterial. Report decimal strings are nonnegative
finite decimal notation (optional fractional part and exponent), at most 4096
characters, with at most four exponent digits. Reports are separate artifacts;
`--report` may not overwrite either evaluator, the catalog or its schema.

The comparator requires the current catalog/source checksums, distinct Python
and Julia identities, and complete unique sample coverage at both prescribed
precisions. Each of the four computations must independently round half-even to
the fixed 50-digit expectation, and all four must agree after half-even rounding
to 70 significant digits. Stale/duplicate/missing/altered rows and missing
precision runs fail. Precision agreement is observed stability, not a certified
interval enclosure or fixture approval.

The existing Python and Julia CI jobs run tests and upload separate reports.
`Candidate production-decay reference agreement` downloads both and compares
them. The [verification record](../../docs/verification/ep01-production-decay-oracle.md)
contains locally executed reports, provenance, residuals and remaining gates.
