# Julia reference-tool environment

This environment pins development tools separately from the native library.
It now runs the independent [P01 candidate catalog](../bioir/README.md)
reference validator. Its fixtures require PI review before implementation
approval; approved normative fixtures are not yet published.
Do not count successful dependency installation as scientific conformance.

Use juliaup to select the reference runtime:

```sh
juliaup add 1.10.13
julia +1.10.13 --project=conformance/julia -e 'using Pkg; Pkg.instantiate()'
```

Commit the Pkg-generated `Manifest.toml` here. Update it deliberately with Pkg,
review the dependency diff, and rerun the applicable checks. The library's own
manifest remains untracked so it can resolve independently.

After initial installation, check that the pinned tools load without network:

```sh
JULIA_PKG_OFFLINE=true julia +1.10.13 --project=conformance/julia -e 'using JSON, JSONSchema, SHA, Test'
```

P01 reference commands are in the catalog instructions. FIR/solver conformance
still requires its separately ratified contracts and independent evidence.
