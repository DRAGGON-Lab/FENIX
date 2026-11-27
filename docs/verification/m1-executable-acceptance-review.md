# M1 executable packet — bounded acceptance review

**Review PASS; PI acceptance PENDING.** Refs #31 and #34. No unresolved
blocking findings. This report recommends the exact packet below for human PI
review; it records no scientific approval, issue closure or native implementation.

## Reviewed identity and ownership

Reviewed PR #95 head: `7a90803f852da9b7cd7593f7d8dc54380cbe445d`.
Landed main merge: `301dc0542a8bc08750de5796df3269881819b1ca`.
Hosted tested merge: `35af5c3ad1bfe1c5208087ad2f96bf9a79fdb017`.
All three Git trees are identical. Checks ran in an isolated worktree on
`review/m1-executable-acceptance`; the original checkout's `.gitignore` and
untracked `.ignore` were preserved.

The root reviewer owns this report, receipt and retained evidence. A separate
engineering reviewer assessed contracts, transport, identity and rejection paths;
a separate scientific reviewer derived the balances, checked analytical laws and
independently recomputed hosted Julia samples. Neither reviewer rewrote candidate
expectations. Agent review supplies evidence for the PI, not independent human
scientific authority.

Scope was frozen by the requested review plan: complete contract and fingerprint
coverage, all catalog outcomes, independent references, all four methods and
current-source hosted evidence. Affected files are this report, its
[JSON receipt](m1-executable-acceptance-review.json) and its
[evidence directory](m1-executable-acceptance-review/). Non-goals: native APIs,
#32/#33 implementation, #35 installation/integration, acceptance recording,
oscillator #84, SSA, growth, publication and release gates.

## Evidence and acceptance criteria

The reviewed [profile](../../spec/community/executable-profile-proposal.md) and
[manifest](../../spec/community/review-manifest.json) remain PROPOSED. The manifest
SHA-256 is `30255a118bcd17ba8f75d500eaec161bf9c1443f77c15ba74282e7c032f4da81`.
An independent inventory derived from the reviewed Git tree agrees with all
**307** declared fingerprints; every byte hash matches, with no missing or extra
entries. The receipt additionally fingerprints review evidence and relevant
reference-environment locks. No packet artifact was modified by this review.

| Criterion | Evidence and outcome |
|---|---|
| P08 contract correspondence | PASS: explicit owners and local tuples, five directed connections, units and quantity bases; immutable Design/Experiment linkage; exhaustive producer correspondence for all 13 parameters, four initials, populations, geometry and observables. |
| Version and mathematical identity | PASS: closed version/template/backend dispatch; exact finite ASTs; only reactions, equations and observables sort in UTF-16 order. Fresh/idempotent normalization, exact model/wrapper bytes and SHA-256, provenance exclusions, renaming/permutation and identity perturbations verified. |
| Literal catalog | PASS: all 87 unique rows accounted for: 14 positive packets, 56 expected rejections with matching categories/pointers, 17 lexical projections. Analytical packets map by state ID. Row outcomes are retained in the receipt. |
| Supplemental transport | PASS: 10 literal vectors and 6 grid witnesses; binary64 rounding/overflow, collapsed coordinates, signed zero and bitwise grid matching, exact counters/revisions, malformed JSON/Unicode and stale source/result links. ECMAScript independently checks Number/BigInt projections. |
| Independent references | PASS: ten complete case definitions, 30 samples; Decimal 80/160-digit refinement, independent BigFloat 512/1024-bit refinement and comparison controls. Mutation controls include trajectory-preserving changes. Julia comparison/regression execution is hosted, not local. |
| Balance and sensing | PASS: exact cancellation, population/volume scaling, read-only sensing, open-system source/loss terms and nonconservative weighting/sign counterexamples; serialized ASTs checked against independent laws and asymmetric probes. |
| Frozen numerical profile | PASS: all four methods, both settings, explicit columns, state bounds and population-weighted balance bounds including represented initial discrepancy. Full RHS/Jacobian probes include asymmetric, zero and threshold states. |
| Failure discipline | PASS: strict sensing-stage rejection, budgets, incomplete/nonfinite/negative output, retained tail failures and Julia successful-tail/corrupted-success controls. No clipping or fallback. |
| Repository regressions | PASS locally: repository checker, 6 harness tests, 88 package tests and Ruff. Native M1 and local Julia execution NOT RUN. |

Reference columns are `sender.signal, receiver.signal, env.signal,
receiver.reporter`; wire columns are `env.signal, receiver.reporter,
receiver.signal, sender.signal`. Comparisons use explicit IDs. The independent
balance is

```text
M = N_s s + N_r r + E
M' = N_s p_s - N_s d_s s - N_r d_r r - d_e E.
```

Every export/import term cancels pairwise. Reporter production has zero signal
stoichiometry. For closed cases the triangle inequality gives
`|M_num(t)-M_num(0)| <= sum_i w_i b_i(t) + |M_num(0)-M_ref(0)|`,
with reference-order weights `(N_s,N_r,1,0)` and
`b_i(t)=1e-9+1e-8|reference_i(t)|`. Frozen initials are exactly representable;
that observation does not remove the initial-error term from the proposed rule.
Open-system checks establish the algebra; the study does not integrate a general
open-system balance observable or establish biological validity.

## Numerical evidence and revision binding

