# Independent native M1 conformance

Refs #35. This gate runs the accepted P08 profile through independently installed
Python and Julia packages. The Python wheel installs only locked runtime
dependencies. Julia loads an archived package tree with its own locked
environment and depot. Each runtime compiles and executes its own inputs,
then reads the other runtime's original result and manifest bytes.

Each producer supplies ten cases with two methods and two settings, for 80
successful runs and 240 four-state samples in total. The comparator checks
canonical model and identity bytes against the accepted fixtures and checks all
state samples independently against the accepted Decimal law. It derives the
closed signal bound using population weights and the initial representation
error. It checks pairwise state differences against twice the single-backend
bound, by the triangle inequality. Cases, solver controls, and bounds come from
the accepted packet. The gate requires both languages to read and verify all
40 peer records with unchanged bytes.

The method calls and work counters are backend-specific. The checks address
scientific conformance in this bounded matrix and preservation of the exact
portable identities. Native failure cases are exercised by the two package
suites. See the [PI decision](../../docs/verification/m1-executable-acceptance.md)
for the scope and the [Python](../../packages/python/README.md) and
[Julia](../../packages/julia/README.md) examples for usage.

The [workflow](../../.github/workflows/native-community-integration.yml)
publishes the per-run artifacts and comparison receipt. Install-time dependency
resolution is followed by local execution and peer readback. From environments
prepared as in the workflow, reproduce with:

```sh
mkdir -p artifacts/m1-native
revision=$(git rev-parse HEAD)
python conformance/native_community/python_m1.py produce "$PWD" artifacts/m1-native "$revision"
julia --project=conformance/julia_ode conformance/native_community/julia_m1.jl produce "$PWD" artifacts/m1-native "$revision"
julia --project=conformance/julia_ode conformance/native_community/julia_m1.jl read "$PWD" artifacts/m1-native "$revision"
python conformance/native_community/python_m1.py read "$PWD" artifacts/m1-native "$revision"
PYTHONPATH=conformance/community python conformance/native_community/compare.py "$PWD" artifacts/m1-native "$revision"
```
