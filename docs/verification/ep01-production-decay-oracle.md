# EP-01 production–decay oracle evidence — approved

**Current status: APPROVED by the human PI.** See the
[acceptance record](#human-pi-acceptance-recorded). Earlier REVIEW_REQUIRED and
pending statements below describe historical revisions.

Date: 2026-11-14. Issue [#15](https://github.com/DRAGGON-Lab/FENIX/issues/15).
Branch: `conformance/15-production-decay-oracle`. Base: current `origin/main`,
`fb2d78c0549526a8622c18a3bd71c1993084448c`, including merged PR #53.
The [P02 contract](../../spec/fir/proposals/ADR-P02.md) is ratified; the concrete
[candidate numerical catalog](../../conformance/production_decay/catalog.json)
remains **REVIEW_REQUIRED**. P04 thresholds are not ratified by this work.

## Scope, source and runtime identity

One implementer owns the derivation, candidate catalog/schema, independent
reference CLIs, failure tests, documentation and CI integration. Native package
sources, existing contracts, fixtures, catalogs and locked environments are
unchanged. No modeling API, compiler, solver, SSA support or empirical-validity
claim is added. The issue remains open pending scientific acceptance.

Verification ran on the dirty issue branch based at the revision above. Source
fingerprint: `460c3b46769a904922b996981793da79d9c9e1ad2206c3412da2bf29d1adc478`.
Algorithm: SHA-256 of sorted repository-relative path + NUL + exact bytes + NUL,
over the seven non-cache files under `conformance/production_decay/`, plus
`.github/workflows/scaffold-smoke.yml`, `conformance/README.md`,
`docs/scientific-evidence/README.md` and
`docs/scientific-evidence/production-decay.md` (11 files). This report and its
output JSON artifacts are excluded to avoid a circular fingerprint. This is
source provenance, not FIR identity.

Environment: uv 0.11.29; CPython 3.12.13 with libmpdec 4.0.0; Julia 1.10.13 with
MPFR 4.2.0. Existing locked Python tools include jsonschema 4.26.0; Julia uses
its unchanged reference manifest. No dependency was added.

All commands below ran from repository root. Python commands used
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. `julia` below means
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`, with
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and `JULIA_PKG_OFFLINE=true`.
These cached runtimes/environments were already available. CI pins Python 3.12
(patch chosen by setup-python), uv 0.11.29 and Julia 1.10.13 in the existing
native jobs.

## Candidate preparation and independent evidence

The [derivation](../scientific-evidence/production-decay.md) precedes candidate
evaluation and establishes initial condition, differential equation, uniqueness,
nonnegativity, equilibrium, monotonicity, pure decay and the fixed-time
zero-decay limit. Parameters and times are exact represented binary64 numbers,
not their short decimal spellings. Units are expected molecules per
representative cell and seconds, under constant rates, fixed volume,
well-mixed conditions and no interventions.

Candidate preparation occurred in a one-off external scratch calculation,
without either shipped evaluator or any FENIX package. Exact rational arithmetic
lifted the input bit patterns and evaluated

\[
 x_0+(\alpha-\beta x_0)t
       \sum_{n=0}^{400}\frac{(-\beta t)^n}{(n+1)!}.
\]

For this matrix, \(0\le\beta t<11\) and
\(|\alpha-\beta x_0|t<20000\). The alternating series is decreasing in
magnitude by the omitted tail. A conservative absolute remainder bound is
\(20000\,11^{401}/402! < 7.687\times10^{-453}\) `molecule`.
The rational sums were converted at 300 decimal digits and published with
half-even rounding to 50 significant digits (zero explicitly preserved).
A separate read-only 500-digit endpoint audit checked all 40 samples: both
ends of the exact-rational first-omitted-term enclosure round to the fixed
published expectation. No expectation-regeneration command is shipped.

The shipped Python integrating-factor evaluator uses Decimal at 100/200 decimal
digits, lifting decoded values with `Decimal.from_float`. The separate Julia
evaluator uses BigFloat at 512/1024 bits and the `expm1` form. Both branch on
exact zero decay before division, have no FENIX imports, and do not call each
other. Each independently checks every computed result against its fixed
50-digit candidate; the comparator requires agreement of all four evaluations
at 70 significant digits and complete unique catalog coverage.

Executed artifacts (all computed values are decimal strings):

- [Python report](production-decay-python.json), 80 computations;
  SHA-256 `9b4673b1d4eb0693f5b2745f24c6d0a1b7275882ebbf93c0c0ff87cb069f58bf`.
- [Julia report](production-decay-julia.json), 80 computations;
  SHA-256 `b31021db5c89aa852aae02fdac84d0f3557ac938c380d860e209174cf2aea5dd`.
- [Cross-language comparison](production-decay-comparison.json), 40 samples / 160
  computations, all four agree at 70 significant digits and match fixed candidates.

Both reports identify exact catalog SHA-256
`ccf91c358d0a34eb793942e23790e539360bbb658489d4f91563f11d36b5dac2`,
current evaluator source checksums, precision units and runtime/library versions.
Checksums identify artifacts; they do not authenticate execution.

## Observed residuals and precision study

| Quantity | Observed maximum | Sample |
|---|---|---|
| Absolute Python 100-vs-200-digit spread | `5.483038997782e-89` molecule | `small-decay-40`, `t=10 s` |
| Absolute Julia 512-vs-1024-bit spread | `1.394634753145e-152` molecule | `baseline-five`, `t=100 s` |
| Absolute spread across all four computations | `5.483038997782e-89` molecule | `small-decay-40`, `t=10 s` |
| Relative spread across all four (nonzero results; denominator is the 1024-bit reference) | `1.624114034413e-89` | `small-decay-40`, `t=1 s` |
| Absolute difference of 1024-bit reference from published 50-digit value | `3.477344331294e-49` molecule | `baseline-five`, `t=100 s` |

Table values summarize the unrounded observed differences. The full maximum
spread is in the comparison artifact. For the last row, the trajectory has
decimal exponent 1, so the publication rounding bound is `5e-49 molecule`.
Exact initial conditions, zero dynamics, equilibrium and dyadic zero-decay
arithmetic pass exact equality checks at both native precisions. Nonnegative
trajectories, monotonicity, equilibrium bounds and the fixed-time small-decay
error bound pass. Substituting decimal-real `0.1` fails reference comparison.
No numerical ODE residual, integration error or interpolation error is measured:
there is no solver in this task. The differential-equation residual vanishes
analytically by the displayed derivation.

These observations establish stability for the bounded catalog. Agreement of
multiprecision calculations is not itself a certified interval error bound.
The [draft error budget](../scientific-evidence/production-decay.md#draft-numerical-error-budget)
separates exact input interpretation, reference arithmetic, 50-digit publication,
eventual binary64 rounding, integration and interpolation. P04 must select
solver thresholds and failure policy; no solver tolerance is silently inferred.

## Executed checks

| Command/check | Result |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v` | PASS; 11 tests with negative subcases |
| `julia --project=conformance/julia conformance/production_decay/tests/test_oracle.jl` | PASS; 252 assertions |
| `uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --report docs/verification/production-decay-python.json` | PASS; 80 computations |
| `julia --project=conformance/julia conformance/production_decay/review_oracle.jl --report docs/verification/production-decay-julia.json` | PASS; 80 computations |
| `uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --compare docs/verification/production-decay-python.json docs/verification/production-decay-julia.json` | PASS; 40 samples, 160 computations |
| Read-only exact-rational sum endpoint audit at 500 decimal digits | PASS; all 40 fixed expectations |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; final repository and link checks |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 package smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 package smoke tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS; 6 existing P01 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v` | PASS; 5 existing P03 tests |
| `git diff --exit-code origin/main -- spec packages conformance/bioir conformance/python conformance/julia conformance/canonicalization conformance/compare_reports.py conformance/reference` | PASS; existing contracts, fixtures, catalogs, reference tools and package sources unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| Ruby standard-library YAML parse and comparison-job dependency check | PASS |
| Hosted GitHub Actions | NOT RUN locally; CI integration supplied for the PR |
| Native modeling APIs, solvers, binary64 integration/interpolation thresholds, SSA or empirical validation | NOT RUN; outside scope / pending separate contracts |
| Human PI acceptance of numerical fixtures | NOT RUN; pending review; catalog remains REVIEW_REQUIRED |

Tests were written before the evaluators: the first Python and Julia test runs
failed because those modules did not yet exist. The early repository-link check
also failed while this verification record was still absent; the final run
passes. Independent review then reproduced a concrete boundary defect: Julia's
`Set{Float64}` distinguished positive and negative zero as sample times, while
Python rejected the duplicate. Normalizing zero before Julia's set lookup fixed
the defect; both suites now include the signed-zero regression. No candidate
value changed to resolve a failure.

Negative checks cover malformed bit patterns, negative/nonfinite inputs,
incorrect units, malformed expected strings, corrupted expectations, duplicate
case/time identities, stale checksums, missing/duplicate/altered report rows,
missing precision runs and two reports from the same implementation. A
61st-digit alteration passes 50-digit checks and fails 70-digit comparison.
Synthetic transport reports in the Python tests test comparison failure paths;
the saved Julia report comes from real independent Julia arithmetic. Coverage
checks derive the complete required set from the catalog rather than a fixed
case count.

## Independent numerical review and remaining gate

A separate read-only numerical reviewer checked the derivation, units, exact
binary64 interpretation, candidate values, evaluator independence, rounding,
report boundaries and error budget. An independent exact-rational 256-term
solution-series probe with an alternating-tail bound put all 40 true values
inside their published 50-digit rounding cells; the smallest margin as a
fraction of half a rounding cell was approximately `0.009256632825146329`
(`small-decay-40`, `t=0.5 s`). The reviewer independently ran the native tests
and cross-language comparison, confirmed the signed-zero fix, and found no
remaining numerical blocker. This agent review is evidence, not human PI
acceptance or an empirical validation claim.

The human PI must review and accept these concrete expectations before they
become approved scientific fixtures. Keep issue #15 open and the catalog
REVIEW_REQUIRED until that decision. P04 numerical solver thresholds and failure
policy remain a separate unratified contract; approval of the implementation
plan does not ratify either the numerical fixtures or P04.

## Review follow-up: sample order and retained rational audit

Date: 2026-11-14. PR [#54](https://github.com/DRAGGON-Lab/FENIX/pull/54).
Follow-up baseline: `66be371c44a0d580ddf646b5a1688e00f284b287`. The preceding
record describes that historical revision and is preserved. Environment and
cache/runtime command prefixes are unchanged from the record above.

Read-only reproduction reversed the catalog's samples in memory: the previous
monotonicity checks failed seven Python cases and fourteen Julia case/precision
pairs. Sorting a separate `(numerical time, value)` view made those probes pass.
The updated suites exercise original, reversed and rotated samples at both
precisions, retain the original sample/value association for expectation checks,
and reject deliberately incorrect time/value associations. They assert that
the input catalog was not mutated. Decimal-real `0.1` regressions now select
case `baseline-zero` and time bits `3ff0000000000000` by identity instead of
position, keeping that regression meaningful under reordering.

The retained [rational auditor](../../conformance/production_decay/audit_rational.py)
is a read-only reconstruction of the documented candidate-preparation recurrence,
not a verbatim archive of the scratch generator. It independently decodes
binary64 bits to exact fractions, calculates terms `n=0…400`, and bounds the
remainder by the absolute first omitted term, with factorial denominator `402!`.
The bounds `beta*t < 11` and `|(alpha-beta*x0)*t| < 20000` are checked before
calculation; they restrict this audit rather than FIR admissibility. Both
endpoints are rounded half-even to 50 significant digits using exact integer
quotient/remainder operations, replacing the scratch script's finite-precision
decimal publication step. All 40 enclosures round to the unchanged expectations.
This supplies a bounded enclosure audit separately from the two evaluators'
observed precision stability and makes no solver-error claim.

The auditor imports neither evaluator nor any FENIX package, adds no dependency,
and has no write/regeneration path. Its optional `--catalog PATH` selects an
input; stdout identifies every checked sample and the catalog checksum, and
errors produce a nonzero exit. Tests cover half-even ties, decade carries,
negative rounding, exact zero/initial/equilibrium/zero-decay cases, omitted-tail
indexing, malformed/negative/nonfinite encodings, incorrect units, audit-domain
limits and corrupt expectations. CLI tests verify byte-identical inputs after
both successful and failing audits. The new audit tests initially failed to
import the not-yet-created module; all final tests below pass.

Follow-up source fingerprint:
`e8e994304de37c01681ca3884d00d3efe90e2c41854bd0228e0839c124f68985`.
The same sorted path + NUL + bytes + NUL SHA-256 algorithm and scope as above
now cover 13 files (nine under `conformance/production_decay/`, excluding caches,
and the same four documentation/CI paths). The evidence record and output
reports remain excluded. Verification ran dirty on the follow-up baseline.

| Command/check | Follow-up result |
|---|---|
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/production_decay/tests -v` | PASS; 16 tests, including four rational-audit tests |
| `julia --project=conformance/julia conformance/production_decay/tests/test_oracle.jl` | PASS; 647 assertions |
| `uv run --project packages/python --locked --offline python conformance/production_decay/audit_rational.py` | PASS; all 40 samples, unchanged catalog checksum |
| `uv run --project packages/python --locked --offline python conformance/production_decay/review_oracle.py --compare docs/verification/production-decay-python.json docs/verification/production-decay-julia.json` | PASS; existing 160 computations still agree at 70 digits |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository and links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| Baseline byte comparison with `66be371` for catalog/schema, both evaluators, saved numerical reports, `spec`, `packages` and existing conformance catalogs/tools | PASS; unchanged |
| Ruby standard-library CI YAML parse; `git diff --check`; `git diff --cached --check` | PASS |
| Hosted follow-up CI and human PI fixture acceptance | NOT RUN locally / pending |

The existing Python CI job now runs the retained rational audit as well as its
tests. No fixtures or numerical evaluator reports were regenerated. The catalog
remains REVIEW_REQUIRED, issue #15 remains open, and P04 remains separate.


## Human PI acceptance recorded

On **2026-11-14**, the repository user, acting as human PI, explicitly accepted
the reviewed issue #15 oracle on PR
[#54](https://github.com/DRAGGON-Lab/FENIX/pull/54):

> Ok, I reviewed it and accept it, please record that desicion and make a final push with that before I merge the PR

Approval source: this Codex conversation; no public approval URL or separate
personal name was supplied. Reviewed revision:
[`1982357b3deed88e8e0cd8f745effd5c3bd960b3`](https://github.com/DRAGGON-Lab/FENIX/commit/1982357b3deed88e8e0cd8f745effd5c3bd960b3).
The reviewed source fingerprint is
`e8e994304de37c01681ca3884d00d3efe90e2c41854bd0228e0839c124f68985`;
the reviewed catalog SHA-256 is
`ccf91c358d0a34eb793942e23790e539360bbb658489d4f91563f11d36b5dac2`.

**Decision: ACCEPTED.** This approves the concrete bounded production–decay
mathematical oracle, its derivation, 40 numerical reference samples, independent
Python/Julia evaluators and retained rational audit. The catalog now records
APPROVED. The draft error budget remains a reference-artifact budget; acceptance
does not ratify P04 numerical solver thresholds or failure policy, SSA eligibility,
native compiler/solver implementations or empirical predictive validity.
No PR is merged or issue closed by this record; the user will merge PR #54.

Only approval metadata, status handling and current-status documentation change.
The catalog schema/runners support REVIEW_REQUIRED and APPROVED artifacts;
unknown status remains a tested rejection. CLI/comparison status output follows
the loaded catalog. Numerical formulas, input encodings, units and all 50-digit
expectations are unchanged. Both native reports were executed again to refresh
catalog/evaluator checksums; all 160 computation rows are exactly equal to the
reviewed revision. The comparison still agrees at 70 significant digits.

Approval-record source fingerprint:
`124cb9852d3c8f141fda7515aa7a2eeb2ebc882cabee001c04c6c697238bbef4`.
Algorithm: sorted repository-relative path + NUL + bytes + NUL SHA-256 over
nine non-cache files under `conformance/production_decay/`, plus the four
CI/documentation paths in the earlier fingerprint and `docs/approved-decisions.md`
(14 files). This evidence record and report artifacts are excluded.
Verification ran dirty on reviewed revision `1982357`, with the same locked
runtime/cache settings documented above.

| Current artifact | SHA-256 |
|---|---|
| Catalog (status metadata changed only) | `468c05a59fc23106dfc2e9e3454e9709ef0b61c9e130885180ecd4e67a07406d` |
| Python report (all computation rows unchanged) | `a29f92938d6f466749d0531869c2aa9f29a243561f4635372c351fcdfee7d37e` |
| Julia report (all computation rows unchanged) | `8ba294073831ed75925e9d4615cc0cbdc05e37a018eb591b5fd468f0f60dfc1d` |

| Command/check | Acceptance-record result |
|---|---|
| Python oracle report command recorded above | PASS; 80 unchanged computations |
| Julia oracle report command recorded above | PASS; 80 unchanged computations |
| Python cross-language comparison command recorded above | PASS; 40 samples / 160 computations, fixture_status APPROVED |
| Python production-decay unittest command recorded above | PASS; 16 tests |
| Julia production-decay test command recorded above | PASS; 648 assertions |
| Rational auditor command recorded above | PASS; all 40 approved samples |
| Repository/link checker and harness unittest commands recorded above | PASS; repository/links and 6 harness tests |
| Python and Julia package smoke commands recorded above | PASS; 2 assertions/tests each |
| Structured baseline comparison with `1982357` | PASS; only catalog status changed; native report computation rows unchanged |
| `git diff --exit-code 1982357 -- spec packages conformance/bioir conformance/python conformance/julia conformance/canonicalization` | PASS; existing contracts, packages and unrelated catalogs/tools unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| Hosted checks for the final approval-record commit | NOT RUN locally; checked separately in GitHub |

Scientific acceptance follows the explicit human instruction above, independently
of automated check results. Earlier pending gates for P01/P03 and future execution
contracts remain separate from this oracle acceptance.
