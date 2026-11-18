# #29 native ODE scientific gate — implementation evidence

Base main: `c248274ecd3352bdacc4f0d2f405f1668c103323` (merged #28).
Worktree: `/private/tmp/fenix-29`, branch `feat/29-native-ode`. Original checkout
edits are preserved. This receipt does not supply human scientific acceptance,
merge approval, #30 alpha acceptance or EP-04 closure.

## Scope and references

[Native gate instructions](../../conformance/native/ODE.md) describe the independent
reference builder, two native producers, closed report formats and 100-digit
Decimal comparator. Scientific authority remains ratified P01–P04 and the unchanged
APPROVED ten-scenario/40-sample production–decay catalog. Expected source/model
bytes are derived from approved templates with external RFC 8785; neither compiler
generates expectations. Production APIs, scientific contracts, package versions,
locks and approved fixtures are unchanged.

The matrix contains 480 outputs: 320 required baseline/refined reference checks,
160 coarse-study reference observations, 320 required same-study cross-language
method-pair checks and160 coarse pairwise observations. Required bounds remain
P04 B=1e-9+1e-8*abs(reference), and derived pairwise2B. All studies require complete
finite nonnegative outputs. Existing stricter Julia coarse tests remain intact.
No convergence-order, biological-prediction or authenticated-execution claim follows.

## Verification record

Local runtime: CPython3.12.13, Julia1.10.13, uv0.11.29; macOS x86_64. Native Julia
uses `conformance/julia_ode`, offline with depot `/private/tmp/fenix-julia-depot`.
Python uses its installed locked worktree environment. Full source/catalog/schema/
lock fingerprints accompany the generated artifacts; source revision selects the
external commit, while fingerprints identify any dirty implementation contents.

- PASS: repository checker and six harness regressions.
- PASS: full Python package suite,88 tests; native FIR catalog suite,3 tests.
- PASS: full Julia package tests in pinned native environment.
- PASS: unchanged Julia native ODE matrix,603 assertions, plus7 exploratory controls.
- PASS:16 Python analytical-reference tests and independent rational audit of all40 samples.
- PASS: 29 report/preflight regressions and Ruff checks after all owners froze sources.
- Final end-to-end evidence: PASS; native Python and Julia each emitted60runs/240samples; all320 required reference and320 required pairwise comparisons passed, with160 coarse observations of each kind.
- Hosted CI: not yet run at preparation of this receipt.
- Human scientific acceptance/merge: NOT RUN; leave issue open pending explicit acceptance.

Earlier failures: reference manifests were rejected as stale during parallel source
edits; these are deliberate fingerprint protection, not numerical acceptance.
An initial Julia report reader used the scientific JSON parser's binary64 numeric
policy for integer budgets; native transport parsing was corrected after lexical
validation so max_nfev retains its integer type. Independent review identified a
partial-failure report schema restriction that could mask numerical diagnostics;
the success comparator still enforces complete coverage after that correction.
No scientific fixture, threshold or production implementation was changed.

Engineering review was performed across ownership boundaries. A separate numerical
review checks comparator arithmetic and coverage. Agent review does not grant
human PI scientific acceptance. The human PI explicitly deferred automated branch
protection for this single-maintainer phase on #28; CI must fail on mismatches and
the PI manually withholds merge. No protection activation is attempted by #29.

The final source-stable pipeline used base revision c248274 with dirty-source fingerprints identifying the implementation. Prior corruption-test failures during parallel edits also identified stale fingerprints; the source-stable rerun passed. CI will use its exact GITHUB_SHA.
