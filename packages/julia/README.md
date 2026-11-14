# Julia scaffold (not yet a scientific library)

Provisional module/package name `Fenix`, subject to ADR-P06. Independent native Julia package, without Python or mandatory Catalyst dependencies. No BioIR/FIR APIs or solvers implemented.

    julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'

Smoke tests validate package load only.
