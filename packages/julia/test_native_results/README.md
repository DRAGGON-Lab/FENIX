# Native Julia results verification

Run from the repository root using Julia 1.10.13 and the Pkg-generated native
SciML environment. Do not prepend the package environment to LOAD_PATH.

```sh
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode packages/julia/test_native_results/runtests.jl --report artifacts/julia-native-results.json
```

The runner asserts the loaded Fenix source path. It loads all four accepted
Python and four accepted Julia profile examples using supplied exact local
sources; verifies immutable/fresh exports and original formatting/newlines;
rejects closed-shape/source/FIR/grid/counter/interface failures; and runs a fresh
Julia child with solver entry points trapped during readback. Readback compiles
sources but must never execute either backend.

Capture is compared against all 40 fixed independent analytical samples using
Tsit5 and Rodas5P at P04 baseline (`rtol=1e-10`, `atol=1e-12`, `max_step=1s`) and
refined (`1e-11`, `1e-13`, `0.5s`) settings, each with RHS budget 100000. Binary64
samples convert exactly to BigFloat at 512-bit precision; acceptance remains
`1e-9 + 1e-8*abs(reference)` molecules. No expected value is generated from the
native solver. Every capture's own sample bits survive serialization and loading;
independent reruns are not required to have identical bits.

The report fingerprints actual runtime/platform, source, schema, catalog,
evaluator and lock bytes and records 160 sample/method/setting comparisons.
Report destinations reuse the existing guard against overwriting inputs and
symlink/hardlink aliases. CI uploads a separate native-results artifact.
Historical independent receipts and the independent reference lock stay intact.

Package unit tests separately cover malformed raw JSON, lexical numeric rules,
signed-zero/subnormal/midpoint transport, exact large-integer mutation isolation,
backward wall clocks and no-success-on-failure without repository fixtures.
These checks establish bounded consistency and analytical agreement, not
execution authenticity, empirical biological validity, #29 or human acceptance.
