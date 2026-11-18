# Native ODE scientific gate (#29)

The gate uses the unchanged APPROVED ten-scenario production–decay catalog and
its 40 samples, under ratified P04. It validates source and mathematical identity
before executing the installed native packages. It supplies bounded numerical
consistency, not biological validity or authenticated execution.

An independent Python reference builder imports neither native package. It
instantiates approved GFP source/model templates, using exact catalog binary64
words, Experiment ID `ode_<case-id>`, revision 1, one direct `amount` observable
and no interventions. External RFC 8785 and unchanged P03 normalization supply
derived source/model bytes. These generated artifacts do not replace approved
fixtures. Each producer validates them before solving; the comparator regenerates
expectations independently rather than trusting the supplied manifest.

Each language executes 60 runs: ten scenarios, two methods, three studies. Python
uses DOP853/Radau; Julia uses Tsit5/Rodas5P. Baseline settings are rtol=1e-10,
atol=1e-12, maximum step 1 s; refined settings are 1e-11/1e-13/0.5 s; coarse
settings are 1e-9/1e-11/2 s. The RHS budget is always 100000.

Reports retain raw binary64 words, settings, source/model identities, counters,
runtime/dependency versions and source/catalog/schema/lock fingerprints. At
100-digit Decimal precision, the comparator independently checks 320 required
baseline/refined reference errors against B=1e-9+1e-8*abs(reference), and 320
same-study Python–Julia method-pair differences against the derived 2B bound.
It also reports 160 coarse reference errors and 160 coarse pairwise differences.
Complete finite nonnegative output remains required for all studies. Existing
Julia tests retain their stricter coarse acceptance assertions. No monotonic
refinement or method-order claim is made. Signed zero is permitted; negative
samples, including negative subnormals, are rejected without clipping.

From the repository root, install the existing locked Python and native Julia
environments, then run (substitute the externally selected full source revision):

```sh
uv sync --project packages/python --locked
julia --project=conformance/julia_ode -e 'using Pkg; Pkg.instantiate()'
uv run --project packages/python --locked --offline python conformance/native/prepare_ode.py --source-revision "$REVISION" --report artifacts/ode-references.json
uv run --project packages/python --locked --offline python conformance/native/run_ode.py --references artifacts/ode-references.json --source-revision "$REVISION" --report artifacts/ode-python.json
JULIA_PKG_OFFLINE=true julia --project=conformance/julia_ode conformance/native/run_ode.jl --references artifacts/ode-references.json --source-revision "$REVISION" --report artifacts/ode-julia.json
uv run --project packages/python --locked --offline python conformance/native/compare_ode.py --references artifacts/ode-references.json --source-revision "$REVISION" --report artifacts/ode-comparison.json artifacts/ode-python.json artifacts/ode-julia.json
```

Use CPython 3.12.13, Julia 1.10.13, uv 0.11.29 and committed locks. Run all native
report tests, package tests, native FIR/ODE and independent reference suites as
specified in the development workflow. Julia keeps its pinned active environment
without LOAD_PATH changes or Python calls. Reference preparation, separate native
producers and comparison run in CI; the final context is `Native ODE scientific
gate`. Producer failures cannot become success through existing report files.
Artifacts also record runner image, kernel and CPU information.

Independent engineering and numerical reviews precede explicit human PI
scientific acceptance. Under the PI's 2026-11-18 single-maintainer governance
decision on #28, GitHub branch protection is deferred: the PI manually withholds
merge when CI fails. Workflow success does not establish automated merge
protection. #30 and final EP-04 acceptance remain separate.
