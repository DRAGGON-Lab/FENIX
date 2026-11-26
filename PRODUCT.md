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

**Current implementation status:** Both independently installable packages implement the bounded M0 production–degradation path: immutable BioIR documents, native FIR compilation and P03 identity, native ODE execution, and P07 source-linked results/manifests. Python uses SciPy DOP853/Radau; Julia uses SciML Tsit5/Rodas5P. The independent native FIR gate (#28, PR #73) and PI-accepted ODE scientific gate (#29, PR #74) are merged. These gates cover approved references, not exhaustive validation or biological validity. The [bounded M0 repository alpha](docs/verification/m0-alpha/README.md) adds executable examples, installation proofs and benchmark receipts; the PI accepted this bounded repository alpha at revision `566ba94`. P06 version governance, registry publication, stronger provenance (#42) and generated-input investigation (#59) remain separate.