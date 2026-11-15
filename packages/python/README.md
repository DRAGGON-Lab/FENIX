# Native Python M0 BioIR content

Provisional distribution `fenix-bio`, module `fenix`, version `0.0.0`, pending
package governance ADR-P06. Python 3.12+; no runtime dependencies or Julia required.

`fenix.bioir` provides immutable, keyword-only dataclasses for the ratified
[P01 M0 subset](../../spec/bioir/proposals/ADR-P01.md). `DesignContent` and
`ExperimentContent` are **uncommitted content objects**. Construction validates
native values and local references. `to_dict()` returns fresh dictionaries/lists;
`to_json()` emits ordinary JSON with `allow_nan=False`, preserving declaration
order and accepted numeric values without sorting or normalization.

```python
from fenix.bioir import (
    Compartment, DesignContent, DesignReference, ExperimentContent, Function,
    InitialCount, Observable, Parameter, ParameterAssignment, Port, PortReference,
    Quantity, Species,
)

target = PortReference(species="x", port="amount")
design = DesignContent(
    id="production_decay", revision=1,
    compartments=(Compartment(id="cell", volume=Quantity(value=1e-15, unit="L")),),
    species=(Species(id="x", compartment="cell", ports=(Port(id="amount"),)),),
    parameters=(Parameter(id="alpha", unit="molecule/s"), Parameter(id="beta", unit="1/s")),
    functions=(
        Function(id="production", kind="constitutive_production", target=target, parameter="alpha"),
        Function(id="decay", kind="first_order_decay", target=target, parameter="beta"),
    ),
)

# Syntactically valid placeholder only: this API cannot commit or hash a Design.
claimed_reference = DesignReference(id=design.id, revision=design.revision, digest="0" * 64)
experiment = ExperimentContent(
    id="baseline", revision=1, design=claimed_reference, source_design=design,
    parameters=(
        ParameterAssignment(parameter="alpha", quantity=Quantity(value=10, unit="molecule/s")),
        ParameterAssignment(parameter="beta", quantity=Quantity(value=0, unit="1/s")),
    ),
    initial_counts=(InitialCount(species="x", quantity=Quantity(value=0.5, unit="molecule")),),
    observables=(Observable(id="amount_x", target=target),),
    interventions=(),
)
content_json = experiment.to_json()
```

All IDs, revisions, quantities and collections are explicit. Only fixed `kind`
and `schema_version` tokens have defaults. Collections require tuples of exact
native value types; lists, mappings and subclasses are rejected as nested values.
`Quantity` accepts built-in `int`/`float` only, excluding booleans, nonfinite values
and integers outside `[-(2^53-1), 2^53-1]`. Quantities are nonnegative; compartment
volume must be positive. Exact units are `L`, `molecule`, `molecule/s`, `1/s`,
with role checks and no implicit conversion. Zero rates, fractional expected
counts, signed zero, positive subnormals and empty observables are accepted.

`source_design` is required validation context, neither stored nor serialized.
The reference ID/revision must match it; digest syntax is checked, but **digest
correspondence and trusted revision identity remain unverified**. Rebuilding an
Experiment (including `dataclasses.replace`) requires supplying `source_design`
again. Frozen content does not establish an archive of immutable committed revisions.

Failures raise `BioIRValidationError(ValueError)` with `category`, `path` and a
readable message. Paths are JSON Pointers relative to the constructor that failed:
`Quantity(value=-1, unit="molecule")` reports `/value`; an unresolved function port
at Design construction reports `/functions/0/target/port`. Unknown keywords,
missing arguments and positional arguments retain Python's `TypeError`.
One primary diagnostic is returned; multiply invalid inputs have no universal
error precedence guarantee. Categories follow the applicable P01 reference names;
native nonfinite quantities use `NUMBER_RANGE` and oversized integers use
`INTEGER_RANGE`. Structural and role-local quantity violations use `SCHEMA`.

Raw JSON parsing, duplicate keys, malformed Unicode, token overflow/underflow,
canonical bytes/digests, envelopes and exact committed Design references belong
to [#19](https://github.com/DRAGGON-Lab/FENIX/issues/19). Python literals have already
lost raw-token information; e.g. an underflowed literal is indistinguishable from
zero at this boundary. No FIR, compiler, execution, results or wider BioIR support
is supplied. Accepted fractional counts do not establish SSA eligibility.

## Development checks

```sh
uv sync --project packages/python --locked
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests -v
uv run --project packages/python --locked --offline python -m unittest discover -s packages/python/tests_native_content -v
uv run --project packages/python --locked --offline ruff check packages/python/src/fenix/bioir packages/python/tests/test_bioir.py packages/python/tests_native_content
uv run --project packages/python --locked --offline ruff format --check packages/python/src/fenix/bioir packages/python/tests/test_bioir.py packages/python/tests_native_content
uv run --project packages/python --locked --offline mypy --config-file packages/python/pyproject.toml
```

Ruff targets Python 3.12 on the new code/tests. Strict mypy checks `fenix.bioir`
through the editable installation, with the shipped `py.typed` marker and no
blanket missing-import suppression. Configuration follows the
[official Ruff configuration](https://docs.astral.sh/ruff/configuration/) and
[mypy import guidance](https://mypy.readthedocs.io/en/stable/running_mypy.html).
Ruff, mypy, jsonschema and rfc8785 are locked development tools only.

The separate native-content suite uses a test-only structural adapter and
`jsonschema` to check **29 content projections** from the approved 92-case P01
catalog. [Coverage](tests_native_content/coverage.json) lists all 63 deferred cases
and reasons. Detailed paths use the corresponding accepted rejection-suite
expectations, translating constructor locations and `/content` explicitly.
Metadata variants exercise content only. This is not full native 92-case
conformance, biological validation or implementation approval. Both original
catalogs and fixture bytes remain unchanged. The package tests run against an
editable install and a clean wheel without development dependencies in CI.