Local Python 3.12.13 / uv 0.11.29 / SciPy 1.18.1 / NumPy 2.5.5 used the locked
environment. Node was 24.18.0 locally; hosted identity checks used Node 22.
All methods retain baseline `rtol=1e-9, atol=1e-11`, refined
`rtol=1e-11, atol=1e-13`, maximum step 1 second and 200000 RHS calls.
Each method supplies 20 integrations and 60 four-state sample comparisons.

| Method | Execution | Maximum state-error/bound | Maximum closed-drift/bound |
|---|---|---:|---:|
| DOP853 | Local | 0.0605612 | 1.63118e-8 |
| Radau | Local | 0.0137038 | 1.39466e-7 |
| Tsit5 | Hosted | 0.00677002 | 5.70914e-8 |
| Rodas5P | Hosted | 0.0151208 | 1.12552e-7 |

All ratios are below one: 80 integrations / 240 four-state samples overall.
All eight tail attempts (two settings per method) report STAGE_DOMAIN while the
analytical extracellular count is positive. Failed attempts supply no successful
trajectory. Julia's outcome was observed separately; SciPy's outcome was not
imposed on it. Current Julia source also tests valid successful-tail comparison
and corrupted-success rejection for all four columns, even though observed tails
fail. These controls ran in the hosted investigation.

The final-head [community workflow](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45972078514)
passed all four jobs. The [Julia job](https://github.com/DRAGGON-Lab/FENIX/actions/runs/45972078514/job/140414684147)
ran Julia 1.10.13, SciMLBase 3.58.0, OrdinaryDiffEqTsit5 2.1.5 and
OrdinaryDiffEqRosenbrock 2.7.5. Retained API metadata binds the run to PR head
`7a90803`; the receipt records tested merge `35af5c3`, whose complete tree matches
the reviewed head and landed merge.

Artifact `15185118717` was retrieved via the public nightly.link mirror after
GitHub's artifact API returned HTTP 401. Its ZIP SHA-256
`0422f4a0d33837cbbfbf71d7ce571a4a599dc26c4a5ec0a06a3b9a7e79a98642`
matches GitHub's recorded digest. The exact retained
[Julia receipt](m1-executable-acceptance-review/julia-final-head.json) SHA-256 is
`67c2076c11c7f04f8f560dae26735824cf11434462f3d6f9eac8fd29af20a3aa`.
All six source/reference/settings/lock hashes match reviewed bytes, including
current `study.jl` hash `2a626c7209e4a53285102ac04ae7bf7520466b7344660c1623553a2fac54bca3`.
The independent Decimal re-audit recomputed 120 Julia samples and 72 closed
balances from raw states; it did not trust reported pass flags or error ratios.
Hosted BigFloat and kernel/control execution is distinguished from this local
recomputation. Local Julia is **NOT RUN**, because no runtime is available.

## Findings and dispositions

| ID / severity | Location and trigger | Impact | Disposition / focused repair |
|---|---|---|---|
| D1 / low | `conformance/community/feasibility/README.md:78`: current prose says Julia feasibility remains NOT RUN. Reproduce by comparing that sentence with the final-head hosted job and retained receipt above. | Can mislead readers about current hosted coverage. | Superseded explicitly by this report: current-source hosted PASS, local NOT RUN. A later documentation update should link this exact evidence; preserve historical receipts. No scientific blocker. |
| D2 / low | `docs/verification/m1-executable-packet.md:72`: historical receipt paragraph says source hashes match current files. Compare its `julia-5de3833.json` `study.jl` hash (`c3aa8a9d…`) with the current hash above. | Historical green evidence alone does not cover the later successful-tail controls. | Superseded by final-head receipt and matching source hashes in this review. A later documentation update should label that claim historical and cite final-head evidence. The fingerprinted packet remains unchanged. No scientific blocker. |

No confirmed scientific or engineering defect requires a semantic repair or new
expectation. Environment attempts that failed before validation (default uv cache
permissions, restricted download DNS, exploratory Python 3.9 and an incomplete
environment) are recorded separately in the receipt; successful locked reruns
supply the outcomes above. Historical failed hosted Julia syntax attempts remain
historical and are not relabelled as successful checks.

## PI decision boundary and next step

Already accepted: P08 mathematics at `186cfb3` and strict-failure bounded
completion scope at `6964014`. Still proposed: this exact executable profile,
finite schemas/binding/numeric/normalization/version choices, 87-row literal
catalog and supplemental vectors, unchanged ten analytical definitions/30 samples,
and frozen bounded numerical acceptance criteria with the four-method evidence.
Illustrative result/manifests are synthetic wire examples, not native solves.
Hashes establish bounded consistency, not execution authentication.

**Recommendation: present this exact packet for explicit PI acceptance.** No
acceptance is inferred from this review, its PR, a merge or passing CI. Following
acceptance, record the decision and reconcile #31/#34 child gates; then proceed
in order to Python #32, Julia #33, independent installation/integration #35 and
final epic #7 acceptance. Each implementation issue retains its own focused PR.

The [receipt](m1-executable-acceptance-review.json) gives exact executed commands,
timestamps, PASS / FAIL / NOT RUN, complete fingerprints and retained outputs.
For independent reproduction, run the two `audit_*.py` tools in the evidence
directory using the commands in that receipt. No network is needed for those
retained-evidence audits.
