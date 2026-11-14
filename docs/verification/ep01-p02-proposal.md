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
