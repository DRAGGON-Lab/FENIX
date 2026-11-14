# EP-01 package tooling verification

Date: 2026-11-14. Base revision: `e14cc91235cf131754bb4fe4d2123823d5fe8ee0`.
Tooling source fingerprint: `a75db919da1ed0c3075a31fe7208bfc113165711ad84108356af3ec9cb079d65` (SHA-256 of sorted relative
path + NUL + file bytes + NUL for the tooling files, excluding this report and
the separate BioIR proposal). These changes were verified in a dirty feature
branch before committing; no scientific runtime implementation was changed.

Environment: macOS x86_64, uv 0.11.29, CPython 3.12.13, Julia 1.10.13.
Julia was downloaded to `/private/tmp/julia-1.10.13`; it was not installed globally.
The uv cache and Julia depot were under `/private/tmp`.

## Executed checks

All commands ran from the repository root. Prefix uv invocations with
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia invocations used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and the absolute Julia binary
above, with `--startup-file=no`. Exit status was 0 for each final check below.

| Check / exact command | Outcome |
|---|---|
| `uv sync --project packages/python --locked` | PASS, editable package plus locked development tools installed |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 2 tests |
| `uv build --project packages/python --offline` | PASS, sdist and wheel under `packages/python/dist/` |
| `uv venv --python 3.12 /private/tmp/fenix-wheel` | PASS, clean environment |
| `uv pip install --offline --python /private/tmp/fenix-wheel/bin/python --no-deps packages/python/dist/fenix_bio-0.0.0-py3-none-any.whl` | PASS, no development dependencies |
| `/private/tmp/fenix-wheel/bin/python -m unittest discover -s packages/python/tests -v` | PASS, 2 tests against installed wheel |
| `JULIA_PKG_OFFLINE=true julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS, 2 package tests |
| `julia --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'` | PASS, Pkg generated the committed reference manifest |
| `JULIA_PKG_OFFLINE=true julia --project=conformance/julia -e 'using JSON, JSONSchema, SHA, Test'` | PASS, reference tools load offline |
| `ruby -e 'require "yaml"; YAML.load_file(".github/workflows/scaffold-smoke.yml")'` | PASS, YAML syntax only |
| `git diff --check` | PASS |
| GitHub Actions execution | NOT RUN locally; requires a PR/workflow run |
| Mathematical conformance, native semantic validators | NOT RUN; contracts are not ratified |

Initial sandbox network attempts for uv and Julia failed DNS resolution;
explicitly approved retries succeeded. These initial failures do not count as
passes. Build output contained the pre-existing setuptools license-table
metadata deprecation warning; both distributions built successfully.

No scientific accuracy, cross-language compiler parity or biological validity
is established by these checks. The library packages remain independently
installable; their runtime dependency sets remain empty.
