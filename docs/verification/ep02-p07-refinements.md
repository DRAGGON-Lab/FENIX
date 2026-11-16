# EP-02 / #22 — P07 review refinements

**PROPOSED; revised contract awaits further scientific review and explicit
human-PI ratification. No native P07 runtime implementation is included.**

Baseline: initial PR #64 proposal revision `908997e4e8edb679a7d9ac093f69ee9df24bd8f5`.
Date: 2026-11-16. The user expressed approval of the basis, then explicitly
requested five refinements and another scientific review **before ratification**.
This record documents those refinements; it does not record final ratification.
The initial [proposal evidence](ep02-p07-proposal.md), JSON audit and checksum
receipt remain byte-for-byte historical. New evidence is recorded separately.

## Revised contract and ownership

The primary author owns the revised ADR/schema, proposed examples, audit source,
new verification files and PR #64 description. Independent scientific and
engineering reviewers own read-only assessments. Only the stale prerequisite
paragraph of issue #22 is updated externally, as explicitly requested.
No package, dependency, CI, ratified P01–P04 contract, approved fixture or
historical verification receipt may change.

Dependency graph remains **refined proposal → independent scientific review →
explicit PI ratification → separate native implementation/test PR → human
implementation review**. #22 stays open; #29/#42 and the parent epic are separate.

The [revised ADR](../../spec/results/proposals/ADR-P07.md) now distinguishes:

- Language-neutral core source/FIR identities, binary64 and exact integer rules,
  execution controls, producer identification, `evaluations.nfev`, clocks,
  randomness, output integrity and the unchanged ODEResult schema.
- Required `backend.profile = python-scipy-ode/0.1.0`, with SciPy solver details,
  Python/NumPy/SciPy environment and backend `njev`/`nlu`. The relative-tolerance
  floor belongs to this backend. Unknown profiles reject; a future reviewed
  Julia/SciML profile can reuse the core without requiring Python-specific
  fields. No Julia profile or functionality is implemented.
- Required nullable `producer.build_id`, preserving an opaque ID only when
  installed build metadata reliably identifies the actual build/source snapshot.
  Runtime Git/VCS inspection and network lookup are forbidden. Null is required
  when unknown; `0.0.0` plus null cannot distinguish development builds. Build
  generation/governance and stronger attestation remain P06/#42 work.

The revised proposal explicitly retains native acceptance obligations for
wrong-source/same-FIR rejection, raw manifest/result byte round trips, binary64
and large-integer fidelity, solver-free readback, and no successful record after
solver failure. These are not claimed as implemented by candidate audits.

## Multi-observable reference candidate

The new hand-prepared Experiment declares observables `z_amount, a_amount,
m_amount`, all targeting the existing single molecular-count state. Its expected
unnormalized FIR retains that order. The result columns are `a_amount, m_amount,
z_amount` under unchanged P03 normalization, with three direct `x` mappings and
`molecule` units. Two state rows reuse the approved `baseline-zero` oracle's
nearest-binary64 values at 1 and 10 seconds; no numerical oracle is invented.
All manifest observations are synthetic and are not execution receipts.

| Candidate identity | SHA-256 |
|---|---|
| Experiment P01 content | `820265c52cc4ec4bc857044e3c14f096bf9d75040236da33671ab74392d4f7fd` |
| P03 normalized FIR identity wrapper | `07c998a3dc972bd7df415200d0b7f0ea565aca821f278dcf95598e486e1fd2e5` |
| Exact result JSON bytes, including final newline | `cc6882d6240bdc5bbd436dacb7be80722edc4ee852822d182282116574b1199b` |

The Python audit uses external rfc8785 and exact rational arithmetic, never
native FENIX. The revised ECMAScript cross-check independently serializes the
same candidate source and normalized model and checks observable columns, direct
state-value bits, mappings, units and exact output hashes. These fixed-ASCII
fixture serializers are not general native normalizers. JavaScript JSON.parse
does not establish exact large integers; the Python field-specific probe remains
the integer check. The [candidate catalog](../../spec/results/proposals/examples/checksums.json)
freezes all eleven candidate file hashes.

The original three result artifacts are unchanged. Their proposed manifests
change only to the revised core/backend representation. The multi example's
non-null `candidate:p07-multi-observable-v1` build label is explicitly synthetic;
the original three manifests use null. No real build is asserted by this label.

## Tracking correction

