# FENIX

**Biomolecular and collective computation** — targeting independent native Python and Julia scientific libraries governed by shared language-neutral biological and mathematical contracts.

**Current implementation status:** Python implements the ratified M0 production–degradation path: typed content authoring, verified committed Design/Experiment documents, native FIR compilation and P03 identity, SciPy DOP853/Radau execution, and P07 source-linked results/manifests. All five EP-02 child implementation issues (#18–#22) are closed, and PR #65 merged at `32acf4f4b51e257c7efed65203360e5e9ee83598`; [post-merge CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581) passed seven jobs. [EP-02](https://github.com/DRAGGON-Lab/FENIX/issues/4), the bounded native Python M0 implementation milestone, was completed following explicit PI approval on 17 November 2026. Julia M0 content builders, strict committed Design/Experiment documents, canonical content digests, exact local references and native BioIR-to-FIR compilation with P03 identity are implemented; the human PI accepted the bounded issue #25 implementation at `da13860` on 17 November 2026 (see the [acceptance record](docs/verification/ep03-julia-compiler.md#human-pi-implementation-acceptance--2026-11-17)). Native Julia SciML ODE execution is implemented under P04 with explicit Tsit5/Rodas5P methods; human issue #26 implementation acceptance, Julia results/manifests, independent cross-language scientific conformance (#28/#29), and broader whole-project release authorization remain separate gates. P06 version governance, stronger provenance/archive work (#42) and generated-input investigation (#59) retain separate scopes. Implementation completion and passing CI do not establish complete M0 or stable-core acceptance, biological validity or authenticated execution. See the [maintenance audit](docs/verification/ep02-status-governance.md) and [Python usage](packages/python/README.md).

## Concept

- **BioIR Design:** immutable versioned biological constructs and hierarchies.
- **BioIR Experiment:** versioned contexts, exact design revision references, interventions and observations.
- **FIR:** immutable, backend-independent resolved mathematics. Python and Julia must independently compile the same canonical FIR payload and SHA-256 digest.
- **Execution:** SciPy and direct SciML ODE first; restricted direct SSA later, with explicit capability checks.
- **Evidence:** independent mathematical references, cross-language conformance, automatic provenance. Agreement alone does not prove biological validity.

Read [PRODUCT.md](PRODUCT.md), [ARCHITECTURE.md](ARCHITECTURE.md), [AGENTS.md](AGENTS.md), the [development workflow](docs/DEVELOPMENT_WORKFLOW.md), and [approved decisions](docs/approved-decisions.md). The [agentic engineering audit](docs/AGENTIC_ENGINEERING_AUDIT.md) records the review against current Codex and Claude Code guidance.

## Repository map

`packages/python`: native M0 documents, FIR compiler, ODE execution and source-linked results; `packages/julia`: native M0 BioIR content/documents, FIR compiler and SciML ODE execution; `spec/`: ratified BioIR/FIR subsets and FIR canonicalization contract; `conformance/`: independent scientific fixtures; `examples/`: verified examples; `.github/`: independent package smoke CI.

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
