# ADR-P01 proposal review evidence — not ratification

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
