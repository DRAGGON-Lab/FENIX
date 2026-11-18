# Native FIR conformance (#28)

This test-only gate runs each installed native package independently against the
unchanged APPROVED catalogs, then validates both reports against references
before comparing their bytes. It does not change scientific contracts or approve
ODE execution, biological predictions, or an alpha release.

From the repository root (uv 0.11.29, CPython 3.12.13, Julia 1.10.13):

```sh
uv sync --project packages/python --locked
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
uv run --project packages/python --locked --offline python -m unittest discover -s conformance/native/tests -v
uv run --project packages/python --locked --offline python conformance/native/run_fir.py --source-revision "$(git rev-parse HEAD)" --report artifacts/native-fir-python.json
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode conformance/native/run_fir.jl --source-revision "$(git rev-parse HEAD)" --report artifacts/native-fir-julia.json
uv run --project packages/python --locked --offline python conformance/native/compare_fir.py --source-revision "$(git rev-parse HEAD)" artifacts/native-fir-python.json artifacts/native-fir-julia.json
```

Each report contains exactly 300 rows: 84 canonicalization cases, 207 rejection
cases and nine native compiler producer controls (overlapping input sets).
Rejections retain approved category, path and document expectations; the old
reference-only stage labels are not native API promises. Canonicalization cases
emit actual bytes wherever the catalog supplies expected bytes. Thirteen FIR
identity cases and nine producer controls emit actual normalized model bytes,
identity-preimage bytes and SHA-256 digests. Each runner also checks that the
native digest property matches the hash of emitted native identity bytes.
Compiler provenance is excluded from mathematical byte equality.

For producer controls, the comparator reads the approved primary FIR artifacts,
applies only P03's six declaration/assumption sorts using UTF-16 ordering, and
serializes with external `rfc8785`. It never imports a native package or invokes
either compiler to generate expectations. The 13 identity expectations are the
unchanged approved byte artifacts. Independent reference validation precedes
pairwise comparison, so two implementations agreeing on an incorrect result fail.
Mismatches identify case/artifact, both hashes, first byte offset and at most 33
bytes of context from each side.

The version 1 [report schema](fir-report.schema.json) closes report, runtime,
case, observation and byte objects. The comparator enforces exact row coverage,
source references, outcomes, diagnostics, bytes and hashes, default runtime pins,
locked dependency versions and current source/catalog/schema/lock fingerprints.
The native package must resolve to the fingerprinted checkout sources. Reports
inside the checkout must be under ignored `artifacts/`; source/fixture symlink
and hardlink aliases cannot be overwritten through this destination rule.
Reports establish bounded consistency, not authenticated execution. The CLI's
`--source-revision` must be the externally selected full commit SHA (CI uses
`GITHUB_SHA`); fingerprints additionally identify dirty source contents.

[CI](../../.github/workflows/native-fir.yml) exchanges artifacts between separate
Python and Julia jobs. The final stable context is **Native FIR conformance**.
Each producer artifact also records the actual runner image identifiers, kernel
and CPU configuration. It fails if either producer fails, including when a report was written before
validation failed. Protected-branch requirement activation is a separate
administrator step; merely adding this workflow does not enforce main protection.

Historical reference receipts and their NOT_RUN outcomes remain unchanged.
#29 numerical comparison, #30 repository alpha, registry publication, P06,
production API expansion and final EP-04 PI acceptance are outside this PR.
