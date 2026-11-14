# ADR-P01 review evidence and ratification record

The proposal checks below are historical. The final governance-update section
records subsequent human ratification and the outstanding fixture-catalog gate.

## Historical proposal checks before the three-concern revision

These results apply to the earlier source fingerprint below, not the revised
proposal. The subsequent review record covers the updated schema and examples.

Date: 2026-11-14. Tooling base: `5dbefafabc58510af40e47cb112dfa3aa3880cea`.
Proposal source fingerprint: `24514fb9cea349c8f330a0d50187e3fd07fe4f52b41a806d24a0bd21a08328a7` (SHA-256 of sorted relative
path + NUL + bytes + NUL for proposal files and the two index files, excluding
this report). Checks ran against the dirty proposal branch before committing.

Runtime: CPython 3.12.13, jsonschema 4.26.0, rfc8785 0.1.4;
Julia 1.10.13, JSON 1.13.4, JSONSchema 1.6.0; system Node.js.

## Executed checks

All final checks exited 0. These are proposal sanity checks only, not stable
APIs, approved fixtures, scientific semantic validation or empirical evidence.

| Check | Outcome |
|---|---|
| Python Draft7Validator.check_schema on the candidate schema | PASS |
| Python structural validation: Design and Experiment examples | PASS, 2 accepted |
| Python structural rejection probes: extra field, mM unit, nonempty interventions, newline in ID | PASS, 4 rejected |
| Julia JSONSchema.Schema and JSONSchema.validate on the same examples/probes | PASS, 2 accepted and 4 rejected |
| Independent ECMAScript/JCS and Node SHA-256 cross-check of both example content digests | PASS, both match the Python rfc8785 example calculations |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `git diff --check` | PASS |
| `git diff --exit-code -- conformance/julia/Project.toml conformance/julia/Manifest.toml` | PASS; repeated offline instantiation preserved environment files |
| Raw duplicate-key rejection, semantic/reference/capability validators | NOT RUN; implementation awaits PI ratification |
| Independent scientific review and human PI ratification | NOT RUN / PENDING |

The schema uses local fragment references only. No native FENIX package is
imported for these proposal checks. The candidate content hashes are illustrative
and must not become normative expectations without explicit review.

The Python check used the package environment interpreter and these operations:

```python
schema = json.loads(Path("spec/bioir/proposals/bioir-m0.schema.json").read_text())
Draft7Validator.check_schema(schema)
validator = Draft7Validator(schema)
# validate() on each example; is_valid() on deep-copied Experiment mutations:
# content.unknown = 1
# content.parameters[0].quantity.unit = "mM"
# content.interventions = [{"time": 1}]
# content.id = "baseline\n"
```

