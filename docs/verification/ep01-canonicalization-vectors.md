# EP-01 canonicalization reference-vector evidence — REVIEW_REQUIRED

Issue [#16](https://github.com/DRAGGON-Lab/FENIX/issues/16), M-1 / EP-01.
Date: 2026-11-14. Branch: `conformance/16-canonicalization-vectors`.
Base: `origin/main` at `a599077740b5d1759bb4d7a4868aafcd37abdf69`, including
merged PR #54. The [ADR-P03 contract](../../spec/canonicalization/proposals/ADR-P03.md)
is ratified and unchanged. The concrete [catalog](../../conformance/canonicalization/catalog.json)
remains **REVIEW_REQUIRED**; issue #16 stays open pending human PI acceptance.
Plan approval does not approve fixture expectations or native implementations.

## Scope and source identity

One implementer owns the existing catalog/schema, Python and ECMAScript reference
checkers, tests, CI and documentation. New expectations are explicitly authored
candidate byte strings under the ratified contract, followed by independent
verification. No native parser, FIR normalization/validation, compiler, solver,
broader #17 rejection implementation, package source or scientific rule changes.
All 137 prior input/normalized/canonical fixture files and all 67 prior catalog
case records are unchanged. Earlier [P03 proposal evidence](ep01-p03-proposal.md)
is historical and has not been rewritten.

Verification ran on the dirty issue branch at the base revision above. Source
fingerprint: `630be4a98940cf6b1bc33690071878ba50c459c63ac1e5bb9ee49ce4166123b3`.
Algorithm: SHA-256 of sorted repository-relative path + NUL + exact bytes + NUL,
over all non-cache files under `conformance/canonicalization/`, plus
`.github/workflows/scaffold-smoke.yml`, `conformance/README.md` and
`spec/canonicalization/README.md` (182 files). This evidence record and its report
outputs are excluded to avoid a circular fingerprint. This records source
provenance, not FIR identity or execution authentication.

Runtime versions: uv **0.11.29**; CPython **3.12.13**; external `rfc8785` **0.1.4**;
`jsonschema` **4.26.0**; Node **24.18.0**, V8 **13.6.233.17-node.50**;
Julia **1.10.13** for existing checks. No dependency or lockfile changes.
Python uses the existing locked development environment. Commands below run
from repository root. `julia` denotes
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no` with
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot` and `JULIA_PKG_OFFLINE=true`.

## Vector preparation and requirement coverage

Sources: [RFC 8785](https://www.rfc-editor.org/rfc/rfc8785.html), sections 3.1,
3.2.2.2, 3.2.2.3 and 3.2.3, Appendices A/B, and the ratified P03 numeric,
Unicode and identity rules. New candidate expectations were written as explicit
UTF-8 strings before either oracle ran; neither shipped checker generated them.
No fixture regeneration command is provided. Per-case `reference` records the
rule and rationale; catalog artifact records contain exact input/output hashes.

| Requirement | Executable IDs and fixed behavior |
|---|---|
| UTF-16 key ordering | Existing `unicode-order`; new `nested-utf16-keys`: recursively order `1`, `10`, `2`, U+1F600, U+E000. The supplementary key's first UTF-16 unit D83D precedes E000. |
| Signed zero | New raw `raw-zero` (`0`), `raw-negative-zero` (`-0`), existing `signed-zero` (`-0.0`), all emit `0`. |
| Numeric spelling | New `number-one`, `number-one-decimal`, `number-one-exponent`: raw `1`, `1.0`, `1e0` all emit `1`. |
| Exponent thresholds | New `exponent-minus-seven`, `exponent-minus-six`, `exponent-twenty`, `exponent-twenty-one`: `1e-7`, `0.000001`, `100000000000000000000`, `1e+21`. |
| Subnormals | Existing Appendix B bit vectors `rfc-0000000000000001`, `rfc-8000000000000001`, emitting `5e-324`, `-5e-324`. |
| Nonfinite rejection | Existing NaN `rfc-7fffffffffffffff` and infinity `rfc-7ff0000000000000`; new negative infinity `rfc-fff0000000000000`. The sign counterpart has exponent 7ff and zero fraction; rejection follows section 3.2.2.3. |
| Unicode preservation | Existing `composed`, `decomposed`, `escapes`; new `escaped-composed` (raw escaped U+00E9) equals literal `composed`, while decomposed bytes remain distinct. |
| Array ordering | New `array-forward` and `array-reversed` emit distinct arrays `[3,{"a":1,"z":2},1]` and `[1,{"a":1,"z":2},3]`; only the object's properties sort. |
| Binary64 integer boundary | New `boundary-below`, `boundary-exact`, existing `large-rounding`, new `boundary-above-two`: raw 2^53−1, 2^53, 2^53+1, 2^53+2 emit 9007199254740991, 9007199254740992, 9007199254740992, 9007199254740994. The halfway odd value rounds ties-to-even. |

The schema-validated `coverage` map has exactly these nine required categories.
Both checkers reject unknown references, duplicate IDs/references and coverage
consisting solely of contract_only cases. Tests pin the concrete coverage above.
Orphaned input and expectation files fail. The catalog now has **84 cases**:
27 binary64, 27 JSON JCS, 13 FIR identity and 17 contract_only. Both reports show
**63 PASS, 4 REJECT_CONFIRMED, 17 NOT_RUN**.

FIR identity checks serialize the supplied expected normalized object; they do
not transform the original input. Tests retain all six expected declaration-order
checks and existing identity relationships, including the observable permutation
pair. Native semantic validation, normalization, idempotence and end-to-end round
trips remain **NOT RUN**. Cross-language agreement is not biological validation.

## Reports, integrity and failure checks

Report format version `1` records runtime/serializer identity, implementation,
catalog/schema/evaluator checksums and each case's stage. Successful rows carry
actual `canonical_hex` and SHA-256. FIR identity rows additionally carry actual
`model_canonical_hex` and SHA-256. Rejected/unexecuted rows claim no output bytes.
The comparator requires exactly the registered Python and ECMAScript identities,
complete unique case coverage, current provenance and exact stage/status/byte/digest
agreement with the fixed artifacts; row order is irrelevant. Runtime versions
are recorded, with identity/format checks, not independently attested.

Python uses external `rfc8785`; Node independently implements the Appendix A
recursive sorting with ECMAScript primitive serialization and nonfinite/Unicode
guards. Neither invokes the other or imports FENIX. Both retain direct output-byte
comparisons. Python checks the JSON Schema; Node mirrors its boundary constraints
without dependencies. Both protect catalog/schema/evaluator files and fixture
directories against report overwrites, including symlink and hard-link aliases.

| Executed artifact | SHA-256 |
|---|---|
| Catalog, including exact per-fixture hashes | `dc4c17a08b623d0d3a46e134d9b5457c357783a92fc71211a2f9d4e24b38fa15` |
| Catalog schema | `8852b54516c13cdc84db9d225e88229ba9795052e95c1511bdb9ef66dd3ebc3b` |
| Python evaluator | `7ec483f8cf81c3f8827a180719b93ddda981b7f277125a74a609dd6416d313e5` |
| ECMAScript evaluator | `ab6dfd494ede4015c88fefa0833ddac859e300d09036467d712cb56199d386c3` |
| [Python report](canonicalization-vectors-python.json) | `5959e014066099c359eb9dd25cd06064b974edaf0064e9f2af473f334674288d` |
| [Node report](canonicalization-vectors-node.json) | `fe03c90f8ed11d04870d51dd90995e15f0b9f86902883b8421deab2796e8f079` |

Regressions preceded checker changes. The initial Python run had 12 failing
subcases and 6 errors across 10 tests; the Node test module failed because the
old checker ran its CLI on import. Failures included accepted protected-output
writes and missing provenance/coverage boundaries. The later boolean report
version regression failed separately (`true` compared equal to integer `1`);
strict version typing fixes it. Final results below supersede these expected
initial failures. No prior expected fixture was changed to resolve a failure.

Failure regressions cover missing/duplicate/extra report rows, modified bytes or
digests, stale catalog/schema/evaluator provenance, invalid runtime/implementation
identities, false normalization success, output attached to rejection/unexecuted
rows, invalid stage/outcome field combinations, missing/unknown/duplicate coverage,
orphaned/corrupt artifacts and protected outputs. A pair of reports that agree
on wrong bytes and the corresponding wrong digest still fails. Rehashed wrong
identity/model artifacts fail direct comparison within both independent oracles.
The Python boundary suite runs the real Node CLI against copied catalogs; its
coverage and overwrite subcases therefore exercise both checkers.

## Executed verification

All completed checks below exited **0**. Initial failing regressions are recorded
above. The Julia commands use the cached offline reference depot noted earlier.

| Exact command/check | Outcome |
|---|---|
| `uv sync --project packages/python --locked` | PASS; existing eight packages |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --report docs/verification/canonicalization-vectors-python.json` | PASS; 84 cases |
| `node conformance/canonicalization/review_p03.cjs --report docs/verification/canonicalization-vectors-node.json` | PASS; 84 cases |
| `uv run --project packages/python --locked --offline python conformance/canonicalization/review_p03.py --compare docs/verification/canonicalization-vectors-python.json docs/verification/canonicalization-vectors-node.json` | PASS; all fixed bytes/digests/statuses match |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/canonicalization/tests -v` | PASS; 14 tests with mutation subcases |
| `node --test conformance/canonicalization/tests/test_review.cjs` | PASS; 4 tests |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository and links |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 harness tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 package smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 package smoke assertions |
| `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` | PASS; 6 P01 tests |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-16-p01-python.json` | PASS; 92 existing cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-16-p01-julia.json` | PASS; 92 existing cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-16-p01-python.json /private/tmp/fenix-16-p01-julia.json` | PASS; 92 independent outcomes match |
| `node conformance/reference/check_p01.cjs` | PASS; 41 existing canonical/digest cases |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; 24 FIR examples, 8 source structures (structural checks) |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 99 structural assertions |
| Ruby standard-library YAML parse and P03 Node-test step check | PASS; CI parses and contains Node test command |
| Baseline byte/case-record comparison against `origin/main` | PASS; 137 old fixture files and 67 old case records identical |
| `git diff --exit-code origin/main -- spec/canonicalization/proposals spec/fir spec/bioir packages conformance/bioir conformance/python conformance/julia conformance/production_decay conformance/reference conformance/compare_reports.py docs/approved-decisions.md docs/verification/ep01-p03-proposal.md` | PASS; contracts, packages, unrelated catalogs and historical P03 evidence unchanged |
| `git diff --check` | PASS |
| `git diff --cached --check` | PASS; staged issue changes |
| Hosted GitHub Actions | NOT RUN locally; existing P03 job extended with Node tests and separate Python/Node report uploads |
| Native FIR validation/normalization and all 17 contract_only outcomes | NOT RUN; outside scope |
| Human PI acceptance of concrete vectors | NOT RUN; REVIEW_REQUIRED, issue #16 remains open |

## Separate read-only review

A separate read-only scientific reviewer reproduced the initial fingerprint,
all six artifact hashes, prior-byte/case-record preservation, both reference test
suites and saved-report comparison. No concrete vector expectation defect was
found against RFC 8785/P03. The reviewer found a Python boundary defect: a
rehashed malformed UTF-8 binary64 input could be caught as an expected nonfinite
serialization rejection, while Node correctly failed artifact bit equality.
A new regression reproduced the false REJECT_CONFIRMED before the fix. Binary64
input equality now checks exact ASCII bytes outside the serialization rejection
handler. All 14 Python tests pass after the fix, both reports were refreshed,
and all output case rows remain unchanged. The README now distinguishes the
derived negative-infinity bit pattern from published Appendix B rows.

Final separate read-only review confirmed the fix, refreshed source/artifact
identities, all 14 Python tests, 4 Node tests, saved-report comparison and
whitespace checks. There are no unresolved review findings.
Agent review does not approve scientific fixtures; final concrete-vector
acceptance belongs to the human PI. No native implementation or follow-on issue
is authorized by this PR.

The read-only source/fixture audit above is reproducible with this exact command:

```sh
python3 - <<'PY'
from pathlib import Path
import hashlib, json, subprocess
base='a599077740b5d1759bb4d7a4868aafcd37abdf69'
root=Path('conformance/canonicalization')
paths=sorted([p for p in root.rglob('*') if p.is_file() and '__pycache__' not in p.parts]
             +list(map(Path,['.github/workflows/scaffold-smoke.yml','conformance/README.md','spec/canonicalization/README.md'])))
fingerprint=hashlib.sha256()
for p in paths:
    fingerprint.update(p.as_posix().encode()+b'\0'+p.read_bytes()+b'\0')
print('Source fingerprint:',len(paths),fingerprint.hexdigest())
old=json.loads(subprocess.check_output(['git','show',base+':'+str(root/'catalog.json')]))
new=json.loads((root/'catalog.json').read_bytes())
assert new['cases'][:len(old['cases'])]==old['cases']
old_paths=subprocess.check_output(['git','ls-tree','-r','--name-only',base,str(root/'inputs'),str(root/'expected')]).decode().splitlines()
for name in old_paths:
    assert Path(name).read_bytes()==subprocess.check_output(['git','show',base+':'+name]),name
print('PASS:',len(old_paths),'prior fixture files and',len(old['cases']),'prior cases unchanged')
PY
```
