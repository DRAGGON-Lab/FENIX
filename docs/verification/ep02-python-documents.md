# EP-02 / #19 — committed Python BioIR documents

Issue [#19](https://github.com/DRAGGON-Lab/FENIX/issues/19), parent #4.
Implementation starts from merged PR #58, main
`91dd4c2d95d617dc998b4bd5bb255f512aac59d4`, on
`feat/19-python-bioir-documents`. Human implementation approval remains pending.

The delivery adds frozen document envelopes, metadata, strict P01 ingestion,
scientific digest verification, exact local Design resolution, explicit revision
replacement and fresh envelope JSON serialization. Content-only #18 APIs remain
unchanged. Canonical content bytes hash direct RFC 8785 content; ordinary envelope
JSON provides digest-preserving readback, including large integral floats whose
canonical integer spellings P01 cannot ingest. Optional expected digests pin a
caller's trusted expectation. Verified self-consistency does not authenticate
origin, establish a global revision archive or provide persistence.

The [package documentation](../../packages/python/README.md) describes APIs and
boundaries. FIR normalization/compilation, simulation, P07 archive provenance,
ergonomic builders and systematic generated-input testing (#59) are outside scope.

## Reproducibility and fixed acceptance

The [machine-readable receipt](ep02-python-documents.json) records exact commands,
UTC times, exit codes, output excerpts, log hashes, dependency versions, base source
identity, changed-file hashes and the aggregate dirty-source fingerprint. The
fingerprint hashes sorted relative path + NUL + file bytes + NUL, excluding this
evidence pair to avoid self-reference. Tests ran dirty on the base revision;
committed files carry the recorded source bytes. Full local logs remain in ignored
`artifacts/ep02-19/`. Initial regression failures are retained in the JSON record.

Environment: CPython 3.12.13, uv 0.11.29, Ruff 0.17.5, mypy 2.4.1,
jsonschema 4.26.0, rfc8785 0.1.4, Julia 1.10.13 and Node 24.18.0.
uv uses `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia uses
`/private/tmp/julia-1.10.13/bin/julia`, the existing
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, and `JULIA_PKG_OFFLINE=true`.
Installation/build dependencies were available in the existing local cache.

The native document suite covers all **92 original P01 cases** (49 parse,
5 canonical, 15 Design, 19 Experiment and 4 revision), and the **97 P01 cases**
from the rejection suite. The two sets overlap; they are not 189 unique fixtures.
The latter set's 110 P03/FIR cases are explicitly outside native #19 conformance.
The original root-only SCHEMA paths are coarsened only for legacy comparison;
detailed categories, paths and input identities are checked against the rejection
catalog. Reference-only stage labels are not a new native diagnostic API.
Generic JSON fixtures directly exercise private production helpers; document cases
use public loaders. Adapters only dispatch operations and identify supplied inputs.
Serialization also passes the original ratified envelope schema via dev jsonschema.
The existing 29 content projections remain unchanged and pass independently.

The Python reference and production implementations share external rfc8785.
Consequently Python serializer agreement alone is not independent evidence; fixed
approved canonical bytes and independent Julia/Node checks remain essential.
No catalogs, schemas, expected bytes or fixtures were regenerated. Both retained
207-case rejection reports were regenerated and verified to change only the Python
manifest/lock fingerprints; every case row and every other field is unchanged.
Their current hashes appear in the machine-readable record. Earlier receipts and
hashes remain historical evidence rather than being rewritten to claim new checks.

## Executed outcomes

All final local checks in the machine-readable record are PASS (exit 0):

- Editable and clean-wheel package tests: 28 methods each, including 17 new
  parser/document regressions. Regression-first failures for missing APIs were
  recorded before implementation.
- Native document suite: 3 methods covering all 92/97 cases and envelope schema
  serialization. Content-only suite: 2 methods covering 29 projections.
- Ruff lint/format: 11 files; strict mypy: 5 production modules.
- Source/wheel build, locked runtime export/install and wheel metadata audit:
  only fenix-bio and rfc8785 0.1.4 installed; site-packages import and py.typed verified.
- Original Python P01 tests: 8; Python/Julia P01 reports and comparison: 92;
  independent ECMAScript byte/digest audit: 41.
- Python rejection tests: 10; Julia reference/harness: 268/45 assertions;
  independent 207-case reports and comparison; ECMAScript digest audit: 144.
- P03 reference Python/Node tests: 15/5; reports/comparison pass. The historical
  17 contract-only rows remain NOT RUN; no native FIR claim follows.
- Production-decay reference Python/Julia tests: 16/648 assertions, 40-sample
  rational audit, independent reports/comparison: 160 computations agreeing at
  70 significant digits. These are existing reference checks, not a new solver.
- Julia library smoke: 2 assertions; repository/link checks; 6 harness tests;
  workflow YAML syntax; protected-artifact audit; working/staged whitespace.

Independent scientific review found no unresolved scientific correctness issues;
one stale README dependency statement was identified and corrected. Independent
engineering review results are recorded in the receipt. Agent reviews are bounded
checks, not human PI implementation approval. Hosted CI is observed separately on
the focused PR; it is not represented as locally executed evidence. No merge,
publication, parent epic closure or subsequent delivery is included.

## Review clarification — 2026-11-15

This documentation-only follow-up is based on implementation revision
`187aa9f69317eb56467ce208601c35801e10bbbb`. The source fingerprints, original
machine-readable receipt, artifact hashes and broad execution results above remain
historical evidence for that revision; they are unchanged and do not claim to
verify subsequent documentation edits.

The review found no confirmed blocking correctness defect. These limitations
remain explicit for #19's bounded milestone:

- **Self-consistency is not authorization or provenance authentication.** A
  modified document with its correctly recomputed digest can be self-consistent
  without being the document a researcher authorized. `expected_digest` allows
  comparison against a caller-supplied trusted external expectation; establishing
  that trust, signatures, archives and provenance auditing remain future work.
- **Revision checks are predecessor-relative.** A trusted supplied predecessor
  supports replacement validation. It does not establish global revision history,
  prevent concurrent conflicting branches or guarantee that historical documents
  remain stored. In-memory immutability supplies no persistence guarantee.
- **Generated-input investigation remains required future conformance work.**
  Fixed approved cases and hand-authored regressions do not exhaust interactions
  among numeric parsing, canonicalization, revisions and references.
  [Issue #59](https://github.com/DRAGGON-Lab/FENIX/issues/59) now explicitly includes
  combined cross-feature scenarios, reproducible replay and minimized failures.
  It remains open without becoming a retroactive acceptance blocker for #19 or
  selecting a testing framework in this follow-up.
- **Serializer agreement within Python is not fully independent.** Production and
  the Python reference share `rfc8785`. Their serializer agreement alone is
  insufficient independent evidence. The
  [approved P01 expectations](../../conformance/bioir/README.md),
  [approved canonicalization vectors](../../conformance/canonicalization/README.md)
  and executed Julia/Node comparisons and audits listed above supply additional
  bounded milestone evidence. They do not establish exhaustive correctness or
  biological validity.

Follow-up checks use the same locked Python environment and
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Each listed command exited 0:

| Exact command | Clarification outcome |
|---|---|
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS, repository/local links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS, 28 methods |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_documents -v` | PASS, 3 methods; 92 original and overlapping 97-case P01 subset plus schema checks |
| `git diff --exit-code 187aa9f -- . ':(exclude)packages/python/README.md' ':(exclude)docs/verification/ep02-python-documents.md'` | PASS, all other tracked files unchanged |
| `git diff --check` and `git diff --cached --check` | PASS, working/staged whitespace |

Only the package README and this human-readable verification record change
locally. Production code, public API, tests, dependencies, scientific contracts,
catalogs, fixtures and original execution receipts remain unchanged. Broad
reference, Julia and wheel suites were **NOT RUN again locally** for this prose
follow-up; their original results remain attached to `187aa9f`. Human
implementation approval and merging remain pending.
