# EP-03 / #24 — native Julia committed BioIR documents

Implemented on base `7391ddc236e1` in branch `feat/24-julia-documents` under
unchanged ratified ADR-P01 and its approved independent references. #14 and #23
are completed prerequisites. This record supplies implementation evidence for
human review, not PI acceptance, issue closure or release authorization.

The native package now provides strict original-byte JSON parsing, direct RFC
8785/JCS content identity, immutable committed Design/Experiment envelopes,
verified local exact Design references, trusted expected-digest checks,
predecessor-relative revision replacement and metadata amendments. It depends
on JSON.jl and Julia's SHA standard library, without Python or reference-tool
imports. No persistence/history service, FIR compiler, solver or authentication
mechanism is introduced. Callers retain historical documents.

Self-consistency is distinct from trusted reference identity. Committed Experiment
loading verifies its own digest before local resolution; supplied Designs are
verified immutable native values. Direct construction revalidates uncommitted
Experiment data against the exact verified Design. No network lookup or reference
substitution is available. Metadata remains outside scientific content identity.
Transport JSON retains Float64 spellings needed by P01's safe integer-token rule;
canonical content bytes are a separate artifact and apply no FIR normalization.

## Executed checks

Environment: Julia 1.10.13, JSON 1.13.4, JSONSchema 1.6.0, uv 0.11.29,
CPython 3.12.13. Julia used `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`
and `JULIA_PKG_OFFLINE=true`; uv used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`.
Julia commands below used `/private/tmp/julia-1.10.13/bin/julia`.

| Command | Outcome |
|---|---|
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS, 660 assertions: 402 existing + 77 JSON + 181 documents |
| `julia --project=conformance/julia packages/julia/test_native_documents/runtests.jl --report artifacts/julia-native-documents.json` | PASS, original 92 + overlapping 97 P01 cases, 743 assertions; 27 approved binary64 JCS vectors, 53 assertions; local package identity assertion |
| `julia --project=conformance/julia packages/julia/test_native_content/runtests.jl` | PASS, existing 29 builder projections |
| Copied standalone package tests with `PATH=/nonexistent` | PASS, 660 assertions; no Python/Python3 executable available |
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS, three methods covering same 92 + 97 P01 case sets and schema/transport checks |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 88 tests |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, six tests |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report artifacts/p01-python.json` | PASS, 92 independent reference cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report artifacts/p01-julia.json` | PASS, 92 independent reference cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py artifacts/p01-python.json artifacts/p01-julia.json` | PASS, 92 matching approved expectations |
| `node conformance/reference/check_p01.cjs` | PASS, 41 independent byte/digest checks |
| `git diff --exit-code -- spec/bioir spec/fir spec/canonicalization conformance packages/python` | PASS, protected contracts/references/Python unchanged |
| `git diff --check` | PASS |

Standalone validation copied the package and its ignored generated manifest to
`/private/tmp/fenix24-standalone`, loaded that project with an absolute Julia
executable and executed its package tests outside the repository. Neither Python
executable was available on PATH. The library manifest remains untracked.

The adjacent JSON receipt records source-file hashes, a source fingerprint and
retained log tails/hashes. Original source-linked receipts and historical
acceptance records remain unchanged. CI runs the new native document suite and
uploads its report separately from historical independent reference reports.
Hosted CI is NOT RUN locally; its results must be checked on the PR.

## Review and limits

Separate agents independently reviewed parser/serialization engineering and
P01 document integrity/scientific boundaries; no confirmed defects remained.
Supplemental seeded finite-binary64 comparisons against Node JSON.stringify
found no mismatches (9,999 and 19,988 samples in two separate agent runs). These
exploratory checks create no golden values and do not prove universal correctness.

Initial red attempts failed at integration: the first root attempt lacked a
resolved package environment; a subsequent test-agent attempt reached missing
PortableJSON.jl, then a file-level docstring error. They are not behavioral red
evidence. Final integrated suites passed after dependency setup and header fix.

The bounded fixture sets overlap and are not exhaustive. Broader malformed-input,
FIR normalization/compiler, native dual-language ODE, stronger provenance and
whole-project release acceptance remain separate gates. No scientific contract,
approved fixture, mathematical meaning or package version was changed.
