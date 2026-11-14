# ADR-P02 proposal review evidence

Date: 2026-11-14. Base revision: `d8379f7f32582b4c7a2ced678160041ce8e31ee0` (merged P01 PR #50).
Source was checked in a dirty issue #13 proposal branch before committing.
Source fingerprint: `2f1f146da0b80ba7d30804b71d656cdf3b3b641ef25dad0216833ce08c1c0ea1`.
Algorithm: SHA-256 of sorted relative path + NUL + bytes + NUL for all files
under `spec/fir/proposals/`, plus its FIR README and the approved-decision index.
This report is excluded.

Status: **PROPOSED; human PI ratification pending.** No normative FIR byte/digest
expectations, mathematical interpreter, compiler, solver or SSA propensity was
implemented. The P01 reference-implementation acceptance PR is separate.

## Executed checks

Runtime: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0;
Julia 1.10.13/JSON 1.13.4/JSONSchema 1.6.0. Prefix uv invocations with
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`.

| Check actually executed | Outcome |
|---|---|
| `uv run --project packages/python --locked --offline python -` with Draft7Validator.check_schema and example assertions | PASS; candidate meta-schema valid; production/decay example accepted; unsupported SSA declaration rejected; broken-reference example structurally accepted as intended |
| `julia --project=conformance/julia -e ...` with JSONSchema.Schema/validate on the same three example files | PASS; independent structural results match Python |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS |
| `git diff --check` | PASS |
| Mathematical/reference/unit consistency validator | NOT RUN; not implemented before ratification |
| FIR canonical bytes/digests | NOT RUN; require ADR-P03 |
| Scientific approval or independent numerical oracle | PENDING; proposal checks are not scientific ratification |

All final executed checks exited 0. The structurally accepted broken-reference
example is deliberately NOT called mathematically valid. A future independent
semantic validator must reject it; structural schema validation cannot resolve
mathematical references or establish reaction/equation consistency.

## Reproduction of the proposal-only structural assertions

Load `spec/fir/proposals/fir-m0.schema.json` into Draft7Validator or JSONSchema.
Validate `examples/production-decay.json` successfully; reject
`examples/invalid-ssa.json`; structurally accept `examples/invalid-reference.json`.
The proposal documents its expected semantic rejection separately.

No native package source/dependencies changed; package smoke tests were not
rerun for this proposal-only branch. No P01 fixture or approved content digest
was changed. Issue #13 must remain open until the proposal is explicitly ratified
and its scientific fixture/review requirements are satisfied.

## Merge update after P01 PR #51

Merged `origin/main` at `a3c73f2` (P01 PR #51) into the ADR-P02 proposal branch
whose previous head was `da30e11`. The only merge conflict was an append conflict
in `docs/approved-decisions.md`. Resolution preserves both main's P01 reference
implementation/evidence section and the P02 proposal section. The full P02
contract, candidate schema and example files are byte-identical to `da30e11`;
`git diff da30e11 --exit-code -- spec/fir/proposals` exited 0.

Post-resolution checks executed from the repository root:

- PASS: `uv run --project packages/python --locked --offline python scripts/check_repo.py`.
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` (6 tests).
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s conformance/python/tests -v` (6 tests including catalog subcases).
- PASS: `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` (2 smoke tests).
- PASS: `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p02-merge-python.json` (92 candidate cases).
- PASS: `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p02-merge-julia.json` (92 independent candidate cases).
- PASS: `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-p02-merge-python.json /private/tmp/fenix-p02-merge-julia.json` (92 matching cases).

uv invocations used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. Julia used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true`, and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`. Commands exited 0.
No new semantic/golden expectations were authored or ratified during this merge.
Historical proposal checks above still apply to the unchanged proposal files.

Resolved decision-index SHA-256: `72a7e2ed3401e1505cf90a24ca4af9e97f5f54c402052241dea500d034592c77`.

The unfiltered staged whitespace check flagged the intentional trailing spaces
and tab in `conformance/bioir/inputs/whitespace.input` imported from main. Its
bytes were confirmed identical to main and preserved. The staged formatting
check excludes only that one raw-input fixture; scientific fixture checks are
not excluded or changed. The normal working-tree whitespace check also passed.

## Identity, mapping and reaction–equation clarification

Date: 2026-11-14. Base revision:
`147c9c8a05e0087e9fb1e87f536cffa3bd1be1af`, existing branch
`docs/13-fir-p02-proposal`. Checks ran on the dirty proposal revision before
committing. The earlier evidence above is historical and is preserved.

Revised source fingerprint:
`97f61274429769c129d95f0c1e0d0f32324275f4371a31b1811de4fc724abce1`.
The algorithm is unchanged: SHA-256 of sorted relative path + NUL + bytes + NUL
for every file under `spec/fir/proposals/`, plus `spec/fir/README.md` and
`docs/approved-decisions.md` (20 files). This includes the new structural review
scripts and P02-local BioIR examples; this report is excluded. This is a source
fingerprint, not a FIR model digest or canonical vector.

Scope: proposed identity and producer/source-map contracts, reaction–equation
invariant and exact M0 consistency rules, illustrative positive/negative examples
and structural review scripts. No compiler, FIR semantic/provenance validator,
solver, normalization or hashing implementation was added. ADR-P02 remains
**PROPOSED; human PI ratification pending**.

Runtime: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0/rfc8785 0.1.4;
Julia 1.10.13/JSON 1.13.4/JSONSchema 1.6.0. All uv commands used
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`. All Julia commands used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no` in place of `julia`.
Commands ran independently from the repository root.

| Executed command/check | Outcome |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS; locked environment available without fetching |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; Draft-07 meta-schema check, all 9 FIR examples, 4 P01 source structures, identity/isolation and mapping assertions |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 42 independent structural assertions |
| Existing native P01 validators on original, GFP and LacI source pairs (commands below) | PASS in Python and Julia; exact Design references and both source content digests checked |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository links and harness |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| `git diff --exit-code 147c9c8a05e0087e9fb1e87f536cffa3bd1be1af -- spec/bioir conformance packages` | PASS; P01 specifications, fixtures, reference tools and package files unchanged |
| `git diff --check` and `git diff --cached --check` | PASS; proposal whitespace |
| FIR reference/role/unit/reaction–equation semantic validation and source-map resolution | NOT RUN; no implementation authorized before ratification |
| FIR normalization, bytes or hashes | NOT RUN; ADR-P03 required |
| Human PI ratification and independent scientific fixture/semantic review | PENDING |

Every executed final check above exited 0. The GFP and LacI complete `model`
objects equal each other and the base model; both BioIR source digests and the
mapped species differ. The standalone observable-renaming example differs only
at the semantic observable ID. No identity hash was computed to establish these
payload comparisons.

All three consistency negatives and the corrected RHS-reference negative pass
both structural validators. Whole-envelope comparisons against independently
mutated base copies confirm each contains only its documented defect, including
unchanged provenance. Their expected semantic rejection paths and reasons are in
the [example notes](../../spec/fir/proposals/examples/README.md). Structural
acceptance is not a claim of mathematical validity.

Both scripts reject absent/duplicate map entries, missing state-map fields,
wrong FIR state ID, missing qualifying Design digest and unsupported mapping
extensions. They accept standalone FIR and partial provenance, as required by
the general schema. They also structurally accept unresolved source species,
port and compartment IDs: post-ratification provenance validation must resolve
these against the exact supplied Design and check the species-scoped port and
compartment relationship. Compiler completeness remains a producer obligation,
not an origin flag or a structural-schema claim.

### Reproduce the separate P01 source checks

These commands exercise existing P01 tools only. They do not implement FIR
source-map resolution or change the P01 fixture catalog.

```sh
uv run --project packages/python --locked --offline python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'conformance/python')
from p01 import strict_parse, validate_design, validate_experiment
for directory, prefix in [(Path('spec/bioir/proposals/examples'), ''), (Path('spec/fir/proposals/examples/sources'), 'gfp-'), (Path('spec/fir/proposals/examples/sources'), 'laci-')]:
    design = strict_parse((directory / (prefix + 'design.json')).read_bytes())
    experiment = strict_parse((directory / (prefix + 'experiment.json')).read_bytes())
    validate_design(design)
    validate_experiment(experiment, design)
