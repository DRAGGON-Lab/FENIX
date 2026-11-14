# FENIX development workflow

**Audience:** maintainers, human reviewers, ChatGPT, Codex and Claude Code.
**Scope:** process; scientific requirements live in [PRODUCT.md](../PRODUCT.md), [ARCHITECTURE.md](../ARCHITECTURE.md), [approved decisions](approved-decisions.md) and ratified specifications.

## One instruction source across coding agents

- Root [AGENTS.md](../AGENTS.md) is the durable, concise coding-agent policy. Package-specific and specification-specific `AGENTS.md` files add narrowly scoped constraints.
- Current OpenAI Codex reads applicable `AGENTS.md` files from root toward the working directory.
- Claude Code v2.1.277+ also reads `AGENTS.md` directly when a `CLAUDE.md` or `CLAUDE.local.md` does not supersede it. The repository deliberately does **not** commit a separate `CLAUDE.md`, because the modern shared-file path is simpler and preserves nested `AGENTS.md` discovery.
- For older Claude Code versions, upgrade where possible. A local `CLAUDE.md` containing `@AGENTS.md` is a fallback, but note that a root `CLAUDE.md` can affect automatic discovery of deeper `AGENTS.md`. Check `/context all` and read scoped files explicitly. Do not maintain a second divergent instruction manual.
- The former `AGENT.md` was retired: this document owns collaboration process; `AGENTS.md` owns implementation rules.

Source references: [Claude Code memory and AGENTS.md discovery](https://code.claude.com/docs/en/memory), [Claude Code engineering guidance](https://code.claude.com/docs/en/best-practices), [Codex AGENTS.md discovery](https://learn.chatgpt.com/docs/agent-configuration/agents-md), [Codex review rules](https://developers.openai.com/blog/custom-code-review-rules-for-codex).

## Responsibilities

| Role | Accountable outcome | May not self-authorize |
|---|---|---|
| Human PI / scientific maintainer | Accept scientific contracts, mathematical oracles, scientific claims and normative compatibility changes | Waiving required evidence without a documented decision |
| ChatGPT / design lead | Resolve ambiguity, compare options, prepare scope and ADR proposals, review implementation against approved decisions | Treating generated material as experimentally validated |
| Codex / Claude Code / implementation agent | Inspect the real repository, implement a narrowly scoped change, add tests, report evidence and open a PR | Inventing normative mathematics, silently rewriting fixtures or merging unreviewed code |
| Independent scientific reviewer | Evaluate mathematical evidence, units, portability and capability limits | Approving their own proposed golden results without independent checking |

Agents are tools and not independent authorities. A PR author and a reviewer can use different agents, but the scientific approval remains human.

## Task lifecycle

1. **Intake:** Select a single issue, explicit milestone and current ratified contract. Capture desired observable behavior, files in scope, explicit non-goals, dependencies and the failure behavior.
2. **Read-only preflight:** Read applicable `AGENTS.md`, repository source, tests and real dependency manifests. Identify whether the issue requires an unratified ADR; if so stop before semantic implementation.
3. **Plan:** Briefly state intended edits, independent references, positive and negative tests, test commands, and any irreversible effects.
4. **Implement:** Prefer red/green/refactor for nontrivial logic; keep each change small. Do not edit unrelated files or silently expand scope.
5. **Verify:** Run focused tests, the offline repository checker, and the applicable native package tests. Record actual output and explicitly label checks that did not run.
6. **Review:** Open a focused PR with the approved ADR/decision references, scientific assumptions, evidence and failure cases. Human approval is mandatory for contract changes.
7. **Land and hand off:** Merge only after required status checks and reviews. Update release and scientific evidence records when applicable; close this issue without automatically starting dependent work.

### Copyable issue handoff

```text
Goal and user/scientific outcome:
Approved decision / ratified ADR:
Milestone and dependencies:
Expected files/modules:
In scope:
Explicit non-goals:
Expected behavior and rejected inputs:
Independent reference / invariant:
Exact verification commands:
Review owner and approval needed:
```

### Verification commands

Run independently from the repository root:

```sh
python scripts/check_repo.py
python -m unittest discover -s scripts/tests -v
python -m pip install --no-deps -e packages/python
python -m unittest discover -s packages/python/tests -v
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
```

The first two check repository-document consistency, **not science**. Native package smoke tests check packaging only. When M0/M1 scientific conformance suites exist, an agent must additionally execute the relevant mathematical and cross-language checks.

Do not claim that a check passed unless it actually ran. A locally unavailable runtime is `NOT RUN`, not `PASS`.

## Review and GitHub enforcement

Documented `AGENTS.md` policies alone **cannot technically enforce** human PI approval. For `main`, maintainers should configure a GitHub ruleset or branch protection with pull requests, required passing CI checks, no force pushes and human review. Once a verified scientific-review team/account exists, add CODEOWNERS for `spec/`, `conformance/` and normative ADRs, and enable required code-owner review.

Do not invent a reviewer handle or claim CODEOWNERS enforcement exists without branch settings. The issue templates and PR template are prompts; CI tests are mechanical checks; human judgment evaluates scientific evidence.

Recommended required checks after this change: `Repository harness`, `Python-only package` and `Julia-only package`, subject to observed GitHub Actions status names. Longer-term: independent analytical, cross-language and SSA profile conformance checks.

## Parallel agents and shared contracts

Different agents may independently implement Python and Julia **only after** the shared contracts and golden vectors are ratified. Avoid simultaneous writes to `spec/`, conformance reference data, or compatibility matrices. Resolve conflicting compiler output against independent evidence and approved specifications; never make one compiler normative by default.

## Security and provenance

No secrets, tokens or private experimental datasets in prompts, logs or repository. Treat serialized BioIR/FIR as untrusted input and reject executable payloads. No mandatory network access, uncontrolled plugin/tool installation, automatic merges, deployments or publication. Explicit user approval is needed for externally visible actions, as appropriate to the task.

## Continuous improvement

When agents repeat the same avoidable failure, add the smallest high-value scoped instruction **or** a deterministic test. Prefer tests and linters for mechanical rules. Retire stale instructions instead of accumulating contradictory prompts. Add a repository-local skill only when a repeated workflow has shown that the automation is genuinely useful.
