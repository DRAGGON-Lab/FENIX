# EP-02 / #18 — native Python M0 BioIR content

Implemented [#18](https://github.com/DRAGGON-Lab/FENIX/issues/18), the first focused
delivery under [#4](https://github.com/DRAGGON-Lab/FENIX/issues/4), from `origin/main`
`972f23b` (merged PR #57). Human implementation review remains pending.

Production changes are confined to the Python package: immutable keyword-only
M0 values, Design/Experiment content roots, programmatic P01 validation and fresh
ordinary JSON serialization. Public names and `0.0.0` remain provisional. No
runtime dependencies were added. Test adapters, development tooling, CI, package
and status documentation accompany the API. The complete usage and diagnostics
contract is in the [package README](../../packages/python/README.md).

Non-goals: committed document envelopes, raw parsing, canonicalization, digests,
trusted revision replacement and verified exact Design references (#19); FIR or
compilation (#20); execution (#21/P04); results/manifests (#22/P07). A supplied
Design context establishes local validation only. Its digest is unverified.

## Evidence identity and environment

Verification ran on dirty source based on
`972f23b` on branch `feat/18-python-bioir-content`, 2026-11-15.
The [machine-readable execution record](ep02-python-content.json) contains the
full base revision, per-file SHA-256 manifest, aggregate source fingerprint,
exact commands, environment, UTC start times, exit codes, output excerpts and
log hashes. Its source fingerprint hashes sorted repository-relative path,
NUL, file bytes, NUL for changed/new source files; this evidence pair is excluded
to avoid self-reference. The record also retains the two temporary audit-script
bodies, failed wrapper attempts and the initial red regression output.
Local full logs remain under `artifacts/ep02-18/` (ignored).

Runtime: macOS 15.7.9 x86_64; CPython **3.12.13**; uv **0.11.29**;
Ruff **0.17.5**; mypy **2.4.1**; jsonschema **4.26.0**; rfc8785 **0.1.4**;
Julia **1.10.13**; Node **24.18.0**. Julia is available through
`/private/tmp/julia-1.10.13/bin/julia`, using the existing
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and `JULIA_PKG_OFFLINE=true`.
uv commands use `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`.

| Artifact | SHA-256 |
|---|---|
| Python manifest | `9b006f263ed7e7c936233bec47dc47f5e6f591b12844bd275e462d40831b7786` |
| uv lockfile | `2e0b9f22e4c2669fd5f424205ba832568ff95ef7f66f4e7d187e89a154ea2cda` |
| Built wheel | `4013b9778037eb68e73c205ad641f3b37748ecb0984bdb097af2443191d5a77e` |
| P01 catalog, unchanged | `ffd8b03732094543baff2464ab8c83f672dab6ebb22f2237621a1df8e493fcbc` |
| Rejection catalog, unchanged | `5117b37ec7d4d45e111943e925dcfc27a3ac280ddeabfb456ff37b93a9750088` |
| Retained Python rejection report | `b4fce6c7bfcc9dfb7a47b1a86922b45f664e639204bf5e683548023ba5482b5d` |
| Retained Julia rejection report | `7ec002c0be669e2a64e9fdea019d26d8167991182fde60d595511c813f868921` |

The two retained rejection reports were regenerated with the unchanged native
reference tools. A structured baseline comparison verifies **identical 207 case
rows and every other field**, except the manifest/lock provenance. Comparison of
the refreshed retained reports passes. All files under `spec/` and `conformance/`
remain byte-for-byte unchanged from the base.

## Coverage and outcomes

The behavioral regression suite was written before implementation and initially
failed with `ModuleNotFoundError: fenix.bioir` (**expected FAIL**, preserved).
After implementation all final checks below passed. Early orchestration attempts
leaked macOS system Python's `__PYVENV_LAUNCHER__` into uv child processes and
failed imports; clearing that launcher variable in the temporary runner resolved
them. One audit attempt used unavailable unqualified `python`; the final audit
used the locked uv interpreter. Initial dependency installation also required
network access; locked checks subsequently ran offline. These environment failures
are not presented as package successes.

| Check | Final local outcome |
|---|---|
| Editable package tests | PASS, 11 methods covering native behavior and packaging |
| Native content projections and coverage partition | PASS, 29 cases across 2 methods |
| Schema checks and ordinary JSON readback on accepted projections | PASS |
| Ruff lint and format checks on new code/tests | PASS, 5 files |
| Strict mypy on public BioIR package | PASS, 2 modules |
| Locked environment sync | PASS |
| Wheel and source-distribution build | PASS |
| Clean wheel install with `--no-deps`, package tests | PASS, 11 methods |
| Wheel audit | PASS, only `fenix-bio` installed; `py.typed` present; no `Requires-Dist`; imports from site-packages |
| P01 Python harness tests | PASS, 8 methods |
| P01 Python/Julia reports and comparison | PASS, all 92 approved reference expectations |
| P01 ECMAScript audit | PASS, 41 byte/digest checks |
| Rejection Python tests | PASS, 10 methods |
| Rejection Julia reference tests | PASS, 268 assertions |
| Rejection Julia harness tests | PASS, 45 assertions |
| Rejection Python/Julia reports and comparisons | PASS, all 207 approved reference expectations |
| Rejection ECMAScript audit | PASS, 144 digest checks |
| P03 Python/Node tests | PASS, 15 Python and 5 Node tests |
| P03 Python/Node reports and comparison | PASS, existing serialization evidence only; historical 17 contract-only rows remain NOT RUN |
| Production-decay Python/Julia tests | PASS, 16 Python tests and 648 Julia assertions |
| Rational oracle audit | PASS, 40 samples |
| Production-decay reports and comparison | PASS, 160 computations across 40 samples; agreement at 70 significant digits |
| Julia library package smoke | PASS, 2 assertions |
| Repository/link checker and harness tests | PASS, 6 harness methods |
| Workflow YAML syntax | PASS |
| Protected baseline and retained row audit | PASS |
| Working and staged whitespace | PASS |

The [projection registry](../../packages/python/tests_native_content/coverage.json)
accounts for every original catalog case: **29 PROJECTED** (6 acceptance controls,
23 rejections), **63 DEFERRED** with per-case reasons. Only Design/Experiment
content operations are projected; digest cases, exact digest references,
execution-profile and unknown-field raw diagnostics are excluded. Parse,
canonical and trusted revision operations are deferred to #19. Unknown constructor
keywords retain `TypeError` and are tested separately. Metadata variants test
content construction only. This is **not full 92-case native conformance**.

The test adapter only translates structural nesting to public constructors. It
performs no semantic validation. Error categories match the original P01 catalog;
detailed paths match corresponding accepted rejection-suite cases after removing
`/content` and adding the path of the failing constructor. Accepted output matches
all required content fields and the ratified schema definitions. Catalogs and
fixture bytes were not regenerated.

## Independent review and remaining gates

Separate engineering and scientific reviewer agents inspected the actual diff,
contracts and tests and independently executed focused checks. Both reported no
confirmed defects. Engineering also verified the fresh wheel, marker, dependency
metadata and strict typing. Scientific review independently confirmed the exact
29/63 partition, reference/role/unit constraints and unchanged scientific files.
Agent review is bounded evidence, not human PI implementation approval.

Human review of the focused PR is required. No merge, package publication or
parent epic closure is authorized by these results. Hosted CI is **NOT RUN
locally**; its actual statuses are available on the PR. Native raw parsing,
canonical bytes/digests, full committed-document conformance, compilers, solvers
and empirical biological validity are outside this delivery and remain unclaimed.

## Review concern follow-up — 2026-11-15

This documentation follow-up is based on implementation commit
`15c2a066e8cc3bcf71eea63394f01be9782c21b0` on the same PR branch. The execution
receipts, source fingerprints, artifact hashes and broad verification outcomes
above describe that implementation revision and remain historical evidence.
The original machine-readable receipt is unchanged; it does not claim verification
of these later documentation edits.

The three review concerns are recorded as accepted boundaries:

- The public API remains **uncommitted content authoring**. Construction and
  ordinary JSON serialization do not establish committed document validity. A
  syntactically valid but incorrect Design digest can remain in content; the
  existing regression demonstrating that behavior is preserved.
- Tuple-only collections, exact typed nested values and subclass rejection are
  deliberate M0 reproducibility constraints. An ergonomic builder remains future
  work; no public API or runtime behavior changes in this follow-up.
- Evidence consists of fixed approved projections and hand-authored behavioral
  regressions. Systematic generated-input/property-based and metamorphic testing
  has not been performed. This limitation does not block #18.

[Issue #19](https://github.com/DRAGGON-Lab/FENIX/issues/19) now has a high-priority
acceptance gate requiring verified Design scientific-content digests under P01
and exact ID/revision/digest correspondence before committed Experiment acceptance.
Verification may use a previously verified immutable Design whose digest remains
tied to its exact content; unchecked digest strings and ID/revision matches alone
are insufficient. Committed envelope self-consistency is checked before local
reference resolution. Required regressions cover a valid pair, an incorrect
reference digest, content changed with its old digest, a self-consistent replacement
that differs from the exact reference, and missing/stale references. Offline
resolution, rejection without substitution, and the distinction between
self-consistency and trust in an expected reference remain required by P01.

The separate [generated-input conformance issue #59](https://github.com/DRAGGON-Lab/FENIX/issues/59)
references epic #4 and depends on #19; it adds no acceptance blocker for #18.
It records valid committed round trips, identity-preserving metadata/object-order/
whitespace changes, identity-changing content/array-order changes, invalid inputs
and stale references, and reproducible minimized failures. Approved fixed references
remain required. No testing framework or dependency is selected here.

Follow-up checks ran with `UV_CACHE_DIR=/private/tmp/fenix-uv-cache` and the
unchanged locked Python environment described above. All listed commands exited 0.

| Exact command | Follow-up outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS, repository and local links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 11 methods |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS, 29 projections across 2 methods |
| `git diff --exit-code 15c2a06 -- . ':(exclude)packages/python/README.md' ':(exclude)docs/verification/ep02-python-content.md'` | PASS, all other tracked files unchanged |
| `git diff --check` and `git diff --cached --check` | PASS, working and staged whitespace |

Production code, tests, dependency locks, scientific contracts, catalogs, fixture
bytes and original machine-readable receipts are unchanged. Broad reference,
Julia and wheel suites were **NOT RUN again locally** for this documentation-only
follow-up; their implementation-revision outcomes are retained above. Human
implementation approval and merging remain pending.
