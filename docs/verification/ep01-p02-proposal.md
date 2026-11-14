# ADR-P02 proposal review evidence

Date: 2026-11-14. Base revision: `d8379f7f32582b4c7a2ced678160041ce8e31ee0` (merged P01 PR #50).
Source was checked in a dirty issue #13 proposal branch before committing.
Source fingerprint: `2f1f146da0b80ba7d30804b71d656cdf3b3b641ef25dad0216833ce08c1c0ea1`.
Algorithm: SHA-256 of sorted relative path + NUL + bytes + NUL for all files
under `spec/fir/proposals/`, plus its FIR README and the approved-decision index.
This report is excluded.

Status: **PROPOSED; human PI ratification pending.** No normative FIR byte/digest
expectations, mathematical interpreter, compiler, solver or SSA propensity was
implemented. The P01 reference-implementation acceptance PR is separate.

## Executed checks

Runtime: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0;
Julia 1.10.13/JSON 1.13.4/JSONSchema 1.6.0. Prefix uv invocations with
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`.

| Check actually executed | Outcome |
|---|---|
| `uv run --project packages/python --locked --offline python -` with Draft7Validator.check_schema and example assertions | PASS; candidate meta-schema valid; production/decay example accepted; unsupported SSA declaration rejected; broken-reference example structurally accepted as intended |
| `julia --project=conformance/julia -e ...` with JSONSchema.Schema/validate on the same three example files | PASS; independent structural results match Python |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `git diff --check` | PASS |
| Mathematical/reference/unit consistency validator | NOT RUN; not implemented before ratification |
| FIR canonical bytes/digests | NOT RUN; require ADR-P03 |
| Scientific approval or independent numerical oracle | PENDING; proposal checks are not scientific ratification |

All final executed checks exited 0. The structurally accepted broken-reference
example is deliberately NOT called mathematically valid. A future independent
semantic validator must reject it; structural schema validation cannot resolve
mathematical references or establish reaction/equation consistency.

## Reproduction of the proposal-only structural assertions

Load `spec/fir/proposals/fir-m0.schema.json` into Draft7Validator or JSONSchema.
Validate `examples/production-decay.json` successfully; reject
`examples/invalid-ssa.json`; structurally accept `examples/invalid-reference.json`.
The proposal documents its expected semantic rejection separately.

No native package source/dependencies changed; package smoke tests were not
rerun for this proposal-only branch. No P01 fixture or approved content digest
was changed. Issue #13 must remain open until the proposal is explicitly ratified
and its scientific fixture/review requirements are satisfied.

## Merge update after P01 PR #51

Merged `origin/main` at `a3c73f2` (P01 PR #51) into the ADR-P02 proposal branch
whose previous head was `da30e11`. The only merge conflict was an append conflict
in `docs/approved-decisions.md`. Resolution preserves both main's P01 reference
implementation/evidence section and the P02 proposal section. The full P02
contract, candidate schema and example files are byte-identical to `da30e11`;
`git diff da30e11 --exit-code -- spec/fir/proposals` exited 0.

Post-resolution checks executed from the repository root:

- PASS: `uv run --project packages/python --locked --offline python scripts/check_repo.py`.
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` (6 tests).
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` (6 tests including catalog subcases).
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` (2 smoke tests).
- PASS: `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p02-merge-python.json` (92 candidate cases).
- PASS: `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p02-merge-julia.json` (92 independent candidate cases).
- PASS: `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-p02-merge-python.json /private/tmp/fenix-p02-merge-julia.json` (92 matching cases).

uv invocations used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true`, and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`. Commands exited 0.
No new semantic/golden expectations were authored or ratified during this merge.
Historical proposal checks above still apply to the unchanged proposal files.

Resolved decision-index SHA-256: `72a7e2ed3401e1505cf90a24ca4af9e97f5f54c402052241dea500d034592c77`.

The unfiltered staged whitespace check flagged the intentional trailing spaces
and tab in `conformance/bioir/inputs/whitespace.input` imported from main. Its
bytes were confirmed identical to main and preserved. The staged formatting
check excludes only that one raw-input fixture; scientific fixture checks are
not excluded or changed. The normal working-tree whitespace check also passed.
