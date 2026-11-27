# M1 proposed stage-domain investigation

Refs #31 / #34. Base: `bab8541c73ebc4d366e3bf5dd32f90aaa74fde68`
(refreshed main, 2026-11-27). This focused change implements the approved plan's
feasibility investigation and documented-proposal path. It does **not** complete
the full review packet, native M1 implementation or oscillator delivery.

Affected files: the new `conformance/community/feasibility/` probe, frozen
settings, tests, README and observed receipt; the existing community workflow
and navigation links; this verification record; the proposed P08 completion-scope
decision. Non-goals: native package/schema changes, fixture replacement, changed
mathematics/domain rules, accepted golden values, scientific approval, issue
closure, publication or merges. The existing oscillator audit checkout is
preserved; this work lives in an isolated worktree from refreshed main.

## Numerical evidence

The [retained receipt](../../conformance/community/feasibility/scipy-receipt.json)
contains full numerical samples, 160-digit reference values, error ratios,
settings and SHA-256 fingerprints of the exact probe, settings, source reference
files and dependency lock. It is observed investigative output, not approved
golden data. Reference laws and all ten original case definitions are unchanged.

Python 3.12.16 / NumPy 2.5.5 / SciPy 1.18.1 on macOS arm64:

- **PASS:** 40 integrations / 120 four-state sample comparisons, both methods at
  both settings, against independent Decimal laws.
- Maximum component error / proposed state bound: approximately `0.060573`.
- Maximum closed signal drift / derived population-weighted bound:
  approximately `6.12e-8`. Initial representation discrepancy is explicitly
  included, and happens to be zero for these integer initial states.
- **Observed domain failures:** all four long-tail controls reject a negative
  sensed internal stage despite a strictly positive exact extracellular count.

| Method | Setting | First failing stage time (s) | Extracellular stage count |
|---|---|---:|---:|
| DOP853 | baseline | 64.854986 | -8.7811e-13 |
| DOP853 | refined | 76.033931 | -5.9814e-15 |
| Radau | baseline | 55.196350 | -1.6293e-10 |
| Radau | refined | 61.636844 | -2.7987e-13 |

These are observed coordinates, not portable exact-time requirements. The
frozen control expects a domain failure under the pinned SciPy graph; regressions
do not require bit-identical stage times/counts across platforms. The receipt
and CI output preserve actual values. The positive-law witness is evaluated at
the actual first failing time. Failed attempts produce no success trajectory.

## Engineering verification

Commands use the workflow's locked/offline Python project. Locally available
uv is 0.13.10 and Python is 3.12.16; the CI job pins the documented uv 0.11.29
and Python 3.12.13. Local evidence is not mislabelled as that pinned CI run.

| Check | Result |
|---|---|
| `uv sync --project packages/python --locked` | PASS |
| `python -m unittest discover -s scripts/tests -v` | PASS — 6 tests |
| `python -m unittest discover -s packages/python/tests -v` | PASS — 88 tests |
| `python -m unittest discover -s conformance/community -v` | PASS — 8 existing reference tests |
| `python -m unittest discover -s conformance/community/feasibility -v` | PASS — 9 tests |
| `ruff check conformance/community/feasibility` | PASS |
| `python scripts/check_repo.py` | PASS — repository consistency, not science |
| Julia package / independent-reference / Tsit5 / Rodas5P execution | NOT RUN — Julia is unavailable locally |
| Native M1 / cross-language conformance / clean installed M1 examples | NOT RUN — executable contract/reference acceptance pending |
| New GitHub Actions job | NOT RUN locally — remote outcome remains separate |

The added CI job preserves the existing independent community reference job.
It runs the new tests and emits its own receipt. Its success means bounded
comparisons and predicted failure controls behave as recorded; it is not an M1
scientific acceptance status.

## Human gate

Review the [completion-scope proposal](../../spec/community/execution-feasibility-proposal.md).
The existing P08 domain rule is preserved. The PI must decide whether the
executable profile accepts explicit failures for valid long-tail requests or
requires a separately investigated completion guarantee. The remaining complete
wire/identity/rejection/reference/method packet must still be prepared and
accepted at an exact revision before #32/#33. No approval or issue closure is
inferred from this candidate PR or its checks.