Julia used `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`,
`JULIA_PKG_OFFLINE=true`, and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no --project=conformance/julia -e ...`
with `JSONSchema.Schema(JSON.parsefile(...))`, asserting `validate(...) === nothing`
for both examples and `!== nothing` for the same four mutations (Julia index 1
for the first parameter). No custom semantic validation was executed.

The independent Node command used `node --input-type=module` with this reference
approach, based on RFC 8785 Appendix A; it did not use Python/FENIX output to
construct the canonical serialization:

```javascript
function jcs(v) {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(jcs).join(',') + ']';
  return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + jcs(v[k])).join(',') + '}';
}
// For each example: SHA-256(UTF-8(jcs(document.content))) === document.digest.
```

The full general numeric/Unicode vector suite and pinned upstream JavaScript
reference are #14/#16 work. This small independent example check does not
substitute for those gates. #12 remains open until scientific approval and its
post-ratification semantic validation requirements are met.


## Revised proposal: representation, execution separation and digest guarantees

Date: 2026-11-14. Status: **PROPOSED; PI ratification still pending**.
Base revision: `e710935822a1576a135696fd0e18f5c8b8b4c3f2`. Reviewed dirty-source fingerprint: `d6b785cbd9d5bee49c72bd496f22781651bfc8d4affd5b5e3c5a02926e1f0fe5`.
The fingerprint uses sorted relative path + NUL + bytes + NUL for all files
under `spec/bioir/proposals/`, plus `spec/bioir/README.md` and
`docs/approved-decisions.md`; this evidence report is excluded.

Changes: explicitly identify the initial M0-compatible subset and its extension
obligations; move requested execution profiles out of scientific Experiment
content; distinguish content identity, separately audited metadata/snapshots,
trusted-reference integrity and author authentication. No ExecutionSpec or
storage/provenance implementation was introduced.

The illustrative Experiment digest changed after removing `profile`. Its
`schema_version` remains `0.1.0` because this is an unratified proposal revision.
The Design example is byte-for-byte unchanged relative to the base revision.
No approved fixture, historical committed scientific document or normative
identity was rewritten. Earlier proposal bytes remain available in Git history.

### Executed checks

All commands below exited 0. Python ran under uv 0.11.29 / CPython 3.12.13 with
jsonschema 4.26.0 and rfc8785 0.1.4. Julia used 1.10.13 with JSON 1.13.4 and
JSONSchema 1.6.0 from its pinned environment; Node used v24.18.0.

| Exact command | Outcome |
|---|---|
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python /private/tmp/fenix-p01-revision-review.py` | PASS; meta-schema, 2 accepted examples, 8 structural rejection probes, digest boundary checks |
| `JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot JULIA_PKG_OFFLINE=true /private/tmp/julia-1.10.13/bin/julia --startup-file=no --project=conformance/julia /private/tmp/fenix-p01-revision-review.jl` | PASS; 2 accepted examples and the same 8 structural rejection probes |
| `node /private/tmp/fenix-p01-revision-review.cjs` | PASS; independently computed example digests and digest boundary checks |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `git diff --check` | PASS |
| Native package smoke tests | NOT RUN for this documentation/schema revision; native package code is unchanged |
| Semantic validators, scientific conformance, ODE/SSA execution and authentication | NOT RUN; these probes do not implement or establish those capabilities |
| Human PI ratification | PENDING |

Structural rejection probes cover the original unknown-field, invalid-unit,
nonempty-intervention and newline-ID cases, plus misplaced `profile: m0_ode`,
misplaced `profile: ssa`, a second species and a second compartment. The latter
two demonstrate subset boundaries, not a general BioIR-validity decision.

Python and Node independently verify the same digest properties for both
examples: metadata changes preserve scientific identity; content mutation breaks
comparison with the original digest; a recomputed replacement digest is
self-consistent but differs from the trusted original; illustrative execution
requests stored separately do not change scientific content identity. These
checks do not establish SSA admissibility, signatures or author authenticity.

### Exact review scripts

The scripts were executed as temporary review artifacts, not installed as
semantic validators or wired into scientific CI. Their contents are preserved
below so the checks can be reproduced after temporary files expire. The Python
baseline comparison deliberately names the original proposal commit rather than
the moving branch HEAD.

<details>
<summary>fenix-p01-revision-review.py</summary>

Artifact SHA-256: `b8e14a915e7645ab09b7ac19ea7275c90522c8e92e23d6899d63464cf762fea5`.

