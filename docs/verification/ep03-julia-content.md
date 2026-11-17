# EP-03 / #23 — native Julia M0 content

Implemented uncommitted native authoring under ratified ADR-P01 and the approved
P01/rejection reference catalogs. Keyword-only validating constructors, typed
immutable vector/tuple snapshots, structured categories and paths, fresh exports
and ordinary JSON are available independently of Python. JSON.jl is the only
runtime package dependency. Names/version remain provisional pending P06.

Committed envelopes, raw parsing, canonical bytes/digests, trusted revisions and
exact Design digest correspondence are #24. A syntactically valid reference digest
can be incorrect in uncommitted content; no committed validity is claimed. FIR,
solvers and biological predictive validity remain outside this delivery.

## Executed checks

Environment: Julia 1.10.13, JSON 1.13.4, JSONSchema 1.6.0, uv 0.11.29,
CPython 3.12.13. Julia used `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`
and `JULIA_PKG_OFFLINE=true`; uv used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`.
Commands ran from the issue worktree based on main `b7850cb`.

| Command | Result |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 88 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS, 29 projections |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS, 402 assertions |
| `julia --project=conformance/julia packages/julia/test_native_content/runtests.jl` | PASS, 29 projections and local package identity check |
| Copied package direct native tests with `PATH=/nonexistent` | PASS, 402 assertions; both Python executable lookups absent |
| `git diff --exit-code -- spec/bioir spec/fir spec/canonicalization conformance packages/python` | PASS, protected sources unchanged |
| `git diff --check` | PASS |

The runtime executable was `/private/tmp/julia-1.10.13/bin/julia`. Standalone
validation copied the package, including its ignored generated manifest, to
`/private/tmp/fenix23-standalone`, then used that project to load Fenix and execute
its tests without repository fixtures. It asserted that neither `python` nor
`python3` was on PATH. This is bounded installation/independence evidence.

The registry accounts for 29 projected cases (6 accepts, 23 rejects) and 63
explicitly deferred P01 cases. Original input checksums, categories and detailed
paths remain authoritative. The structural adapter supplies no semantic rules.
No initial red run was captured because implementation arrived before tests ran.

Separate agents reviewed core scientific constraints and test/adapter engineering
boundaries and independently ran focused tests. No confirmed defects remained.
Review strengthened source-loading identity and invalid native string handling.
These reviews do not supply human scientific or implementation acceptance.
Hosted CI and human review remain separate. No issue/epic closure or merge is
performed by this delivery. Full raw/document/FIR/solver conformance is NOT RUN.
