# ChatGPT–Codex collaboration policy

**AGENTS.md** is the operational entrypoint for coding agents. **ChatGPT** plans, resolves ambiguities, reviews architecture and converts validated work into small tasks. **Codex** inspects actual files, edits scoped implementation, writes/tests code and prepares reviewable PRs. **The human PI** approves normative scientific claims, BioIR/FIR semantics, dimensions, canonicalization, independent golden vectors and stable releases.

## Issue handoff template

Each implementation handoff must state: approved decision/ADR, objective, non-goals, expected paths, dependencies, positive and negative acceptance criteria, exact test commands and milestone. Keep to **one child issue per focused PR**.

## Execution loop

1. Read AGENTS.md, PRODUCT.md, ARCHITECTURE.md, relevant ADRs and actual tests.
2. Report short plan and assumptions; inspect dependencies before editing.
3. Change only the requested behavior; preserve independent package installation; add targeted tests.
4. Run what is available. Explicitly distinguish **passed**, **failed** and **not run** checks.
5. Update documentation for behavioral changes; submit a small PR with evidence and limitations.
6. Stop and escalate a proposed ADR if mathematical semantics, schema fields, units, model identity, golden references or package compatibility need novel decisions. Never self-approve a normative change.

## Reporting

Report goal; files changed; decisions and assumptions; exact commands/results; scientific reference/negative-case evidence; unmet checks; risks and follow-ups. Do not add Docker, network services, unsafe serialized callbacks or new mandatory dependencies by default. Avoid unrelated refactoring and hidden scope expansion.
