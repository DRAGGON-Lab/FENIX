# M0 performance observations

Run one case and method per fresh process, after installing dependencies. From the
repository root, substituting the full reviewed commit SHA for `REVISION`:

```sh
uv run --project packages/python --locked --offline python benchmarks/m0/run.py --case baseline-five --method DOP853 --source-revision "$REVISION" --output artifacts/benchmark-python.json
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode benchmarks/m0/run.jl --case baseline-five --method Tsit5 --source-revision "$REVISION" --output artifacts/benchmark-julia.json
```

Repeat for `linear-production` and the other native methods (`Radau`, `Rodas5P`).
Both drivers default to three warmups and twenty measured repetitions per phase;
`--warmups` and `--repeats` allow exploratory runs, but alpha evidence requires the
default counts. No benchmark dependency or statistical package is required.

The two workloads use unchanged approved [production–decay catalog](../../conformance/production_decay/catalog.json)
parameters/grids and #29 baseline solver settings. Every sampled result is checked
against fixed approved decimal references with unchanged P04 global error bounds,
outside the timed region. Capture is also read back through its native API.
Compilation measurements are checked for unchanged FIR identity. Independent CI
verification compares the example identities against #29 derived references.

Package-load timing includes loading the example helper and native package after
interpreter startup. First-call timing includes JIT where applicable. Compilation
means public `compile_experiment`; solving uses an existing compiled FIR;
capture means public `run_experiment`, which includes its own validation and
compilation. Each phase records its first invocation before that phase's warmups.
The later phases can benefit from earlier phases' compilation and caches; these
are first calls in a documented sequence, not independent process-start costs.
Authoring, file writes, correctness checks and report formatting are excluded
from timing. Garbage collection is left at each runtime's default and thread
settings are recorded, not silently changed. There is no performance threshold,
claimed convergence order, biological predictive claim, or language ranking.

Reports preserve every measured duration, median/range, runtime and dependency
versions, CPU/OS/thread/runner information, source/lock/catalog fingerprints and
source/FIR identities. `source_revision` is externally supplied; fingerprints
identify dirty source contents as well. These are consistency receipts, not
execution-authenticity evidence. CI and local-machine observations must remain
separate baselines rather than being averaged across different machines.

Run failure controls with:

```sh
uv run --project packages/python --locked --offline python -m unittest discover -s benchmarks/m0 -v
```

```sh
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode benchmarks/m0/test_checks.jl
```