print('PASS: 3 exact P01 Design/Experiment pairs, including source content digests.')
PY
```

```sh
julia --project=conformance/julia - <<'JL'
include("conformance/julia/p01.jl")
using .P01Reference
for (directory, prefix) in [("spec/bioir/proposals/examples", ""), ("spec/fir/proposals/examples/sources", "gfp-"), ("spec/fir/proposals/examples/sources", "laci-")]
    design = strict_parse(read(joinpath(directory, prefix * "design.json")))
    experiment = strict_parse(read(joinpath(directory, prefix * "experiment.json")))
    validate_design(design)
    validate_experiment(experiment, design)
end
println("PASS: 3 exact P01 Design/Experiment pairs, including independently encoded source content digests.")
JL
```

No approved golden vectors were emitted or changed. Issue #13 remains subject
to human PI ratification and subsequent independent semantic validation; these
structural checks do not close that gate.

## Review response: abstract identity, parameter provenance and display labels

Date: 2026-11-14. Base revision:
`72f2f68cbcfd0fe16488980b2810591f296043ba`; branch
`docs/13-fir-p02-proposal`. Checks ran on the dirty proposal before committing.
All previous evidence is preserved as historical evidence of earlier revisions.

Source fingerprint:
`5e0fd82eee1ca540d21fbe6246202d9421a6954852781a3698a1e719a5a3a252`.
The unchanged fingerprint algorithm covers 30 files: sorted relative path +
NUL + bytes + NUL for all files under `spec/fir/proposals/`, the FIR README and
the approved-decision index. This report is excluded. This identifies reviewed
source files, not a FIR identity hash or canonical vector.

### Response to each concern

All four concerns are accepted without pushback. Changes are limited to proposed
contracts, illustrative fixtures, their structural review checks and this report.

| Concern | How addressed |
|---|---|
| High: abstract M0 state and equivalence limits | ADR-P02 explicitly calls `x` an abstract mathematical state. Complete resolved semantics and the named output interface determine identity; kinetics alone are insufficient. GFP/LacI may share mathematics without biological equivalence or interchangeability. General renaming and network isomorphism remain undefined. |
| High: state/parameter symbols mapped to BioIR entities and roles | The candidate schema now admits a complete provenance-only state/parameter map. Parameter entries identify the source parameter, function ID and function kind. The producer contract requires both source digests and complete maps; source-resolution, assignment/value/unit and role checks are documented separately. The new renamed-parameters source pair maps `k_prod`/`k_loss` and `synthesis`/`degradation` to fixed FIR symbols without changing the complete `model`. |
| Medium: semantic observable IDs versus display labels | Observable IDs explicitly form the semantic output interface. Optional `provenance.display_labels.observables` stores nonsemantic strings keyed by those IDs. Paired label examples preserve complete models and other provenance; the existing observable-ID rename changes the semantic payload. Labels inside model observables are structurally rejected. |
| Medium: expanded rejection fixtures | Six isolated mathematical consistency negatives now cover both signs, swapped rate references, a dimensionally valid wrong production role, reversed RHS and omitted decay. Two new provenance negatives cover missing source parameters and a wrong existing source function. Each case documents changed JSON Pointer paths and its expected rejection reason. |

The [ADR](../../spec/fir/proposals/ADR-P02.md) and
[fixture notes](../../spec/fir/proposals/examples/README.md) define the revised
contracts and cases. ADR-P02 remains **PROPOSED**. No scientific functionality,
FIR semantic/provenance validator, general symbolic algebra or FIR hashing was
implemented. The schema is still the unratified `0.1.0` candidate, not a migration
of any approved FIR contract. P01 content and existing P02 source revisions were
preserved; the renamed-parameters Design/Experiment pair has new illustrative
identities and P01 source digests, not FIR golden vectors.

### Executed verification

Runtime: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0/rfc8785 0.1.4;
Julia 1.10.13 with the unchanged locked reference environment. uv commands used
`UV_CACHE_DIR=/private/tmp/fenix-uv-cache`; Julia commands used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`. Commands ran from the
repository root; each final executed check exited 0.

