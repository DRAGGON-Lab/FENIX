# EP-02 / #21 — P04 proposal evidence

**PROPOSED; human PI ratification and production implementation remain pending.**

Baseline: `38ae2e851e8833628e0eb71ac0d00faa8ecafa4f` (merged #61).
Date: 2026-11-16 UTC. This is a contract proposal and isolated numerical experiment.
No native executor, dependency manifest/lock, approved fixture, original receipt
or retained reference report changes. Python 3.12.13; uv 0.11.29;
isolated SciPy 1.18.1 and NumPy 2.5.5. All uv commands use
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Temporary dependencies remain outside
the library environment. The [proposal](../../spec/execution/proposals/ADR-P04.md)
and [read-only trial source](../../spec/execution/proposals/review_p04.py)
are review candidates, not a ratified scientific API.

## Executed numerical evidence

The [retained trial report](p04-scipy-trials.json) records every sample/error and
both method/configuration settings. There are 240 repeated comparisons of the
same approved 40 samples (two methods, three configurations), not 240 independent
scientific examples. Nominal and fine runs are required to satisfy the fixed
candidate bound; coarse results are observations. No threshold was loosened.

| Method | Configuration | Max absolute error (molecule) | Max fraction of acceptance bound | RHS calls |
|---|---|---|---|---|
| DOP853 | coarse | 3.81607e-09 | 0.078689 | 2684 |
| DOP853 | nominal | 6.34456e-10 | 0.00972179 | 4496 |
| DOP853 | fine | 1.71356e-11 | 0.000578354 | 8252 |
| Radau | coarse | 4.6578e-09 | 0.00735689 | 8223 |
| Radau | nominal | 4.78165e-10 | 0.000771575 | 14395 |
| Radau | fine | 1.25313e-11 | 5.40475e-05 | 25473 |

All six groups passed the candidate bound. Radau also passed the independently
evaluated stiff control with 3228 RHS calls. DOP853 deliberately
exhausted its 2000-call budget on the same stiff problem (expected failure
control). This exception exercises the exploratory counter, not a native error
API. Refinement changes tolerances and maximum step together; the improved
aggregate errors do not establish formal convergence order, monotonic per-sample
error or a certified universal error bound.

## Exact checks and outcomes

| Command (from repository root) | Outcome |
|---|---|
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --no-project --offline --python 3.12 --with scipy==1.18.1 --with numpy==2.5.5 python spec/execution/proposals/review_p04.py > docs/verification/p04-scipy-trials.json` | PASS; exit 0; 240 comparisons and stiff controls |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python conformance/production_decay/audit_rational.py` | PASS; exit 0; 40 exact rational publication checks |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v` | PASS; exit 0; 16 oracle/harness tests including negative cases |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; exit 0; 46 unchanged package tests |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; exit 0; 6 harness tests |

Proposal-specific lint, report replay and protected-file checks are recorded
below after final review. Initial `ruff check --fix` returned FAIL for eight
dict-constructor style findings. Replacing those constructors with literals and
formatting resolved them; the report was regenerated from the final source.

Fresh native adapter configuration/failure tests, installed executor wheel,
Julia ODE execution and #29 gate: **NOT RUN**, pending production implementation
and their independent gates. This trial does not confer biological validity.

## Artifact identity

| Artifact | SHA-256 |
|---|---|
| `spec/execution/proposals/review_p04.py` | `559cefebf03952df99ffba17476f4b7a3b68a5099a847fa96a46febb167f1f0f` |
| `conformance/production_decay/catalog.json` | `468c05a59fc23106dfc2e9e3454e9709ef0b61c9e130885180ecd4e67a07406d` |
| `docs/verification/p04-scipy-trials.json` | `3259cd134497618f96da8a89d670db5a2356027a1c435f90478af65886bda7a8` |

## Final checks and independent review

All commands here use the same UV_CACHE_DIR prefix above unless Julia/git/cmp.

| Exact command | Actual outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/local links |
| `uv run --project packages/python --locked --offline ruff check spec/execution/proposals/review_p04.py` | PASS |
| `uv run --project packages/python --locked --offline ruff format --check spec/execution/proposals/review_p04.py` | PASS; 1 file |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS; 3 methods, overlapping 207/84/9 controls |
| `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot JULIA_PKG_OFFLINE=true /private/tmp/julia-1.10.13/bin/julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 library smoke assertions, no ODE execution |
| `uv run --no-project --offline --python 3.12 --with scipy==1.18.1 --with numpy==2.5.5 python spec/execution/proposals/review_p04.py > /private/tmp/fenix-p04-replay.json` | PASS; repeated numerical checks |
| `cmp docs/verification/p04-scipy-trials.json /private/tmp/fenix-p04-replay.json` | FAIL; diagnostic byte comparison, 27 DOP853 sample-bit differences; byte identity is not required |
| `git diff --exit-code origin/main -- packages conformance docs/approved-decisions.md docs/verification/ep02-python-compiler.json docs/verification/rejections-python.json docs/verification/rejections-julia.json` | PASS; implementation, dependencies, fixtures and protected receipts/reports unchanged |
| `git diff --check` | PASS |

Both retained and replay reports have matching source/catalog hashes, 240 unique
(method, configuration, case, time_bits) identities and passing pointwise bounds.
Radau samples match; some DOP853 sample bits and error summaries differ between
processes on this host. No cause is established by this evidence. Do not infer
bitwise reproducibility even on this host from the recorded settings. The
proposed contract promises bounded numerical agreement, not exact replay bytes.
The table above describes the retained run, not identical maxima for every replay.

The independent engineering reviewer found no confirmed defect, separately ran
the 240-row experiment and a one-call budget failure, and verified protected
sources/fixtures and whitespace. This is agent review evidence, not PI approval.

The independent numerical reviewer found no blocking numerical/scientific
finding, reran the trials, reconstructed every retained error/bound fraction and
checked equations, units, binary64 inputs and Radau's Jacobian against P02.
Native configuration/errors, overflow/underflow boundary behavior and negative
output diagnostics remain NOT RUN; this proposal does not imply those production
paths exist. Human scientific ratification remains pending.


## Human PI ratification, 2026-11-16

The PI explicitly accepted ADR-P04 at reviewed revision `67820ae` on PR #62.
See the [decision and concerns](../../spec/execution/proposals/ADR-P04.md#human-pi-ratification-record).
All results and pending statuses above describe the original proposal execution;
this appendix does not rewrite those historical receipts. Approval consciously
accepts possible rejection of mathematically well-posed simulations due to tiny
negative sampled values. API documentation and future result manifests must
retain bounded-agreement language. Historical run #43853787258 is existing
infrastructure evidence, not native solver testing. Every requested native case
remains an implementation obligation. No trial/report/fixture bytes were changed.
