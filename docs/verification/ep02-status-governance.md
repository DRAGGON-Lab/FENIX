# EP-02 integration, tracking and governance audit — 2026-11-16

Audited main: [`32acf4f4b51e257c7efed65203360e5e9ee83598`](https://github.com/DRAGGON-Lab/FENIX/commit/32acf4f4b51e257c7efed65203360e5e9ee83598), tree `1295e0609cf0962d789ab37bd54283ecf752e500`. Current main remained at this merge throughout the corrective GitHub actions. The initial local checkout at `d54c628783482088f47cf6b683e524f6fb5269fa` had the same tree; the maintenance branch starts from current main. This is a status/governance correction, not new scientific acceptance.

## Findings and disposition

| Finding | Evidence | Action | Outcome |
|---|---|---|---|
| Integrated Python M0 implementation is on main | Merged PRs [#58](https://github.com/DRAGGON-Lab/FENIX/pull/58), [#60](https://github.com/DRAGGON-Lab/FENIX/pull/60), [#61](https://github.com/DRAGGON-Lab/FENIX/pull/61), [#63](https://github.com/DRAGGON-Lab/FENIX/pull/63), [#65](https://github.com/DRAGGON-Lab/FENIX/pull/65); [post-merge CI](https://github.com/DRAGGON-Lab/FENIX/actions/runs/43960747581) has seven successful jobs | Correct live status documentation and parent tracking | Implementation availability recorded separately from scientific/release signoff |
| Parent reports PR #65 unmerged | [#4](https://github.com/DRAGGON-Lab/FENIX/issues/4) body at audit | Replace stale merge prerequisite; link integrated path and CI | OPEN; explicit final PI acceptance still required |
| ODE scientific gate was closed without required Julia implementation | [#29](https://github.com/DRAGGON-Lab/FENIX/issues/29); `packages/julia/src/Fenix.jl`, `test/runtests.jl`, `Project.toml` | Reopen and explain missing native Julia tests and scientific signoff | OPEN; original criteria unchanged |
| Broader provenance/archive gate was closed without its demonstration | [#42](https://github.com/DRAGGON-Lab/FENIX/issues/42); P07 explicitly excludes archives; #27/#40 remain open | Reopen, correct Python availability and explain unmet archive/checksum/replay criteria | OPEN; no new authentication requirements invented |
| #22 closure preceded merge | [Closure comment](https://github.com/DRAGGON-Lab/FENIX/issues/22#issuecomment-6929801138), issue timeline and PR merge metadata | Preserve history, append integration update and comment | CLOSED; closure at 21:23:45 UTC, merge at 21:30:16 UTC |
| Dependent descriptions have stale merge requirements | [#30](https://github.com/DRAGGON-Lab/FENIX/issues/30), [#40](https://github.com/DRAGGON-Lab/FENIX/issues/40) | Correct Python availability only | Both OPEN; other prerequisites unchanged |
| Current docs mix historical implementation status with current capability | `README.md:5`, `PRODUCT.md:37`, `ARCHITECTURE.md:3`, Python README content/compiler/results sections, decision/spec/evidence indexes | Narrow current-status corrections; append-only results-record addendum | Python implementation distinguished from Julia scaffold and scientific gates |
| Main has no enforced review/check or scientific-owner rules | Branch API: `protected=false`; protection GET: 404 “Branch not protected”; rulesets including inherited and effective main rules: empty; no tracked CODEOWNERS | Document [concrete disabled ruleset proposal](../DEVELOPMENT_WORKFLOW.md#proposed-main-protection--not-applied) | No protection or ownership settings applied |

These tracking/documentation inconsistencies are engineering/release-governance findings, not reproduced numerical defects. No later implementation satisfying #29/#42 was found: main has not advanced beyond PR #65, Julia remains a scaffold, both issues had no comments supporting acceptance, and relevant dependency issues remain open. No GitHub releases or tags were present at audit. Absence of recorded acceptance is not a claim about unrecorded private discussions.

## Scientific and implementation evidence boundaries

The Python API contains verified `DesignDocument`/`ExperimentDocument`, `compile_experiment`, immutable FIR, `solve_ode` with DOP853/Radau, and P07 `run_experiment`/`RunRecord.from_json`. The 88 package methods include the integrated capture/readback path and 19 results methods. P04 tests compare both SciPy methods against the approved 40-sample oracle at predeclared settings. The separate Julia analytical reference evaluator uses BigFloat; it is not the missing native Julia ODE adapter. Its candidate/reference reports do not establish native cross-language solver conformance.

Implementation merge identities verified through GitHub:

| PR | Merge SHA |
|---|---|
| #58 | `91dd4c2d95d617dc998b4bd5bb255f512aac59d4` |
| #60 | `e18245573a01d1a8ed68dba58741229eb51a28e0` |
| #61 | `38ae2e851e8833628e0eb71ac0d00faa8ecafa4f` |
| #63 | `b6beb5e8dfef5d44b333f674424be6e941613b4e` |
| #65 | `32acf4f4b51e257c7efed65203360e5e9ee83598` |

P01–P04/P07 contracts, units, identities, tolerances, fixtures and behavior are unchanged. P07 hashes and exact source linkage establish bounded consistency. Plausible altered positive-time samples with recomputed internal checksums can pass readback, as the existing native test demonstrates. A trusted external manifest hash checks against that expectation; it does not prove execution authenticity, authorship, numerical correctness, biological validity or exact replay. This maintenance does not implement Julia, SSA, archives, new biology, version governance or generated-input tests.

## Closure attribution and explicit metadata actions

GitHub GraphQL returned PR #65 in `closingIssuesReferences` for both #29 and #42; each issue's `ClosedEvent.closer` was PR #65, merge SHA `32acf4f4…`. Closure events occurred at 21:30:20 and 21:30:22 UTC respectively. Attribution to PR #65 is **verified**. Its description contained a negated closing-keyword clause; the precise substring that caused each link remains an **inference**, not a demonstrated parser trace. GitHub's [documented linking behavior](https://docs.github.com/en/issues/tracking-your-work-with-issues/using-issues/linking-a-pull-request-to-an-issue) explains why neutral references are safer.

The original PR description was snapshotted before editing. Its risky clause was replaced with neutral `Refs #29 and #42` wording; other PR content, comments, review and merge history were preserved. The description was neutralized before reopening the issues and adding explanatory comments. Post-action GraphQL verification returned **no closing references**. Before writes, all affected issue bodies/states and PR text were compared with the preflight snapshot to avoid overwriting intervening edits. Replaying the guarded batch refuses changed state rather than duplicating its comments.

- [#22 integration comment](https://github.com/DRAGGON-Lab/FENIX/issues/22#issuecomment-6930689401)
- [#29 reopening evidence](https://github.com/DRAGGON-Lab/FENIX/issues/29#issuecomment-6930689700)
- [#42 reopening evidence](https://github.com/DRAGGON-Lab/FENIX/issues/42#issuecomment-6930689964)

The [new maintenance receipt](ep02-status-governance.json) lists every PATCH/POST target, purpose, resulting URL and before/after body hashes. #4/#30/#40 remain open, #18–#22 remain closed, #29/#42 are reopened. No parent closure, merge, release, protection or CODEOWNERS action was taken. Existing historical comments and numerical verification receipts were preserved.

## Governance proposal and outstanding human decisions

All seven hosted jobs passed, but none was configured as a required branch check. The only recorded PR review on #65 was an automated Codex summary, not a formal approving scientific review; PI-directed implementation closure is separately recorded in #22. Repository permissions do not designate scientific expertise or authority. No repository team or CODEOWNERS scientific mapping was configured.

The workflow's disabled draft proposes PR review, one approval, fresh-push/stale-review safeguards, resolved threads, seven named GitHub Actions checks, up-to-date testing, and no deletion/force pushes or bypass actors. Administrative activation and scientific CODEOWNERS designation require explicit human authorization. The draft explicitly leaves code-owner review false until real owners are approved and configured; it does not claim scientific-review enforcement already exists.

Outstanding PI/administrative decisions:

- Record final EP-02 scientific acceptance and applicable release signoff; #4 stays open until then.
- Review future #29 dual-native numerical evidence and #42 provenance/archive deliverables against their own criteria; this maintenance does not satisfy them.
- Designate qualified human scientific owners and authorize ownership enforcement and ruleset activation.
- Ratify P06 version/release governance in its own task. #59 generated-input investigation remains separate and is not retroactively added as a blocker to completed bounded implementation issues.

## Verification

Commands run from repository root using uv 0.11.29 / Python 3.12.13, with `UV_CACHE_DIR=/tmp/fenix-uv-cache` for uv commands:

| Exact command | Outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS after documentation corrections |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, six tests after documentation corrections |
| `git diff --check` | PASS |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 88 tests during read-only audit on the tree identical to main; not rerun for documentation-only edits |
| `python3 /tmp/fenix-ep02-verify.py verify` | PASS; intended issue states, empty PR closing references, unchanged main/protection/rulesets |
| `python3 /tmp/fenix-ep02-preserve.py` | PASS; protected tracked bytes, historical ratification text and existing results-record prefix unchanged |

Fresh wheel, numerical-reference suites, Julia tests, Ruff and mypy: **NOT RUN** for this documentation-only maintenance. The seven-job post-merge run is separately identified historical CI, not freshly generated scientific evidence. Hosted checks for this maintenance PR are observed separately after push. No tests or golden expectations were changed.

The first documentation link check failed because this report linked its new
companion JSON before that file had been generated. After generating the JSON,
the same checker passed. This ordering failure and correction are recorded in
the new receipt; no scientific expectation was changed.

Independent documentation review found no blocking findings. The reviewer ran
the repository checker, six harness tests, whitespace check and historical P07
prefix comparison successfully. Live GitHub state was assessed by the owner;
the reviewer checked those claims against the new audit receipt. Agent review
does not supply final human scientific or release approval.