| Executed command/check | Outcome |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; Draft-07 schema, 17 FIR examples, 6 source structures, mapping coverage/fields/order, labels and isolated mutations |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 79 independent structural assertions |
| Native P01 source-pair checks reproduced below | PASS in Python and Julia; 4 exact Design/Experiment pairs, including independently checked content digests |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p02-review-python.json` | PASS; 92 cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p02-review-julia.json` | PASS; 92 cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-p02-review-python.json /private/tmp/fenix-p02-review-julia.json` | PASS; 92 matching independent cases |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository links and harness |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| Diff against base for `spec/bioir`, `conformance`, `packages` and the four existing GFP/LacI source files | PASS; unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| FIR semantic and provenance resolution, including role, assignment and display-label target checks | NOT RUN; specified for post-ratification implementation and independent validation |
| FIR canonical bytes/hashes | NOT RUN; ADR-P03 required |
| Human PI ratification and independent scientific fixture approval | PENDING |

The structural scripts intentionally accept all six consistency negatives and
both new provenance negatives, proving only their structural validity and
isolation. They do not execute the future semantic rejection checks. Likewise,
a syntactically valid label key for an undeclared observable requires separate
provenance rejection. Complete mapping cardinality and required-field failures
are rejected structurally; standalone FIR without provenance remains accepted.

Source-pair commands (existing P01 tools only):

```sh
uv run --project packages/python --locked --offline python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0, 'conformance/python')
from p01 import strict_parse, validate_design, validate_experiment
pairs = [(Path('spec/bioir/proposals/examples'), '')] + [(Path('spec/fir/proposals/examples/sources'), prefix) for prefix in ('gfp-', 'laci-', 'renamed-parameters-')]
for directory, prefix in pairs:
    design = strict_parse((directory / (prefix + 'design.json')).read_bytes())
    experiment = strict_parse((directory / (prefix + 'experiment.json')).read_bytes())
    validate_design(design)
    validate_experiment(experiment, design)
