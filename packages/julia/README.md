# Julia scaffold (not yet a scientific library)

Provisional module/package name `Fenix`, subject to ADR-P06. Independent native Julia package, without Python or mandatory Catalyst dependencies. No BioIR/FIR APIs or solvers implemented.

    julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'

Smoke tests validate package load only.

Use native `Pkg` for package dependencies and juliaup to manage Julia runtimes.
CI and the separate reference-tool environment use Julia 1.10.13:

```sh
juliaup add 1.10.13
julia +1.10.13 --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
```

The library's manifest is intentionally untracked. The separate
[reference-tool environment](../../conformance/julia/README.md) commits its
manifest for reproducible tooling without adding dependencies to this library.