Issue [#22](https://github.com/DRAGGON-Lab/FENIX/issues/22)'s prerequisite
paragraph now records completed #21 and merged PR #63 (`b6beb5e`), alongside
completed #20/merged #61. The GitHub API confirmed #21 `closed` with reason
`completed`, and PR #63 merged. Only that paragraph was replaced, the full body
was read back and compared, and #22 was verified still open. P07 ratification
and implementation remain separate gates in the updated note.
The [tracking receipt](p07-issue22-tracking.json) records that readback and the
verified dependency state; it does not claim GitHub enforces scientific approval.

## Current verification and review

All uv commands use `UV_CACHE_DIR=/private/tmp/fenix-uv-cache` from the repository
root. uv 0.11.29; Python 3.12.13; jsonschema 4.26.0; rfc8785 0.1.4;
Node v24.18.0. The [new JSON audit](p07-refinement-audit.json) retains exact
source/input and candidate hashes. The [new checksum receipt](p07-refinement-byte-checksums.txt)
uses independent system SHA-256. Neither replaces an initial proposal receipt.

| Command | Actual outcome |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS; 19 locked packages, no dependency changes |
| `uv run --project packages/python --locked --offline python spec/results/proposals/review_p07.py > docs/verification/p07-refinement-audit.json` | PASS; 4 pairs, 3 multi-observable columns, 2 wrong-source/same-FIR counterexamples, 3 unique analytical reference samples, 8 binary64 probes, 114 structural rejection mutations |
| `node spec/results/proposals/review_p07_refinements.js` | PASS; 11 artifact hashes, 4 result hashes/normalized FIR identities/mappings, 1 new source digest, 8 binary64 probes |
| `shasum -a 256 spec/results/proposals/examples/*.json spec/results/proposals/*.schema.json spec/results/proposals/ADR-P07.md spec/results/proposals/review_p07.py spec/results/proposals/review_p07_refinements.js docs/verification/p07-issue22-tracking.json > docs/verification/p07-refinement-byte-checksums.txt` | PASS; system values agree with Python/Node |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 69 existing package methods |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v` | PASS; 2 methods, 29 fixed projections |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS; 3 methods, original 92 P01 and 97 P01 rejection cases |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_fir -v` | PASS; 3 methods, overlapping 207/84 catalogs and producer controls |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 repository harness methods |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/local links, not science |
| `uv run --project packages/python --locked --offline ruff check spec/results/proposals/review_p07.py` | PASS |
| `uv run --project packages/python --locked --offline ruff format --check spec/results/proposals/review_p07.py` | PASS; 1 file |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml spec/results/proposals/review_p07.py` | PASS; 1 audit source |
| `uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml` | PASS; 13 unchanged package sources |

The first refinement audit mypy invocation **FAILED** because a heterogeneous
negative-test tuple containing an empty list needed an explicit `object` type.
Adding that annotation resolved the error; the same strict command then passed.
No check or validation expectation was weakened, and no dependency was added.

Final replay/protection commands:

| Command | Actual outcome |
|---|---|
| `uv run --project packages/python --locked --offline python spec/results/proposals/review_p07.py > /private/tmp/fenix-p07-refinement-replay.json` | PASS |
| `cmp docs/verification/p07-refinement-audit.json /private/tmp/fenix-p07-refinement-replay.json` | PASS; deterministic bounded audit replay |
| `shasum --check docs/verification/p07-refinement-byte-checksums.txt` | PASS |
| `git diff --exit-code 908997e -- packages conformance .github docs/approved-decisions.md spec/bioir spec/fir spec/canonicalization spec/execution docs/verification/ep02-p07-proposal.md docs/verification/p07-candidate-audit.json docs/verification/p07-byte-checksums.txt spec/results/proposals/review_p07.js spec/results/proposals/ode-result-m0.schema.json` | PASS; runtime, ratified contracts, approved artifacts, historical receipts and result schema unchanged |
| `git diff --check` | PASS |

Both independent reviewers report no blocking finding in the refined proposal.
The scientific reviewer independently recomputed the new P01 source digest and
evaluated the two multi-observable samples with 120-digit Decimal arithmetic,
using represented binary64 beta=0.1. Both samples are nearest binary64; all three
observable columns copy their mapped state bits and preserve units. Independent
schema controls rejected SciPy fields at core scope, backend counters at core
scope, a core method name, an unknown Julia profile and invalid build IDs; null
and nonempty build IDs were accepted. The reviewer also replayed both audits.
The additional scientific controls ran as
`uv run --project packages/python --locked --offline python /private/tmp/fenix-p07-refinement-scientific-controls.py`
with source SHA-256
`c80d506271c1d6c332f6931835e459adee004ab63bcbf4d534a6ef1891b0274a`.
That temporary independent review script is not a portable retained runner;
the tracked Python/ECMAScript audits retain the reproducible fixture checks.

The engineering reviewer separately exercised 18 schema rejection controls,
including misplaced profile data, negative/boolean/fractional backend counters,
unknown nested members/profiles and invalid build IDs. Null and opaque Unicode
IDs passed. Independent exact raw-byte/formatting controls for all four pairs,
normalized multi-observable ordering, direct state bits/units and protected-file
comparisons passed. These independent review controls are bounded evidence and
do not constitute native RunRecord loading or execution tests.
The engineering reviewer also verified all 18 final checksum-receipt entries,
replayed the retained audit byte-for-byte, checked every reported input/candidate
hash against current files and reconfirmed that historical receipts are unchanged.

| Final reviewed artifact | SHA-256 |
|---|---|
| ADR-P07 | `cb45714cc685bdd182655d14794dfc9f5ba2dc1cc6ffde7c2ac022af018facef` |
| RunManifest schema | `8e1c9236f33801ff81a12900d386c531295830ebca22ad2f09b9deb007d6264d` |
| New audit receipt | `cf01e94432fde19c6ec079b621d6626e95917697d6f4b92e8a0cf801547c716f` |
| New system checksum receipt | `5cd111cc0dc739f5195421ae36e3d00abb3e04ad58f8276ea2db980dd307e6aa` |

**NOT RUN:** native P07 capture/readback/failure tests, clean-wheel validation,
distribution builds, Julia runtime execution and CI implementation-target changes.
Those remain obligations of the separate post-ratification implementation.
Passing unchanged package tests does not implement #22, attest execution,
establish biological validity or close #29/#42. Independent agent review is not
PI ratification. **Revised contract ratification and implementation approval
remain PENDING.**
