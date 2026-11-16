# Proposed M0 results and run manifests

[ADR-P07](proposals/ADR-P07.md) proposes source-linked successful ODE records for
[#22](https://github.com/DRAGGON-Lab/FENIX/issues/22), following merged
[PR #63](https://github.com/DRAGGON-Lab/FENIX/pull/63).
**PROPOSED: explicit human-PI ratification is required before implementation.**

The candidate schemas describe structure. The ADR additionally defines raw JSON,
binary64, source correspondence and cross-artifact checks. The
[examples](proposals/examples/README.md) and
[independent audit](proposals/review_p07.py) are review evidence, not execution
receipts or approved golden fixtures. See the
[verification record](../../docs/verification/ep02-p07-proposal.md).

The [refinement record](../../docs/verification/ep02-p07-refinements.md) covers
the revised language-neutral core/backend boundary, nullable producer build ID
and multi-observable column-order candidate. Ratification of the revised
contract remains pending; no native runtime implementation is included.
