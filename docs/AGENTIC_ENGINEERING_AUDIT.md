# FENIX agentic engineering audit

**Reviewed:** 2026-11-14. **Evidence:** files on the `main` branch from the initial scaffold and current official Anthropic Claude Code and OpenAI Codex guidance. This is a repository-harness audit, not a BioIR/FIR mathematical review.

## Findings and changes

| Finding in original scaffold | Impact | Corrective action | Status |
|---|---|---|---|
| Root `AGENT.md` and `AGENTS.md` repeated planning/agent instructions | Confusing document authority, instruction drift | Move human workflow to `docs/DEVELOPMENT_WORKFLOW.md`; keep `AGENTS.md` as coding-agent source | Addressed in PR |
| Claude Code compatibility not explained | Contributors may create a separate inconsistent `CLAUDE.md` | Document that modern Claude Code can read `AGENTS.md` directly; preserve nested scoping | Addressed in PR |
| Root agent policy lacked copy/paste verification commands | Agents had no single concrete evidence loop | Add root preflight and commands and offline harness tests | Addressed in PR |
| Package-specific guidance existed but no explicitly scoped review rules | Risk of overlooking biological or cross-language contract changes | Add targeted review rules to root/spec/package `AGENTS.md` | Addressed in PR |
| CI only checked Python and Julia imports | Documentation/agent policy regressions undetected | Add `Repository harness` job with standalone stdlib tests and link checks | Addressed in PR |
| No structured issue intake for normative scientific changes | Unapproved scientific assumptions can enter implementation tasks | Add separate implementation and scientific-contract templates | Addressed in PR |
| Human PI review was stated only in Markdown | GitHub can still merge without required scientific reviewer | Document necessary GitHub rulesets and CODEOWNERS; do not invent reviewers | **Requires maintainer configuration** |
| Mathematical semantics and reference fixtures remain unratified | Cannot prove biological correctness or parity | ADR-P01/P02/P03 and independent fixtures remain blockers | **Intentionally unresolved** |

## Official sources and how they inform this change

- [OpenAI: AGENTS.md discovery and nested instructions](https://learn.chatgpt.com/docs/agent-configuration/agents-md) — keep root-to-directory agent policy.
- [OpenAI: Custom code review rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex) — a small number of consequential, scoped invariants with safe paths; deterministic checks belong in CI.
- [OpenAI: Iterating development workflows with Codex](https://developers.openai.com/cookbook/examples/codex/iterating-development-workflows-with-codex) — preflight, finite scope, tests, observed evidence and review handoffs; other harness documents are optional conventions.
- [Anthropic: Claude Code memory / AGENTS.md](https://code.claude.com/docs/en/memory) — recent Claude Code versions read AGENTS.md directly, including directory-specific files, unless overridden by CLAUDE.md; avoid duplicate instruction manuals.
- [Anthropic: Claude Code best practices](https://code.claude.com/docs/en/best-practices) — short context, executable checks, and external enforcement for non-negotiable safeguards.

## Architectural assessment

**Preserved:** Separate BioIR Design and Experiment; one canonical backend-independent FIR; mathematical assumptions, units and scientific contracts requiring independent validation; Python and Julia independent installation; M-1/M0/M1/M2 gates.

**Not claimed:** Scientific solver correctness, cross-language model parity, full empirical reproducibility, a required GitHub reviewer, or an activated CODEOWNERS branch rule. None can be established from scaffold-level smoke tests.

## Recommended next gates

1. Merge only when harness, Python and Julia jobs pass, and confirm human review.
2. Configure protected `main` and determine the actual scientific CODEOWNERS identity/team.
3. Ratify ADR-P01 BioIR schema, P02 FIR/capabilities, P03 JCS/numeric canonicalization with independent references **before** compiler implementation.
4. Add deeper conformance CI as the scientific feature surface emerges.
