# EP-02 / #21 — native Python M0 ODE execution

P04 was explicitly ratified by the human PI at reviewed revision `67820ae`;
the decision and accepted concerns are recorded at `147f216`. This separate
implementation starts from that ratification branch without merging it.
Human implementation review remains pending; #22/#29 and parent epic closure
are excluded.

## Delivered behavior and evidence limits

`fenix.execution.solve_ode` executes validated FIRModel with explicit immutable
ODEExecutionSpec and returns tuple-backed ODETrajectory. DOP853 and Radau use the
ratified M0 RHS, with exact constant Radau Jacobian. Zero-only and late-first
grids retain x(0) semantics. Named/empty observations and units are preserved.
The executor changes no FIR/source/provenance bytes or mathematical digest.

Negative sampled counts fail strictly, including tiny interpolation excursions:
the PI consciously accepted possible failure of mathematically well-posed models.
No clipping, hidden fallback or analytical replacement occurs. Underflow follows
binary64 without a floor. Errors distinguish configuration/profile, work budget,
nonfinite arithmetic/output, failed integration and malformed/partial samples.

**Bounded agreement does not imply byte-identical trajectories.** This remains
explicit in the API and README and must remain explicit in future #22/P07
manifests. Local tolerances do not certify arbitrary-input global error. No SSA,
empirical validity or independent dual-language #29 gate is claimed.

The isolated P04 experiments and seven jobs in historical Actions
[run43853787258](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43853787258)
remain separate infrastructure evidence. This record newly executes **68 package
tests**, including **22 native execution methods**, against editable and clean
wheel installations. Native tests cover all PI-requested sampling/failure cases
and all **40 approved samples × two methods × nominal/fine settings** (160 repeated
comparisons, not independent models). Stiff Radau and deliberate DOP853 work-limit
controls use the independent analytical law; approved fixtures are unchanged.
Real overflow/subnormal/budget cases complement controlled backend negative,
nonfinite/status/shape failures. Native tests run through package discovery in
CI, including its clean wheel job.

## Execution and review

The [machine-readable receipt](ep02-python-ode.json) contains exact command
argument vectors, UTC starts, exit codes, log hashes/excerpts, environment,
per-file hashes and artifact identities. Runs were dirty on `147f216`.
Logs/temporary audits remain in ignored `artifacts/ep02-21/`. The source
fingerprint excludes this evidence pair to avoid self-reference.

All uv commands below use `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`; Julia uses
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and `JULIA_PKG_OFFLINE=true`.

| Exact command | Fresh outcome |
|---|---|
| `uv build --project packages/python --offline` | PASS (exit 0) |
| `node conformance/rejections/audit_inputs.cjs` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline ruff format --check packages/python/src/fenix packages/python/tests packages/python/tests_native_content packages/python/tests_native_documents packages/python/tests_native_fir` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS (exit 0) |
| `/private/tmp/julia-1.10.13/bin/julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline ruff check packages/python/src/fenix packages/python/tests packages/python/tests_native_content packages/python/tests_native_documents packages/python/tests_native_fir` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS (exit 0) |
| `python3 artifacts/ep02-21/audit_protected.py` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python conformance/production_decay/audit_rational.py` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --compare artifacts/ep02-21/rejections-python.json artifacts/ep02-21/rejections-julia.json` | PASS (exit 0) |
| `/private/tmp/julia-1.10.13/bin/julia --project=conformance/julia conformance/rejections/review.jl --report artifacts/ep02-21/rejections-julia.json` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python conformance/rejections/review.py --report artifacts/ep02-21/rejections-python.json` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/rejections/tests -v` | PASS (exit 0) |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS (exit 0) |
| `uv export --project packages/python --locked --no-dev --no-emit-project -o /private/tmp/fenix-21-runtime.txt` | PASS (exit 0) |
| `uv pip install --offline --python /private/tmp/fenix-21-wheel/bin/python --require-hashes -r /private/tmp/fenix-21-runtime.txt` | PASS (exit 0) |
| `/private/tmp/fenix-21-wheel/bin/python artifacts/ep02-21/wheel_audit.py` | PASS (exit 0) |
| `uv venv --python 3.12 /private/tmp/fenix-21-wheel` | PASS (exit 0) |
| `uv pip install --offline --python /private/tmp/fenix-21-wheel/bin/python --no-deps packages/python/dist/fenix_bio-0.0.0-py3-none-any.whl` | PASS (exit 0) |
| `/private/tmp/fenix-21-wheel/bin/python -m unittest discover -s packages/python/tests -v` | PASS (exit 0) |
| `git diff --check` | PASS (exit 0) |

Four initial receipt-wrapper checks failed imports because inherited macOS
`__PYVENV_LAUNCHER__` leaked a system-Python prefix. Clearing that launcher variable
fixed replay without package changes. Failed and corrected checks are retained
separately. Initial missing-module red and three intermediate mypy typing errors
are recorded. No expectations, mathematics or tolerance thresholds were weakened.
The evidence-assembly helper also initially used unavailable shlex.join in the
system Python; portable quoting corrected that helper without affecting checks.

The clean wheel contains only fenix-bio, NumPy, SciPy and rfc8785; no development
dependencies. Installed execution source matches tested source and py.typed is
present. Separate engineering and numerical reviewers found no confirmed defect.
Both independently ran all22 execution tests; numerical review additionally
passed240 native coarse/nominal/fine comparisons and checked units/references.
Agent review is bounded evidence, not human implementation approval.

Both rejection reports were independently regenerated and compared: only the
Python manifest/lock fingerprints differ from `147f216`; all207 outcomes and
other fields are unchanged. [Current hashes](ep01-rejections.md#ep-02-ode-runtime-dependency-provenance-refresh)
are checked against retained bytes and recorded in this receipt. Original
compiler/P04 receipts and approved scientific fixtures remain unchanged.

**NOT RUN:** Julia ODE execution, independent cross-language #29, systematic
#59 generated-input investigation, #22/P07 results/manifests and human
implementation approval. New hosted CI is observed separately after push.
