# FENIX

**Biomolecular and collective computation** — independently implemented native Python and Julia scientific libraries governed by shared language-neutral biological and mathematical contracts.

**Status:** Architecture v0.1 approved (29 decisions); repository scaffold only. **No biological modeling APIs, normative BioIR/FIR schemas or numerical solvers are implemented.**

## Concept

- **BioIR Design:** immutable versioned biological constructs and hierarchies.
- **BioIR Experiment:** versioned contexts, exact design revision references, interventions and observations.
- **FIR:** immutable, backend-independent resolved mathematics. Python and Julia must independently compile the same canonical FIR payload and SHA-256 digest.
- **Execution:** SciPy and direct SciML ODE first; restricted direct SSA later, with explicit capability checks.
- **Evidence:** independent mathematical references, cross-language conformance, automatic provenance. Agreement alone does not prove biological validity.

Read [PRODUCT.md](PRODUCT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AGENTS.md](AGENTS.md), [AGENT.md](AGENT.md) and [approved decisions](docs/approved-decisions.md).

## Repository map

`packages/python` and `packages/julia`: independently installable scaffold packages; `spec/`: reserved for ratified BioIR, FIR and canonicalization contracts; `conformance/`: independent scientific fixtures; `examples/`: verified examples; `.github/`: independent package smoke CI.

## Development and smoke tests

Python 3.12+:

```sh
python -m pip install --no-deps -e packages/python
python -m unittest discover -s packages/python/tests -v
```

Julia 1.10+:

```sh
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
```

**Tests only verify packaging/imports. They do not establish scientific correctness.** The language packages do not depend on each other. No Docker Compose, service backend or GUI is required for this library; any future container workflows require a specific reproducibility need.

## Delivery

- **M-1:** Ratified schemas, canonicalization ADR and independently reviewed reference fixtures.
- **M0:** Portable production/decay: both native compilers, identical FIR bytes/hash and analytically verified ODE.
- **M1:** Two-strain sender/receiver signaling and conservation.
- **M2:** Restricted direct SSA with statistical validation.
- **Stable core:** Supported-profile conformance, provenance, docs and independent installation.

Work in small reviewed PRs. **Scientific semantic changes, units, schemas, canonical hashes and golden references require human PI approval.** LOICA 2 is historical reference, not a compatibility target.

License: MIT.
