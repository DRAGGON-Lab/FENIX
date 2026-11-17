# Locked native Julia ODE test environment

Julia 1.10.13. Unlike the independent reference environment in `../julia`, this
environment intentionally loads native Fenix from `../../packages/julia` and
pins the tested SciML dependency graph. Project/Manifest files are Pkg-generated.
The package's own Manifest remains ignored and both packages remain independently
installable. No Python or Catalyst runtime is required.

```sh
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode packages/julia/test_native_ode/runtests.jl --report artifacts/julia-native-ode.json
```

Regenerate through Pkg only when deliberately updating tested dependencies.
Do not regenerate approved mathematical references from numerical output.