print('PASS: 4 exact P01 Design/Experiment pairs, including source content digests.')
PY
```

```sh
julia --project=conformance/julia - <<'JL'
include("conformance/julia/p01.jl")
using .P01Reference
pairs = [("spec/bioir/proposals/examples", ""); [("spec/fir/proposals/examples/sources", prefix) for prefix in ("gfp-", "laci-", "renamed-parameters-")]]
for (directory, prefix) in pairs
    design = strict_parse(read(joinpath(directory, prefix * "design.json")))
    experiment = strict_parse(read(joinpath(directory, prefix * "experiment.json")))
    validate_design(design)
    validate_experiment(experiment, design)
end
println("PASS: 4 exact P01 Design/Experiment pairs, including independently encoded source content digests.")
JL
```

Issue #13 remains open for human PI ratification and subsequent independent
semantic validation. Passing structural or P01 reference checks does not approve
these FIR fixtures or introduce new scientific support.

## P1 review response: initial counts and exhaustive observables

Date: 2026-11-14. Base revision:
`40c82915568a807e6350abc90501b8d06dbdc63a`; branch
`docs/13-fir-p02-proposal`. Checks ran on the dirty proposal before committing.
Historical evidence above is preserved. Source fingerprint:
`6059f264cb2aed4ffeb85c9a5044958f79db370e6fa976d6a698579cea68b75a`.
The unchanged algorithm covers 39 files: sorted relative path + NUL + bytes + NUL
for every file under `spec/fir/proposals/`, the FIR README and approved-decision
index; this report is excluded. This is source evidence, not a FIR identity hash.

The two live Codex review comments on PR #52 were read through GitHub's public
review-comments API. Both findings are accepted without pushback:

| Finding | Response |
|---|---|
| [P1: initial value against Experiment](https://github.com/DRAGGON-Lab/FENIX/pull/52#discussion_r4574565070) | The producer contract now requires each mapped state's initial value and unit to equal its exact Experiment initial-count assignment. No defaults, tolerance, conversion or repair is allowed. A positive FIR declares source initial count 5; its isolated negative changes only FIR initial value to 0. |
| [P1: compiled observables against Experiment](https://github.com/DRAGGON-Lab/FENIX/pull/52#discussion_r4574565073) | The producer contract now requires exhaustive one-to-one observable IDs, mapped species/port-to-state targets and matching units. Empty source observables require an empty FIR list. Four isolated negatives cover invented, missing, renamed and wrong-target observables; a positive empty-observable pair is included. |

P01 observables do not contain a separate unit field. The contract explicitly
uses the source molecular-count port's `molecule` unit and requires the FIR
observable and mapped state units to match. The wrong-target fixture changes
only the observable state to `other`; M0 has no second valid state, so that
case also fails local FIR reference resolution. No broader state model or
diagnostic-precedence rule was invented to construct that fixture.

Two new P02-local Experiments have fresh illustrative identities, valid P01
content digests, and the unchanged P01 example Design reference. All existing
source documents, P01 files and fixtures, package files, and candidate FIR
schema are unchanged. The [fixture notes](../../spec/fir/proposals/examples/README.md)
give each negative's changed path and required rejection reason.
ADR-P02 remains **PROPOSED**. No FIR semantic/provenance validator, solver,
scientific capability, canonical bytes or hashes were implemented. Existing
standalone FIR behavior is preserved. Review-thread resolution state was not
changed; the corrections are supplied for reviewer confirmation.

### Executed checks

Environment is unchanged: uv 0.11.29, CPython 3.12.13/jsonschema 4.26.0/rfc8785
0.1.4; Julia 1.10.13 and its locked native reference dependencies. uv commands
used `UV_CACHE_DIR=/private/tmp/fenix-uv-cache`; Julia used
`JULIA_DEPOT_PATH=/private/tmp/fenix-julia-depot`, `JULIA_PKG_OFFLINE=true` and
`/private/tmp/julia-1.10.13/bin/julia --startup-file=no`. From the repository root:

| Command/check | Outcome |
|---|---|
| `uv sync --project packages/python --locked --offline` | PASS |
| `uv run --project packages/python --locked --offline python spec/fir/proposals/review_examples.py` | PASS; 24 FIR examples, 8 source structures, fixed-fixture equality/isolation and structural unit rejection checks |
| `julia --project=conformance/julia spec/fir/proposals/review_examples.jl` | PASS; 99 independent structural assertions |
| Native P01 Design/Experiment checks on 6 source pairs (reproduction below) | PASS in Python and Julia, including both new source content digests |
| `uv run --project packages/python --locked --offline python conformance/python/run_p01.py --report /private/tmp/fenix-p02-correspondence-python.json` | PASS; 92 cases |
| `julia --project=conformance/julia conformance/julia/run_p01.jl --report /private/tmp/fenix-p02-correspondence-julia.json` | PASS; 92 cases |
| `uv run --project packages/python --locked --offline python conformance/compare_reports.py /private/tmp/fenix-p02-correspondence-python.json /private/tmp/fenix-p02-correspondence-julia.json` | PASS; 92 matching cases |
| `uv run --project packages/python --locked --offline python scripts/check_repo.py` | PASS; repository links and harness |
| `uv run --project packages/python --locked --offline python -m unittest discover -s scripts/tests -v` | PASS; 6 tests |
| `uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v` | PASS; 2 smoke tests |
| `julia --project=packages/julia -e 'using Pkg; Pkg.instantiate(); Pkg.test()'` | PASS; 2 smoke tests |
| Diff against base for P01, conformance, packages, existing source documents and FIR schema | PASS; unchanged |
| `git diff --check` and `git diff --cached --check` | PASS |
| General FIR semantic/provenance validation against sources | NOT RUN; implementation and independent semantic validation remain gated on ratification |
| FIR canonicalization/digests and scientific approval | NOT RUN / PENDING; P03 and human approval required |

Every final executed check exited 0. Structural acceptance of the five new
negative FIR examples is intentional; the fixed-fixture comparisons establish
isolated mutations, not execution of the future source-correspondence validator.

Source validation used the existing native P01 tools only:

```sh
uv run --project packages/python --locked --offline python - <<'PY'
import sys
from pathlib import Path
sys.path.insert(0,'conformance/python')
from p01 import strict_parse, validate_design, validate_experiment
original=Path('spec/bioir/proposals/examples')
sources=Path('spec/fir/proposals/examples/sources')
pairs=[(original/'design.json',original/'experiment.json')]+[(sources/(prefix+'design.json'),sources/(prefix+'experiment.json')) for prefix in ('gfp-','laci-','renamed-parameters-')]+[(original/'design.json',sources/(name+'-experiment.json')) for name in ('initial-five','no-observables')]
for d,e in pairs:
    design=strict_parse(d.read_bytes()); experiment=strict_parse(e.read_bytes())
    validate_design(design); validate_experiment(experiment,design)
print('PASS: 6 exact P01 source pairs and content digests.')
PY
```

```sh
julia --project=conformance/julia - <<'JL'
include("conformance/julia/p01.jl")
using .P01Reference
original="spec/bioir/proposals/examples"
sources="spec/fir/proposals/examples/sources"
pairs=[(joinpath(original,"design.json"),joinpath(original,"experiment.json")); [(joinpath(sources,prefix*"design.json"),joinpath(sources,prefix*"experiment.json")) for prefix in ("gfp-","laci-","renamed-parameters-")]; [(joinpath(original,"design.json"),joinpath(sources,name*"-experiment.json")) for name in ("initial-five","no-observables")]]
for (d,e) in pairs
    design=strict_parse(read(d)); experiment=strict_parse(read(e))
    validate_design(design); validate_experiment(experiment,design)
end
println("PASS: 6 exact P01 source pairs and independently encoded content digests.")
JL
```
