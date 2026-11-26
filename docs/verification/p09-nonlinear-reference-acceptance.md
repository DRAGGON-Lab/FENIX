# P09 bounded nonlinear-reference acceptance — 2026-11-26

The human PI explicitly accepted the bounded nonlinear numerical reference
definitions on [PR #90](https://github.com/DRAGGON-Lab/FENIX/pull/90) at reviewed
commit `0ee6b4253775aa5379db0c11ff3af566727799cf` in this Codex conversation.
The question identified the two 80,000-second oscillator cases, four-step
refinement protocol and 1e-5 peak-scaled investigation limit. It explicitly
retained certified error bounds, native tolerances, P10 wire contracts and native
implementation approval as separate. The PI selected:

> Accept bounded nonlinear references

That explicit instruction supplies acceptance. Solver agreement, CI and agent
review do not supply it; no independent human recomputation is claimed.

## Accepted scope and reviewed artifacts

Acceptance covers the exact two primary case definitions and their bounded
independent numerical study at the reviewed revision:

- The six-state single-cell and 18-state three-strain illustrative primary
  definitions, including their exact initial counts, rates, populations, volumes,
  units and bases in `conformance/oscillators/cases.json`.
- The independently derived density-coordinate RHS and fixed-step classical
  RK4 calculation, checked against the separately accepted component laws.
- The full 80,000-second horizon, five-second output grid and steps 2.5, 1.25,
  0.625 and 0.3125 seconds for each primary case.
- Successively decreasing maximum amplitude-scaled refinement gaps, a final gap
  at most 1e-5, and comparisons of the eight adaptive traces against the finest
  independent trace at that same investigation limit. Per-state scale is
  max(1, peak absolute reference count) over the complete trace.
- Independently reported midpoint upcrossings/extrema as observations, with no
  new sustained-oscillation classifier or native acceptance tolerance implied.

The agent recomputed these SHA-256 values from the reviewed Git blobs:

| Artifact | SHA-256 |
|---|---|
| `conformance/oscillators/cases.json` | `70932f56c47cddb7fd502b165580c65f8a34431721972fbf11a2588ab5c15d25` |
| `conformance/oscillators/nonlinear/rk4.py` | `686a3755e223c7f527215bef57e8b3f3eafa214a7da788b68f29e316c3205e34` |
| `conformance/oscillators/nonlinear/test_rk4.py` | `6dbd1bc8a020970c4083428fff622acf39c5c6f92e22a2bf28bbb62b050149cf` |
| `conformance/oscillators/uv.lock` | `0a067b5cca371843bbaf3f9f58725194f30f98fbff6b8f40a21a8b356341bf53` |

The complete raw catalog pin protects all input definitions. This follow-up
preserves every catalog, evaluator, test, comparison, workflow and lock byte;
historical PROPOSED labels in the reviewed snapshot/generated reports retain
their original meaning. This subsequent explicit decision governs the scope
above. It does not approve the feasibility classifier's thresholds as native
criteria, negative controls as new golden fixtures, or all possible inputs.

## Verification evidence and limitations

The reviewed revision's
[hosted numerical-study job](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45906236546/job/140203529007)
is **PASS**, including all 414 analytical component state/time comparisons,
four fixed-step runs per model, and 1,536,096 comparisons against the adaptive
trajectories. Its sibling
[Decimal/BigFloat job](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45906236546/job/140203529349)
also passed. These jobs are evidence distinct from the human decision.

The agent downloaded `proposed-repressilator-study` from that run and verified
source/catalog/lock/input-report fingerprints and all nineteen primary/control/
RK4 trace checksums. Every per-state refinement and adaptive comparison row was
recomputed from the downloaded CSVs. Hosted maximum peak-scaled discrepancies
were approximately 7.526e-8 single-cell and 3.590e-9 community. Observed orders
were 2.864 then 3.761 in the single cell and 4.074 then 4.045 in the community;
the coarsest single-cell pair is not fully asymptotic. Source/input fingerprints
match the exact reviewed bytes above. Hashes bind artifacts to reports; they do
not authenticate execution.

The local complete study and seven new control tests passed at the reviewed
revision, alongside the existing fourteen study controls, nine analytical/
comparison controls, 88 Python package tests and repository/harness checks.
The RK4 driver imports neither FENIX nor SciPy nor the original RHS/Jacobian/
classifier. Both numerical calculations still share binary64, NumPy and model
definitions. Decreasing step differences and algorithm agreement do not certify
exact-solution error, eliminate shared errors or establish biological validity.

Julia is **NOT RUN locally** (runtime unavailable). Hosted native FIR/ODE and
isolated installation gates retain their own observed status and do not grant
oscillator support. Native oscillator execution remains **NOT RUN — unsupported
profile**. Complete wire/schema/identity/rejection evidence, exact native
reference mapping and tolerances, native Python/Julia implementations and their
scientific acceptance remain required. M0 and M1 obligations are preserved.
No merge, release or issue #84 completion follows from this acceptance.
