# FENIX

**Biomolecular and collective computation** — independently implemented native Python and Julia scientific libraries governed by shared language-neutral biological and mathematical contracts.

**Status:** Architecture v0.1 approved (29 decisions); package scaffold with the [ratified ADR-P01 M0-compatible BioIR subset](spec/bioir/README.md), the [ratified ADR-P02 M0 FIR subset](spec/fir/README.md), the [ratified ADR-P03 canonicalization contract](spec/canonicalization/README.md) and [independent P01 reference validators/candidate fixtures](conformance/bioir/README.md) for review. **Python now provides an uncommitted M0 BioIR content API** with typed construction, validation and ordinary JSON serialization; see the [Python package](packages/python/README.md). Python also provides committed envelopes, strict parsing and exact local Design references, pending implementation review. Python now also compiles verified M0 BioIR into validated immutable FIR with P03 normalization and byte/digest conformance, pending implementation review. Python now provides P04 M0 ODE execution via SciPy, pending implementation review. The bounded reference catalogs are PI-approved; native implementation approval remains separate.

## Concept

- **BioIR Design:** immutable versioned biological constructs and hierarchies.
- **BioIR Experiment:** versioned contexts, exact design revision references, interventions and observations.
- **FIR:** immutable, backend-independent resolved mathematics. Python and Julia must independently compile the same canonical FIR payload and SHA-256 digest.
- **Execution:** SciPy and direct SciML ODE first; restricted direct SSA later, with explicit capability checks.
- **Evidence:** independent mathematical references, cross-language conformance, automatic provenance. Agreement alone does not prove biological validity.

Read [PRODUCT.md](PRODUCT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AGENTS.md](AGENTS.md), the [development workflow](docs/DEVELOPMENT_WORKFLOW.md), and [approved decisions](docs/approved-decisions.md). The [agentic engineering audit](docs/AGENTIC_ENGINEERING_AUDIT.md) records the review against current Codex and Claude Code guidance.

## Repository map

`packages/python`: native M0 content API; `packages/julia`: independently installable scaffold; `spec/`: ratified BioIR/FIR subsets and FIR canonicalization contract; `conformance/`: independent scientific fixtures; `examples/`: verified examples; `.github/`: independent package smoke CI.

## Development and smoke tests

Python 3.12+ with [uv](https://docs.astral.sh/uv/) (CI uses uv 0.11.29):

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v
```

Julia 1.10+ with native Pkg; [juliaup](https://github.com/JuliaLang/juliaup) manages runtime versions (CI and reference tooling use 1.10.13):

```sh
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
```

The [Julia reference environment](conformance/julia/README.md) has a committed manifest; the library resolves independently. Python development tools are locked in the package development group. Use `uv add --project packages/python --group dev <tool>` to change them, then commit both the manifest and lockfile.

Run the independent repository-harness checks before creating a PR:

```sh
uv run --project packages/python --locked --offline python scripts/check_repo.py
uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v
```

**These checks and the package smoke tests do not establish scientific correctness.** The language packages do not depend on each other. No Docker Compose, service backend or GUI is required for this library; any future container workflows require a specific reproducibility need.

## Delivery

- **M-1:** Ratified schemas, canonicalization ADR and independently reviewed reference fixtures.
- **M0:** Portable production/decay: both native compilers, identical FIR bytes/hash and analytically verified ODE.
- **M1:** Two-strain sender/receiver signaling and conservation.
- **M2:** Restricted direct SSA with statistical validation.
- **Stable core:** Supported-profile conformance, provenance, docs and independent installation.

Work in small reviewed PRs. **Scientific semantic changes, units, schemas, canonical hashes and golden references require human PI approval.** LOICA 2 is historical reference, not a compatibility target.

License: MIT.
