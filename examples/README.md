# Native M0 examples

[production_decay.py](m0/production_decay.py) and
[production_decay.jl](m0/production_decay.jl) independently author the same
immutable GFP Design and Experiment, compile mathematical FIR, run a supported
ODE method, save the artifacts, and verify the saved source/result readback.
They use public APIs and runtime dependencies only; neither script reads
repository fixtures or calls the other language.

The two cases use exact inputs and grids from the approved
[production–decay oracle](../conformance/production_decay/README.md):

| Case | Production (molecule/s) | Decay (1/s) | Initial count (molecule) | Sample times (s) |
| --- | ---: | ---: | ---: | --- |
| `baseline-five` | 10 | 0.1 | 5 | 0, 1, 10, 100 |
| `linear-production` | 2 | 0 | 0.5 | 0, 0.5, 1, 10 |

Counts are expected intracellular counts per representative cell. The example
cell volume is explicitly 1e-15 L; no concentration conversion is performed.

From the repository root, after installing the environments documented in the
[development workflow](../docs/DEVELOPMENT_WORKFLOW.md):

```sh
uv run --project packages/python --locked --offline python examples/m0/production_decay.py --case baseline-five --method DOP853 --output-dir artifacts/example-python
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode examples/m0/production_decay.jl --case baseline-five --method Tsit5 --output-dir artifacts/example-julia
```

Python also supports `Radau`; Julia also supports `Rodas5P`. Both use rtol=1e-10,
atol=1e-12, maximum step 1 s and an RHS evaluation budget of 100000. Change
`--case` to `linear-production` for the approved zero-decay scenario. The explicit
`--output-dir` is required; rerunning replaces files in that destination.

Each destination contains committed `design.json` and `experiment.json`, their
canonical content bytes, `fir.json`, canonical model and identity-preimage bytes,
`result.json`, `manifest.json`, and a checksum/source/package-location summary.
The scripts reload the saved source and result files using the native APIs.
The alpha verifier checks the independently approved reference values; example
outputs themselves are observations, never replacement golden fixtures.

Python reads the Python backend profile; Julia reads both approved backend
profiles. Identical FIR mathematical identity is required, while independent
result digests and numerical trajectories need not be identical. These bounded
examples establish neither biological predictive validity nor authenticated
execution. Alpha/release acceptance remains a separate human decision.

The scripts can also be copied outside the checkout and run using an installed
Python wheel or Julia package. They do not alter `sys.path` or `LOAD_PATH` to
locate FENIX. Fresh-install proofs and performance receipts are part of #30's
alpha evidence; package names and versions remain provisional under P06.