```python
import copy
import hashlib
import json
import subprocess
from pathlib import Path
import rfc8785
from jsonschema import Draft7Validator

p = Path('spec/bioir/proposals')
schema = json.loads((p / 'bioir-m0.schema.json').read_text())
Draft7Validator.check_schema(schema)
v = Draft7Validator(schema)
design = json.loads((p / 'examples/design.json').read_text())
experiment = json.loads((p / 'examples/experiment.json').read_text())
def digest(content):
    return hashlib.sha256(rfc8785.dumps(content)).hexdigest()
for doc in (design, experiment):
    v.validate(doc)
    assert digest(doc['content']) == doc['digest']
    annotated = copy.deepcopy(doc)
    annotated['metadata'] = {'description': 'Separately audited annotation'}
    v.validate(annotated)
    assert annotated != doc and digest(annotated['content']) == doc['digest']
    trusted = doc['digest']
    changed = copy.deepcopy(doc)
    changed['content']['revision'] += 1
    assert digest(changed['content']) != changed['digest']
    changed['digest'] = digest(changed['content'])
    assert changed['digest'] == digest(changed['content'])
    assert changed['digest'] != trusted
    # Requests stay outside scientific content; this grants no execution support.
    for request in ({'profile': 'ode'}, {'profile': 'ssa'}):
        run_input = {'experiment': doc, 'execution_request': request}
        assert digest(run_input['experiment']['content']) == trusted
cases = []
for name in ('unknown field', 'invalid unit', 'intervention', 'newline ID', 'ODE profile', 'SSA profile'):
    c = copy.deepcopy(experiment)
    if name == 'unknown field': c['content']['unknown'] = 1
    elif name == 'invalid unit': c['content']['parameters'][0]['quantity']['unit'] = 'mM'
    elif name == 'intervention': c['content']['interventions'] = [{'time': 1}]
    elif name == 'newline ID': c['content']['id'] = 'baseline\n'
    else: c['content']['profile'] = 'm0_ode' if name == 'ODE profile' else 'ssa'
    cases.append((name, c))
for collection in ('species', 'compartments'):
    c = copy.deepcopy(design)
    extra = copy.deepcopy(c['content'][collection][0])
    extra['id'] += '_second'
    c['content'][collection].append(extra)
    cases.append(('additional ' + collection, c))
for name, doc in cases:
    assert not v.is_valid(doc), name
baseline = subprocess.check_output(['git', 'show', 'e710935822a1576a135696fd0e18f5c8b8b4c3f2:spec/bioir/proposals/examples/design.json'])
assert baseline == (p / 'examples/design.json').read_bytes()
old_experiment = json.loads(subprocess.check_output(['git', 'show', 'e710935822a1576a135696fd0e18f5c8b8b4c3f2:spec/bioir/proposals/examples/experiment.json']))
assert old_experiment['digest'] != experiment['digest']
assert old_experiment['content']['schema_version'] == experiment['content']['schema_version'] == '0.1.0'
print('PASS: Draft-07 meta-schema; 2 accepted examples; 8 structural rejection probes.')
print('PASS: metadata/content/trusted-reference and separate execution-request digest probes for both documents.')
print('PASS: Design bytes/digest unchanged; Experiment digest changed; schema version unchanged.')
print('Proposal checks only: no semantic validation, approved vectors, authentication, ODE or SSA execution.')
```

</details>

<details>
<summary>fenix-p01-revision-review.jl</summary>

Artifact SHA-256: `2189c81034cd6ab16c21167bb2ffe8603544bd2b30ca76d1bfd4bba299097089`.

```julia
using JSON, JSONSchema
p = "spec/bioir/proposals"
schema = JSONSchema.Schema(JSON.parsefile(joinpath(p, "bioir-m0.schema.json")))
design = JSON.parsefile(joinpath(p, "examples/design.json"))
experiment = JSON.parsefile(joinpath(p, "examples/experiment.json"))
for doc in (design, experiment)
    @assert JSONSchema.validate(schema, doc) === nothing
end
for name in ("unknown field", "invalid unit", "intervention", "newline ID", "ODE profile", "SSA profile")
    c = deepcopy(experiment)
    if name == "unknown field"
        c["content"]["unknown"] = 1
    elseif name == "invalid unit"
        c["content"]["parameters"][1]["quantity"]["unit"] = "mM"
    elseif name == "intervention"
        c["content"]["interventions"] = [Dict("time" => 1)]
    elseif name == "newline ID"
        c["content"]["id"] = "baseline\n"
    else
        c["content"]["profile"] = name == "ODE profile" ? "m0_ode" : "ssa"
    end
    @assert JSONSchema.validate(schema, c) !== nothing
end
for collection in ("species", "compartments")
    c = deepcopy(design)
    extra = deepcopy(c["content"][collection][1])
    extra["id"] *= "_second"
    push!(c["content"][collection], extra)
    @assert JSONSchema.validate(schema, c) !== nothing
end
println("PASS: Julia structural checks: 2 accepted, 8 rejected. Not scientific conformance.")
```

</details>

<details>
<summary>fenix-p01-revision-review.cjs</summary>

