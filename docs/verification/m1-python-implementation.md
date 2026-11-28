# Native Python bounded M1 implementation — #32

Implementation review candidate based on accepted main `cf2ecbaf558b4843dbaa7d4467b2888e1b389e69`.
The [PI decision](m1-executable-acceptance.md) accepts the bounded specification,
references and numerical criteria; it does not approve this native implementation.
Refs #32. Julia #33, independent integration #35 and final EP-05 acceptance remain
separate. No issue closure, package publication or biological validity is claimed.

## Scope and behavior

`fenix.community` provides immutable Design/Experiment authoring and strict raw
parsing, source-verified FIR compilation and exact 0.2.0 identity, coupled SciPy
DOP853/Radau integration, scoped results/manifests and non-executing readback.
Sources are explicit local inputs. Four packaged schemas copy the accepted bytes;
the bounded validator interprets only their closed grammar and never resolves an
external schema. The package imports neither repository/reference tools nor Julia
and adds no runtime dependency. M0 code, accepted specifications, all 307 packet
artifacts and dependency locks are unchanged.

Capture validates user metadata, compiles once and solves once. Readback verifies
exact local source correspondence and recompiles without solving; it preserves
original bytes, signed-zero grids/copies, exact counters and opaque runtime fields.
Model identity includes resolved counts, rates, populations and geometry while
excluding provenance. Canonical wire columns are `env.signal, receiver.reporter,
receiver.signal, sender.signal`; independent references use `sender.signal,
receiver.signal, env.signal, receiver.reporter`. Every comparison maps by ID.

The coupled kernel implements the ratified per-cell and total-count bases,
read-only Hill sensing and population-weighted medium balance. Radau receives
its full exact state-dependent Jacobian. Strict negative sensing stages,
nonfinite arithmetic, work exhaustion and incomplete/negative output fail;
there is no clipping, fallback or analytical substitution. Zero-only grids
validate then skip integration. Finite valid inputs can still fail numerically.

Non-goals: Julia delivery, cross-language integration acceptance, oscillator,
SSA, growth, general expression ASTs, migration, exhaustive generated inputs,
authenticated execution and universal integration success.

## Executed evidence

Exact commands, timestamps, source and artifact hashes, outcomes and retained
logs are in the [receipt](m1-python-implementation.json). Local Python is 3.12.13,
uv 0.11.29, NumPy 2.5.5 and SciPy 1.18.1.

- Native fixtures: all 14 positive packets, 56 declared diagnostic rejections,
  17 lexical projections, 10 binary64/counter projections and 6 grid witnesses.
  Positive records include both backend wire formats; only SciPy executes here.
- Native numerical comparison: ten analytical cases, two methods, baseline and
  refined controls, 40 integrations/120 four-state sample comparisons against
  independent 160-digit Decimal laws. Closed balance uses accepted weights
  `(N_s,N_r,1,0)`, component bounds `1e-9+1e-8|reference|` and the weighted initial
  representation discrepancy. A nonzero binary64 `0.1` control protects that term.
- Asymmetric high-precision RHS/Jacobian differentiation for exponents 1–4 and
  zero/below/at/above threshold; strict tails, budgets, corrupted backend output,
  zero/late-first grids, empty observables, source immutability and revisions,
  compile/solve-once capture, offline readback and trusted checksum rejection.
- Existing M0 package tests and native content/document/FIR projections;
  repository checker/harness, style/format and strict mypy over 20 source files.
- Independent engineering review compared the finite validator with Draft7 over
  4,554 bounded scalar mutations, with no acceptance differences. This comparison
  covers schema structure, not complete source semantics or exhaustive inputs.
- Clean wheel: runtime-only install and native/M0 tests; verification distinguishes
  install-time network access from offline library execution. No Julia,
  jsonschema, mypy or other development package is required by the library.

The frozen numerical settings are baseline `rtol=1e-9, atol=1e-11`, refined
`rtol=1e-11, atol=1e-13`, maximum step 1 second and 200000 RHS calls. Tail
observations extend driven-n1 to 1000 seconds with maximum step 10 seconds;
explicit failures retain their accepted meaning. No scientific expectation or
bound was changed to obtain a passing native result.

## Independent review dispositions

The root agent owns implementation and evidence. Separate engineering and
numerical reviewers assessed the code without rewriting accepted expectations.
Their confirmed findings were repaired before final verification:

| Finding | Trigger / impact | Repair and control |
|---|---|---|
| Low: raw Unicode encoding error | Malformed result/manifest Python strings leaked UnicodeEncodeError before typed decoding. | Catch encoding failures as CommunityValidationError UNICODE; both readback inputs tested. |
| Medium: nonfinite Jacobian intermediate | `K=V_e=1e308`, n=1, E=0 silently turned overflowing `K*V_e` into a zero derivative. | Check finite nonzero denominator before reciprocal; Radau rejects explicitly, while zero-only skip remains valid. |
| Evidence gap: initial representation term | Frozen integer initials made the omitted discrepancy invisible in the initial test formula. | Explicit represented/reference initial difference plus an exact nonzero binary64 control; accepted bound retained. |

No unresolved blocking findings were reported in the reviewed scope. Historical
reviewer snapshots remain snapshots; final source fingerprints and executed
checks are recorded separately. Agent review and local tests do not substitute
for required human review, final CI or independent #35 conformance.
