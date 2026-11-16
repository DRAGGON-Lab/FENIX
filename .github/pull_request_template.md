## Objective and linked issue

One issue; describe expected behavior and explicit non-goals. Use `Refs #29 and #42` for non-closing references. Reserve closing keywords for work satisfying the referenced issue’s acceptance criteria; avoid closing-keyword phrases even in negated sentences. Parent scientific/release closure requires explicit human PI acceptance.

## Scientific contract review

- Approved decisions / ADR(s):
- Changes BioIR/FIR semantics, units, canonicalization, capability declarations, mathematical golden data or compatibility? **Yes / No**
- If yes, link **human PI-approved ADR**, independent references and updated test evidence before merging.

## Changes and dependencies

List touched files and why. Document new dependencies and compatibility impact.

## Agentic review and verification

- [ ] Checked applicable root and scoped `AGENTS.md` instructions
- [ ] Updated source-of-truth docs without adding duplicate policy files
- [ ] Ran `uv run --project packages/python --locked --offline python scripts/check_repo.py` or recorded why not
- [ ] Ran `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` or recorded why not

## Tests actually executed

| Runtime | Exact command | Outcome |
|---|---|---|
| Python-only | | Not run |
| Julia-only | | Not run |
| Mathematical conformance | | Not run |

## Positive/negative behavior and scientific evidence

State expected success and rejection cases, assumptions and numeric tolerances if applicable.

## Review checklist

- [ ] No unapproved normative or golden-vector changes
- [ ] Independent installation boundaries preserved
- [ ] No unsafe serialized callbacks or committed secrets
- [ ] Small focused change; no unrelated refactors
- [ ] Documentation updated
- [ ] Human review and CI results considered before merge

## Limitations / follow-ups
