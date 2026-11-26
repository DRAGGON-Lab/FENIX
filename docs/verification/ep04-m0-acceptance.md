# EP-04 bounded M0 parent acceptance — 2026-11-26

**Decision: ACCEPTED by the human PI for [EP-04 / issue #6](https://github.com/DRAGGON-Lab/FENIX/issues/6).**

The PI explicitly selected the following response in this Codex conversation:

> Accept bounded M0 EP-04

The question identified the existing bounded M0 profile and the already accepted
child issues #28–#30 as the acceptance scope. It explicitly stated that this is
parent-level PI acceptance only and that PRs #81/#82 remain separate review
items. This record transcribes that human decision; it does not infer acceptance
from CI, an agent review, an issue state or a merge.

## Accepted baseline and child evidence

The decision applies to the bounded M0 profile available on `main` at
`0670cf35d7791e610b4e7c3931a720e9109532ad`. That tree contains the accepted native
M0 implementations and child evidence below, as well as separately scoped
candidate M1 work. The parent decision accepts the M0 profile only.

| Child | Inspected state at acceptance | Evidence |
| --- | --- | --- |
| [#28 — native FIR conformance](https://github.com/DRAGGON-Lab/FENIX/issues/28) | Closed as completed; PR #73 merged | [Native FIR receipt](ep04-native-fir.md), independent reference validation and Python–Julia canonical byte/identity comparison |
| [#29 — native ODE scientific gate](https://github.com/DRAGGON-Lab/FENIX/issues/29) | Closed as completed; PI acceptance recorded; PR #74 merged | [Scientific acceptance](ep04-native-ode.md#human-pi-scientific-acceptance--2026-11-18) at `f35bd609cdcef46fc6d86d7cdecf352593abbba0`, unchanged P04 reference/pairwise bounds and retained CI evidence |
| [#30 — repository alpha](https://github.com/DRAGGON-Lab/FENIX/issues/30) | Closed as completed; bounded alpha accepted; PRs #75/#76 merged | [Accepted profile and checklist](m0-alpha/README.md), reviewed candidate `566ba94bf1814fdf7bcae10db4ebcbf8688a3b53`, independent installs, executable examples and benchmark receipts |

This completes the parent acceptance gate for the existing M0 production/decay
profile: separate immutable sources, canonical FIR identity, approved deterministic
ODE methods, source-linked results/readback, independent numerical references and
language-only installation evidence. Bounds and scope remain those of the
accepted child records. Historical pending-acceptance observations remain intact
as receipts of their original observation times.

## Separate follow-up reviews and limits

[PR #81](https://github.com/DRAGGON-Lab/FENIX/pull/81) adds issue #59's generated
interaction checks and replayable examples; [PR #82](https://github.com/DRAGGON-Lab/FENIX/pull/82)
adds M0 source-revision/capture/readback workflows. Both remain separate review
items. At this decision, #81's 19 checks and #82's 18 checks passed; their combined
local Python integration checks also passed. Those observations strengthen the
bounded regression evidence but do not turn this parent decision into approval
or merge authorization for either PR.

M1 independent reference acceptance and remaining wire/numerical gates, SSA,
P06 compatibility/version governance, stronger provenance, registry publication,
release tags and broader releases retain their own decisions. This acceptance
establishes neither exhaustive input/numerical coverage, authenticated execution
nor biological predictive validity. The PI's deferred branch-protection policy
is unchanged. Refs #6.
