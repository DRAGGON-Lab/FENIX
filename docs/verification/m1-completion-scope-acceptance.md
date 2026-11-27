# M1 bounded completion-scope approval — 2026-11-27

The human PI approved the [P08 execution-feasibility proposal](../../spec/community/execution-feasibility-proposal.md)
on [PR #94](https://github.com/DRAGGON-Lab/FENIX/pull/94) at reviewed revision
`6964014efd9e869bc98337eb3cece3c6ea837f1b` in this Codex conversation:

> I approve this proposal please record the desicion and update the PR

This records approval of the proposal's recommended **alternative 1**: retain
strict sensing-stage domain rejection and state the bounded completion scope
explicitly. A mathematically valid request may fail with a stage-domain
diagnostic. No clipping, signed sensing continuation, method substitution or
universal integration-success guarantee is authorized. Broader completion
requirements would need a separately investigated contract.

The retained SciPy investigation supports this decision: the bounded matrix
passes 40 integrations / 120 four-state sample comparisons, while both methods
at both settings reject negative sensing stages in the long-tail control despite
a strictly positive analytical extracellular count. The proposed state bound is
retained for the full packet; conservation bounds include population weights
and initial representation error. This decision does not turn those candidate
controls into an accepted native tolerance or a complete executable profile.

## Exact reviewed artifacts

SHA-256 values computed before recording approval, from the unchanged reviewed
files at the revision above:

| Artifact | SHA-256 |
|---|---|
| `spec/community/execution-feasibility-proposal.md` | `0a92481d59b1bed651da51cad5ae58fd4a4cfd79577de3ca8ddf075dfc7c4680` |
| `conformance/community/feasibility/settings.json` | `a39091f231a5b101c1e430d53eec6327e337b0e3f04a2870473bcfbc64ef3fc8` |
| `conformance/community/feasibility/scipy-receipt.json` | `84c00e7c0087a611a9bb0c8bdc3f686b34af22b2d9c0ec0351f83b1d39d4bfc3` |

The proposal's status and decision text are updated by this approval-recording
change. The immutable reviewed revision preserves its original wording and
hash. Probe, settings, reference definitions, tests and numerical receipt bytes
remain unchanged. Historical PROPOSED labels in that receipt retain their
original meaning; approval is recorded here, not retroactively inserted into
observed output.

## Remaining gates

The complete M1 wire/result/backend contracts, independent identity and rejection
catalogs, exact ten-case/30-sample reference acceptance, Julia method feasibility
and full numerical-profile acceptance remain separate. Native #32/#33,
integration #35, epic #7 acceptance and downstream #84 native work remain gated.
This decision supplies no implementation acceptance, empirical validation,
issue closure, merge or package publication authorization.

The [verification record](m1-stage-feasibility.md) retains the local checks and
runtime limitations. Explicit PI approval supplies this decision; CI and agent
review do not substitute for it.

Approval-recording verification: **PASS** — offline repository checker, six
repository harness tests, nine feasibility tests (including retained-receipt
fingerprints), and `git diff --check`. Native package suites were **NOT RUN
again** for this documentation-only update; their prior outcomes remain in the
verification record. Julia stage feasibility remains **NOT RUN**.
