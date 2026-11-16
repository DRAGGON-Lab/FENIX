# EP-02 / #22 — P07 human-PI ratification

**RATIFIED on 2026-11-16:** revised P07 contract, schemas and bounded candidate
reference expectations at reviewed revision
[`bc662d3e9778dc7977de39041f8a44cba314851e`](https://github.com/DRAGGON-Lab/FENIX/commit/bc662d3e9778dc7977de39041f8a44cba314851e),
on [PR #64](https://github.com/DRAGGON-Lab/FENIX/pull/64).
**Native implementation approval remains PENDING.** This records approval;
it does not implement #22 or merge its contract PR.

## Human decision and reviewed identity

The approving human PI is the repository user in this Codex conversation.
No separate personal name or public approval URL was supplied. The user stated:

> I approve the proposal.

The user explicitly identified the reviewed artifacts below and specified:

> Ratification should cover the revised schema and bounded candidate reference
> expectations at commit bc662d3, not claim approval of a native implementation.

| Artifact at the reviewed commit | Reviewed SHA-256 |
|---|---|
| ADR-P07 | `cb45714cc685bdd182655d14794dfc9f5ba2dc1cc6ffde7c2ac022af018facef` |
| RunManifest schema | `8e1c9236f33801ff81a12900d386c531295830ebca22ad2f09b9deb007d6264d` |

The human's stated verification limit is retained:

> These are the hashes recorded in the refinement receipt; I did not
> independently recompute every hash from raw bytes in this review.

Agent verification recomputed both raw Git-blob SHA-256 values and confirmed
exact agreement with those supplied values. This mechanical check is separate
from the human's scientific approval and makes no claim that the human manually
recomputed every hash. The [machine-readable record](p07-ratification.json)
retains both expected and recomputed identities and the approval boundary.

Accepted scope: P07's language-neutral core, explicit closed Python/SciPy
backend profile, nullable producer build/source identifier, both versioned
schemas and bounded reference expectations/catalog at `bc662d3`, including the
multi-observable ordering/mapping/unit/checksum example. This does not approve
native implementations, exhaustive validation, Julia functionality, execution
authenticity, biological validity, #29 or #42. Wrong-source/same-FIR rejection,
exact raw-byte round trips, binary64/large-integer fidelity, solver-free readback
and no successful record after failure remain required native acceptance tests.

## Preservation and status annotations

This documentation-only follow-up updates the ADR's status and adds its explicit
ratification record, the decision register, architecture/specification indexes
and the example README. The reviewed ADR hash therefore identifies the immutable
Git blob **at `bc662d3`**, not the ADR after adding this approval annotation.
The contract's normative rules are unchanged.

Schema, candidate JSON/catalog, audit source, approved fixtures, P01–P04, package,
solver and historical receipt bytes are untouched. Drafting-era PROPOSED/PENDING
labels inside those retained artifacts describe their original preparation;
the explicit ratification record controls acceptance status. The original
[proposal](ep02-p07-proposal.md) and [refinement](ep02-p07-refinements.md) records
remain historical; no receipt is regenerated to disguise its original status.

## Checks executed for this record

Commands run from the repository root unless a different working directory is
specified. uv commands use `UV_CACHE_DIR=/private/tmp/fenix-uv-cache` and the
locked Python environment. The reviewed snapshot replay used Python 3.12.13,
jsonschema 4.26.0 and rfc8785 0.1.4, matching the original receipt.

| Command | Actual outcome |
|---|---|
| `git show bc662d3:spec/results/proposals/ADR-P07.md \| shasum -a 256` | PASS; `cb45714c…18facef` |
| `git show bc662d3:spec/results/proposals/run-manifest-m0.schema.json \| shasum -a 256` | PASS; `8e1c9236…7d6264d` |
| Python hashlib SHA-256 over both raw `git show` blobs | PASS; expected/recomputed values retained in new JSON record |
| `mkdir -p /private/tmp/fenix-p07-ratification-reviewed` then `git archive bc662d3e9778dc7977de39041f8a44cba314851e \| tar -x -C /private/tmp/fenix-p07-ratification-reviewed` | PASS; immutable reviewed snapshot extracted for replay |
| `uv run --project packages/python --locked --offline python /private/tmp/fenix-p07-ratification-reviewed/spec/results/proposals/review_p07.py > /private/tmp/fenix-p07-ratification-replay.json` | PASS; 4 pairs, 114 structural rejection mutations, 8 binary64 probes, 2 wrong-source/same-FIR counterexamples |
| `cmp docs/verification/p07-refinement-audit.json /private/tmp/fenix-p07-ratification-replay.json` | PASS; byte-identical historical audit replay |
| `node spec/results/proposals/review_p07_refinements.js` from `/private/tmp/fenix-p07-ratification-reviewed` | PASS; 11 hashes, 4 result/FIR identities/mappings, new source digest and 8 binary64 probes |
| `shasum --check docs/verification/p07-refinement-byte-checksums.txt` from `/private/tmp/fenix-p07-ratification-reviewed` | PASS; all 18 reviewed entries |

The frozen receipt must be checked against its recorded reviewed snapshot:
checking it against the later annotated ADR would compare different documents.
Final repository/harness checks and protected-file comparisons:

| Command/check | Actual outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository/local links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness methods |
| Python byte comparison of the complete normative ADR body, from `## Proposed artifacts and identities` to the final ratification-status marker, against `bc662d3` | PASS; only governance/status annotations changed |
| `git diff --exit-code --diff-filter=CDMRTUXB bc662d3 -- packages conformance .github docs/verification spec/bioir spec/fir spec/canonicalization spec/execution spec/results/proposals ':(exclude)spec/results/proposals/ADR-P07.md' ':(exclude)spec/results/proposals/examples/README.md'` | PASS; no existing protected source/receipt changed; new approval records are additions |
| `git diff --check` | PASS |

Native P07 implementation/capture/readback/failure tests, clean-wheel checks and
Julia runtime execution are **NOT RUN** for this documentation-only follow-up.
They remain obligations of separate implementation and review work. Issue #22
and its parent epic remain open; neither merge nor completion is recorded here.
