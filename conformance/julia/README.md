# Julia reference-tool environment

This environment pins development tools separately from the native library.
It does not yet contain scientific validators or approved reference fixtures.
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

Scientific validation commands will be added after their contracts are ratified.
