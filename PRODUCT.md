# FENIX product brief

**Vision:** Portable, reproducible programmatic biomolecular and collective cellular computation with independent Python and Julia authoring and simulation.

## Problem and audiences

Biological design, experiment conditions, executable mathematics and runtime details are often conflated. Researchers cannot reliably compare or exchange models without clear semantics and evidence.

Users: synthetic/computational biologists (design and simulate), tool/library developers (extend native interfaces), and scientific reviewers (audit mathematical claims, units, results and provenance).

## User journeys

1. Build or read a typed biological Design; validate and commit an immutable revision.
2. Define a separate Experiment referencing that exact Design revision.
3. Compile independently in Python or Julia into identical canonical FIR semantics.
4. Choose an explicitly supported execution profile; run; inspect observations, diagnostics and provenance.
5. Later, export SBOL/SBML, bind experimental data, fit parameters, optimize designs and extend simulation through optional modules.

## Goals and success

**M-1:** Ratified semantic/serialization contracts and independent oracle fixtures, plus standalone package harnesses.

**M0:** Production–degradation authored in both languages; equal FIR bytes/digest; ODE solutions match independent analytical references; invalid inputs fail explicitly.

**M1:** Two-strain sender–receiver community, per-cell versus extracellular count accounting and conservation tests.

**M2:** Restricted direct SSA, admissibility and distribution-level statistical tests.

**Stable:** Both native installations, scientific conformance, provenance, docs and capability/version matrix.

Performance is benchmarked before optimization; correctness takes precedence.

## Non-goals

No LOICA 2 migration/API compatibility; no GUI/server/database; no required standards or Catalyst dependencies; no mandatory hybrid/spatial/agent simulations; no initial auto-differentiation, inference or circuit optimization; no unsupported claim of empirical prediction.

**Current status:** Python implements the ratified M0 production–degradation path: typed content authoring, verified committed Design/Experiment documents, native FIR compilation and P03 identity, SciPy DOP853/Radau execution, and P07 source-linked results/manifests. All five EP-02 child implementation issues (#18–#22) are closed, and PR #65 merged at `32acf4f4b51e257c7efed65203360e5e9ee83598`; [post-merge CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581) passed seven jobs. [EP-02](https://github.com/DRAGGON-Lab/FENIX/issues/4), the bounded native Python M0 implementation milestone, was completed following explicit PI approval on 17 November 2026. Julia M0 uncommitted content builders and validation are now available; Julia committed-document integrity, compilation and native numerical execution, independent cross-language scientific conformance (#28/#29), and broader whole-project release authorization remain separate gates. P06 version governance, stronger provenance/archive work (#42) and generated-input investigation (#59) retain separate scopes. Implementation completion and passing CI do not establish complete M0 or stable-core acceptance, biological validity or authenticated execution. Ratified P01–P04/P07 contracts and bounded PI-accepted reference catalogs remain authoritative; their acceptance does not prove exhaustive native validation or empirical predictive validity. See the [integration/governance audit](docs/verification/ep02-status-governance.md).
