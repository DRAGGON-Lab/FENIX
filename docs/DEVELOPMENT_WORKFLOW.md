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
7. **Land and hand off:** Merge only after required status checks and reviews. Update release and scientific evidence records when applicable; close an issue only after its own acceptance criteria are satisfied and its required acceptance is recorded, without automatically starting dependent work. Parent scientific/release milestones require explicit human PI acceptance; ADR ratification, CI, agent review and a merge do not substitute for it.

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

Run independently from the repository root with uv 0.11.29 and Python 3.12. Julia uses native Pkg; CI pins Julia 1.10.13, available through juliaup. Install the Python environment before running the offline checks:

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python scripts/check_repo.py
uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v
julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'
```

Commit uv-generated `packages/python/uv.lock`; do not hand-edit it. Keep reference tools in the development group rather than runtime dependencies. The separate [Julia reference environment](../conformance/julia/README.md) commits its Pkg-generated manifest; the library manifest remains ignored. Dependency installation can require network access; subsequent offline checks must not fetch resources.

The repository checker and harness tests check repository-document consistency, **not science**. Python package tests now cover typed M0 content construction and serialization as well as packaging; Julia smoke tests check packaging only. When M0/M1 scientific conformance suites exist, an agent must additionally execute the relevant mathematical and cross-language checks.

Do not claim that a check passed unless it actually ran. A locally unavailable runtime is `NOT RUN`, not `PASS`.

For Python BioIR changes, run the native document suite (`python -m unittest discover -s packages/python/tests_native_documents -v` through the locked uv environment), covering 92 original P01 cases and the 97-case P01 rejection subset. Do not report the other 110 P03/FIR cases as native document conformance. Wheel checks install exported locked runtime requirements before the wheel, without development dependencies.

For Python content changes, also run the native-content projections, Ruff and strict mypy commands in the [Python package instructions](../packages/python/README.md#development-checks). CI additionally builds and tests a clean wheel without development dependencies.

For P01 reference validation, also execute the independent catalog runners and
report comparison from the [catalog instructions](../conformance/bioir/README.md).
These check ratified P01 requirements against candidate fixtures and must not be
reported as approval of those fixtures or as FIR/solver conformance.

## Review and GitHub enforcement

Documented `AGENTS.md` policies alone **cannot technically enforce** human PI approval. For `main`, maintainers should configure a GitHub ruleset or branch protection with pull requests, required passing CI checks, no force pushes and human review. Once a verified scientific-review team/account exists, add CODEOWNERS for `spec/`, `conformance/` and normative ADRs, and enable required code-owner review.

Do not invent a reviewer handle or claim CODEOWNERS enforcement exists without branch settings. The issue templates and PR template are prompts; CI tests are mechanical checks; human judgment evaluates scientific evidence.

Recommended required checks after this change: `Repository harness`, `Python-only package`, `Julia-only package` and `Candidate P01 reference conformance`, subject to observed GitHub Actions status names. Longer-term: independent analytical, cross-language and SSA profile conformance checks.

## Parallel agents and shared contracts

Different agents may independently implement Python and Julia **only after** the shared contracts and golden vectors are ratified. Avoid simultaneous writes to `spec/`, conformance reference data, or compatibility matrices. Resolve conflicting compiler output against independent evidence and approved specifications; never make one compiler normative by default.

## Security and provenance

No secrets, tokens or private experimental datasets in prompts, logs or repository. Treat serialized BioIR/FIR as untrusted input and reject executable payloads. No mandatory network access, uncontrolled plugin/tool installation, automatic merges, deployments or publication. Explicit user approval is needed for externally visible actions, as appropriate to the task.

## Continuous improvement

When agents repeat the same avoidable failure, add the smallest high-value scoped instruction **or** a deterministic test. Prefer tests and linters for mechanical rules. Retire stale instructions instead of accumulating contradictory prompts. Add a repository-local skill only when a repeated workflow has shown that the automation is genuinely useful.

For issue #17 rejection validation, run both native suites/reports, comparison
and independent digest audit from the [rejection-suite commands](../conformance/rejections/README.md#run-and-compare).
The bounded suite has human PI acceptance; negative capability fixtures are not
exhaustive, and native package implementation approval remains separate.

For native Python FIR/compiler changes, also run `python -m unittest discover -s
packages/python/tests_native_fir -v` through the locked uv environment. This suite
checks the 207-case rejection catalog and 84-case canonicalization catalog through
native APIs, including exact approved normalized objects/model bytes/identity
bytes and compiler-source controls. Sets overlap. Legacy reference reports retain
historical NOT_RUN rows; new native outcomes must be recorded separately. Expand
Ruff/strict mypy to include the new FIR/compiler modules and tests, and continue
locked-runtime clean-wheel validation. No solver or empirical validity follows.

## Issue references and closure

Reference related issues using `Refs #<issue-number>` in PR descriptions and
commit messages. Replace the placeholder with the relevant issue number.
GitHub interprets closing keywords mechanically: negating a sentence
is not a reliable safeguard. Reserve closing keywords for work that satisfies
that issue's acceptance criteria and required approval. Scientific/release parent
closure needs explicit PI acceptance. ADR approval, CI, an agent review and a
merge each provide different evidence; none alone supplies scientific signoff.
See [GitHub's linking rules](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue).

## Proposed main protection — NOT APPLIED

The [EP-02 audit](verification/ep02-status-governance.md) observed no branch
protection, repository/inherited rulesets, effective main rules or CODEOWNERS.
The following is a reviewable draft, not activated repository configuration.
The disabled enforcement value makes the administrative activation step explicit.

```json
{
  "name": "FENIX main review and CI",
  "target": "branch",
  "enforcement": "disabled",
  "bypass_actors": [],
  "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
  "rules": [
    {"type": "deletion"},
    {"type": "non_fast_forward"},
    {
      "type": "pull_request",
      "parameters": {
        "allowed_merge_methods": ["merge", "squash", "rebase"],
        "required_approving_review_count": 1,
        "dismiss_stale_reviews_on_push": true,
        "require_last_push_approval": true,
        "required_review_thread_resolution": true,
        "require_code_owner_review": false
      }
    },
    {
      "type": "required_status_checks",
      "parameters": {
        "strict_required_status_checks_policy": true,
        "required_status_checks": [
          {"context": "Repository harness", "integration_id": 15368},
          {"context": "Python-only package", "integration_id": 15368},
          {"context": "Julia-only package", "integration_id": 15368},
          {"context": "Candidate P01 reference conformance", "integration_id": 15368},
          {"context": "Candidate production-decay reference agreement", "integration_id": 15368},
          {"context": "Candidate P03 serialization evidence", "integration_id": 15368},
          {"context": "Candidate BioIR/FIR rejection reference agreement", "integration_id": 15368}
        ]
      }
    }
  ]
}
```

These names and GitHub Actions integration ID were observed on the audited main
commit. Administrators must recheck them before activation. Candidate reference
checks do not provide native Julia compiler/ODE conformance.
[API field definitions](https://docs.github.com/en/rest/repos/rules) describe the
ruleset payload; no API write to protection settings is authorized by this draft.

Administrative actions requiring explicit human authorization:

1. Approve the proposed review/check requirements and confirm eligible human
   reviewers can approve changes independently of their author/latest pusher.
   Keep enforcement disabled until an eligible human reviewer is available;
   a sole active maintainer cannot independently approve their own latest push.
2. The PI designates qualified human scientific owners, with verified write
   access, for `/spec/`, `/conformance/`, `/docs/scientific-evidence/`,
   `/docs/approved-decisions.md`, `/ARCHITECTURE.md` and CODEOWNERS itself.
   No identity is inferred from maintainer permissions or agent review.
3. Separately authorize and review CODEOWNERS creation, then enable required
   code-owner review. The draft's `false` records the present ownership gap;
   general PR review alone does not enforce qualified scientific approval.
4. An authorized administrator imports/activates the approved ruleset and
   verifies effective main rules, required checks, review behavior and force-push
   restrictions. No bypass is proposed. No settings are changed by this document.

Until ownership enforcement is configured, human PI approval of normative
specifications and approved golden expectations remains an explicit review gate
under AGENTS.md. [GitHub code-owner requirements](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-code-owners)
require actual eligible identities; placeholder owners provide no enforcement.
