# FENIX coding agent instructions

**Scope:** entire repository. More specific AGENTS.md files may add local constraints.

## Mandatory reading before coding

1. PRODUCT.md, ARCHITECTURE.md and docs/approved-decisions.md.
2. ADR-001.md, then any ratified ADR relevant to the issue.
3. Existing code, actual dependencies, tests and the scoped issue.

**Important:** This is initially a packaging/governance scaffold. No BioIR/FIR contract, numerical API or independently verified mathematical golden fixture has been implemented.

## Non-negotiable scientific rules

- Normative authority belongs to approved, *language-neutral* BioIR/FIR specifications and independently reviewed mathematical references—not Python, Julia or historical LOICA source.
- BioIR Design and Experiment are separate documents; experiments reference immutable exact design revisions.
- FIR is immutable, backend-independent and mathematically semantic. Its digest is SHA-256 of a FENIX-normalized RFC 8785/JCS payload **once normalization rules are ratified**.
- Time seconds; volume litres; count-space molecular states; intracellular ODE expected count **per representative cell**, extracellular count **total**.
- FIR includes deterministic and explicitly supported stochastic semantics, with capability validation. No inferred SSA propensity, implicit unit conversion, silent fallback or untrusted executable serialized callbacks.
- Never change equations, biological assumptions, units, canonicalization, schema, supported profile, model identity or reviewed golden fixtures without a written **human-PI-approved scientific ADR**.
- Never regenerate independent oracle expectations using solely the implementation under test. Do not weaken tests to force CI green.
- Cross-language agreement is not proof of mathematics or empirical biological validity.

## Engineering rules

- **One issue, one small branch, one focused PR**. Never push directly to main or auto-merge; avoid broad rewrites, unrelated refactors and unrequested scope.
- Keep both packages installable **without the other language**. Do not impose mandatory Catalyst, standards adapters, GUI/server/database, Docker Compose or optimizer dependencies.
- Add positive and negative tests for all nontrivial changes, update docs, and report *exactly* which checks passed, failed or were not run.
- Describe scientific units, assumptions, independent reference and numerical tolerances for mathematical changes.
- Avoid eval of untrusted biological models, secrets in repo, silent environment-dependent behavior and uncontrolled input execution.
- Shared normative specs/fixtures are **single-writer human-reviewed**; implementation agents may work in parallel only after reference contract approval.

## When blocked

Stop before inventing a scientific rule. State the precise ambiguity, options, consequences and proposed ADR/independent fixtures. Return to ChatGPT for re-planning and PI approval for normative decisions.

## PR report

Issue and contract references; changes by file; positive/negative tests with commands and results; scientific evidence; dependency/version impacts; known limitations; ADR and reviewer-signoff status. **Scaffold smoke tests do not count as scientific conformance.**

See AGENT.md for planning/implementation responsibilities and package-specific AGENTS.md for local rules.