Artifact SHA-256: `77ef7c3a9313035554860fb2e3a8f8235db9e79b61b4739d9c54fac37888f048`.

```javascript
const fs = require('node:fs');
const crypto = require('node:crypto');
const assert = require('node:assert/strict');
// Independent ECMAScript approach following RFC 8785 Appendix A.
function jcs(v) {
  if (v === null || typeof v !== 'object') return JSON.stringify(v);
  if (Array.isArray(v)) return '[' + v.map(jcs).join(',') + ']';
  return '{' + Object.keys(v).sort().map(k => JSON.stringify(k) + ':' + jcs(v[k])).join(',') + '}';
}
const digest = c => crypto.createHash('sha256').update(jcs(c), 'utf8').digest('hex');
for (const name of ['design', 'experiment']) {
  const doc = JSON.parse(fs.readFileSync(`spec/bioir/proposals/examples/${name}.json`, 'utf8'));
  assert.equal(digest(doc.content), doc.digest);
  const annotated = structuredClone(doc);
  annotated.metadata = {description: 'Separately audited annotation'};
  assert.equal(digest(annotated.content), doc.digest);
  const changed = structuredClone(doc);
  changed.content.revision += 1;
  assert.notEqual(digest(changed.content), changed.digest);
  changed.digest = digest(changed.content);
  assert.equal(digest(changed.content), changed.digest);
  assert.notEqual(changed.digest, doc.digest);
  for (const request of [{profile: 'ode'}, {profile: 'ssa'}]) {
    const runInput = {experiment: doc, executionRequest: request};
    assert.equal(digest(runInput.experiment.content), doc.digest);
  }
}
console.log('PASS: independent ECMAScript example digests and metadata/content/trusted-reference/execution separation probes. No approved golden vectors or execution support.');
```

</details>


## Governance update: human ratification and fixture-catalog gate

Date: 2026-11-14. Reviewed scientific-contract revision:
`35805663e3912f8858bbfbe0c178cf009c5454e2`.
The human PI explicitly approved ADR-P01 in this conversation and added the
language-neutral fixture-catalog acceptance requirement. The approval is
transcribed in the ADR; it is human approval, not agent self-ratification.
No public review URL or separate personal name was supplied.

Dirty-source fingerprint before commit: `c9e2427e62f2a6bcba6e9ae260436b341242629e94edfa962f75e6cf72956d8d`.
This SHA-256 covers sorted relative path + NUL + bytes + NUL for the changed
files listed by `git diff --name-only`, excluding this report. It identifies the
administrative status and acceptance-gate updates, not new scientific fixtures.

The schema's assertions, identifier and both example files remain unchanged.
Only schema title/comment status metadata changed. Numeric, Unicode and digest
rules were not redesigned. The user-approved gate is recorded in the ADR and
conformance requirements, assigned principally to follow-on issues #16 and #17.
It requires original inputs, explicit acceptance/rejection, reviewed categories
and independent Python/Julia reports before validator implementation approval.
No catalog, new error taxonomy, native validator or normative vector was created.

Checks executed from the repository root, all final commands exiting 0:

| Command / check | Outcome |
|---|---|
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS, 6 tests |
| `UV_CACHE_DIR=/private/tmp/fenix-uv-cache uv run --project packages/python --locked --offline python -` with administrative assertions | PASS; schema equals reviewed schema after excluding title/comment; both examples byte-identical to reviewed revision; Draft-07 schema valid; both examples structurally valid; both existing digests match external rfc8785/SHA-256 calculations; ratification revision and gate present |
| `git diff --check` | PASS |
| Native package tests and native scientific validation | NOT RUN for this documentation/status-only change; native package source and schema assertions unchanged |
| Language-neutral catalog and independent implementation acceptance reports | NOT RUN / PENDING; required follow-on work |

Runtime: uv 0.11.29, CPython 3.12.13, jsonschema 4.26.0, rfc8785 0.1.4.
Historical PENDING ratification entries above describe their original runs; the
current contract status is RATIFIED. Fixture review, golden-vector approval and
validator implementation acceptance remain outstanding. Issue #12 and epic #3
are not recorded as complete by this governance update.
