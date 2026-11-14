# FENIX coding-agent instructions

These instructions apply repository-wide. More specific `AGENTS.md` files in `packages/` and `spec/` add scoped requirements.

## First read and source of truth

- Read the issue, changed files and relevant tests. Consult [PRODUCT.md](PRODUCT.md) for scope, [ARCHITECTURE.md](ARCHITECTURE.md) for boundaries, [approved decisions](docs/approved-decisions.md) and ratified ADRs for scientific rules.
- For orchestration, review, role handoffs, and verification commands see [development workflow](docs/DEVELOPMENT_WORKFLOW.md).
- This is a **scaffold**, not a scientific library: ADR-P01, ADR-P02 and ADR-P03 ratify only the M0-compatible BioIR, mathematical FIR and canonicalization contracts. Independent golden references and implementation approval remain pending; do not silently invent them. Honor P01's fixture-catalog gate before parser/validator implementation approval.
- Ratified **language-neutral specifications and independent mathematical oracles** govern science, never Python, Julia, or LOICA source alone.

## Execution contract

1. Work on one approved, issue-sized task. Name non-goals and affected files. Make a short plan before substantive edits.
2. Read scoped `AGENTS.md` files in the affected directory; honor scientific contract gates.
3. Make small, idiomatic changes; write positive and negative tests and update affected docs. Keep both language packages independently installable.
4. Run the precise applicable commands from [development workflow](docs/DEVELOPMENT_WORKFLOW.md). Record **PASS / FAIL / NOT RUN** accurately.
5. Open a focused PR for human review. Do not commit directly to `main`, auto-merge, publish a package or introduce mandatory services as a convenience.

## Scientific red lines

- Changes to BioIR/FIR mathematical semantics, units, parameter meaning, stochastic propensity rules, canonical bytes/digests, capability declarations or approved golden fixtures require a **human-PI-ratified ADR first**.
- Never regenerate golden values solely from the implementation under test or weaken a scientific test to make CI green.
- Preserve separate immutable BioIR Design and Experiment documents and one backend-independent mathematical FIR. FIR identity excludes provenance; ODE and supported SSA behavior share FIR identity but differ by execution profiles.
- Canonical time seconds, volumes litres and molecular count-space; intracellular expected counts per representative cell, extracellular total counts. Reject implicit conversions and unsupported profiles.
- No `eval`, dynamically executable serialized callbacks, hidden network dependencies, credentials or untrusted dataset disclosure. Statistical SSA agreement does not imply identical random trajectories. Cross-language parity does not prove biological validity.

## Escalate rather than guess

If scientific definitions, numeric edge behavior, references, dependencies or requirements are unclear, **stop before implementing the semantic change**. State the uncertainty, alternatives, impact, proposed ADR/independent test and the human approval needed. This is a blocking review gate, not an invitation to fill gaps by inference.

**This file is for coding-agent behavior.** Human/ChatGPT/agent coordination belongs in `docs/DEVELOPMENT_WORKFLOW.md`; avoid creating a separate copy of these rules.
