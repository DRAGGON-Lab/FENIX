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

**Current status:** Skeleton packages and the ratified ADR-P01 BioIR, ADR-P02 mathematical FIR M0 subset schemas and ADR-P03 canonicalization contract. Python has an [uncommitted M0 BioIR content API](packages/python/README.md) for typed construction, validation and ordinary JSON serialization, pending implementation review. Python also provides committed documents, strict parsing and exact local Design references, pending implementation review; Python M0 FIR compilation, validation and P03 normalization/identity are also available, pending implementation review; Python now provides P04 M0 ODE execution via SciPy, pending implementation review. The human PI accepted the bounded [canonicalization reference vectors](docs/verification/ep01-canonicalization-vectors.md#human-pi-acceptance-recorded); the bounded [BioIR/FIR rejection reference suite](docs/verification/ep01-rejections.md#human-pi-acceptance-recorded) is also accepted, with explicitly non-exhaustive negative capability coverage. The [92 P01 reference expectations](docs/verification/ep01-p01-reference.md#human-pi-acceptance-recorded) are accepted, while native implementations, exhaustive validation, compiler/solver correctness and future BioIR semantics remain outside that approval. Native parser/normalizer implementation approval remains separate. Parser/validator implementation approval requires the reviewed language-neutral fixture catalog and independent Python/Julia reports. Remaining exact contracts require scientific ADR approval.
