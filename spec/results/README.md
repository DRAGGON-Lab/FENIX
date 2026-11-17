# Ratified M0 results and run manifests

[ADR-P07](proposals/ADR-P07.md) ratifies source-linked successful ODE records for
[#22](https://github.com/DRAGGON-Lab/FENIX/issues/22), following merged
[PR #63](https://github.com/DRAGGON-Lab/FENIX/pull/63).
**RATIFIED by the human PI on 2026-11-16 at reviewed revision `bc662d3`.**
Native implementation and its approval remain separate.

The accepted schemas describe structure. The ADR additionally defines raw JSON,
binary64, source correspondence and cross-artifact checks. The
[examples](proposals/examples/README.md) and
[independent audit](proposals/review_p07.py) supply accepted bounded reference
expectations, not execution receipts or native implementation approval. See the
[verification record](../../docs/verification/ep02-p07-proposal.md).

The [refinement record](../../docs/verification/ep02-p07-refinements.md) covers
the revised language-neutral core/backend boundary, nullable producer build ID
and multi-observable column-order candidate. The
[ratification record](../../docs/verification/ep02-p07-ratification.md) accepts
the reviewed contract, schemas and bounded expectations. Reviewed artifact and
historical receipt bytes retain their drafting-era labels; those labels do not
override this recorded decision. No native runtime implementation is included.

The additive [Julia/SciML supplement](proposals/ADR-P07-Julia.md) for #27 is
**PROPOSED; PI ratification PENDING**. Its separate closed manifest schema reuses
P07's unchanged core and ODEResult layout. Native Julia results implementation
is gated on review and explicit acceptance of the proposal and bounded evidence.
