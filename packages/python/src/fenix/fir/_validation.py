"""Independent native P02 mathematical and exact-source validation.

Checks recognize the ratified templates directly; they never execute, simplify,
repair or normalize scientific input. Repository schemas and reference programs
are not runtime dependencies.
"""

from __future__ import annotations

import math
import re
from typing import Any

from ..bioir import DesignDocument, ExperimentDocument
from ..bioir._json import pointer
from ._errors import FIRValidationError

_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_ASSUMPTIONS = frozenset(
    (
        "single_representative_cell",
        "well_mixed",
        "fixed_volume",
        "constant_rates",
        "no_interventions",
    )
)


def _need(condition: bool, path: str, message: str, category: str = "SCHEMA") -> None:
    if not condition:
        raise FIRValidationError(category, path, message)


def _object(
    value: object, required: tuple[str, ...], path: str, optional: tuple[str, ...] = ()
) -> dict[str, Any]:
    _need(type(value) is dict, path, "expected an object")
    assert isinstance(value, dict)
    for key in required:
        _need(key in value, pointer(path, key), "required member is missing")
    for key in value:
        _need(type(key) is str, path, "expected string member names")
        _need(key in required or key in optional, pointer(path, key), "unknown member")
    return value


def _text(value: object, path: str, allowed: tuple[str, ...] | None = None) -> None:
    _need(type(value) is str, path, "expected a string")
    assert isinstance(value, str)
    try:
        value.encode("utf-8", errors="strict")
    except UnicodeEncodeError:
        raise FIRValidationError(
            "INVALID_UNICODE", path, "unpaired Unicode surrogate"
        ) from None
    if allowed is not None:
        _need(value in allowed, path, f"expected one of {allowed}")


def _id(value: object, path: str) -> None:
    _text(value, path)
    assert isinstance(value, str)
    _need(_ID.fullmatch(value) is not None, path, "expected an ASCII identifier")


def _number(value: object, path: str, nonnegative: bool = True) -> None:
    _need(type(value) is float, path, "expected an already represented binary64 float")
    assert isinstance(value, float)
    _need(math.isfinite(value), path, "expected a finite binary64 float")
    if nonnegative:
        _need(value >= 0, path, "expected a nonnegative quantity")


def _array(value: object, path: str, size: int | None = None) -> list[Any]:
    _need(type(value) is list, path, "expected an array")
    assert isinstance(value, list)
    if size is not None:
        _need(len(value) == size, path, f"M0 requires exactly {size} entries")
    return value


def _expression(value: object, path: str) -> dict[str, Any]:
    _need(type(value) is dict, path, "expected an expression object")
    assert isinstance(value, dict)
    _need("op" in value, path + "/op", "expression operation is required")
    operation = value["op"]
    _text(operation, path + "/op", ("parameter", "state", "multiply", "subtract"))
    if operation in ("parameter", "state"):
        expr = _object(value, ("op", "id"), path)
        _id(expr["id"], path + "/id")
    else:
        expr = _object(value, ("op", "left", "right"), path)
        for side in ("left", "right"):
            _expression(expr[side], path + "/" + side)
    return expr


def _structure_model(value: object) -> dict[str, Any]:
    path = "/model"
    model = _object(
        value,
        (
            "schema_version",
            "time_unit",
            "states",
            "parameters",
            "reactions",
            "equations",
            "observables",
            "assumptions",
            "capabilities",
        ),
        path,
    )
    _text(model["schema_version"], path + "/schema_version", ("0.1.0",))
    _text(model["time_unit"], path + "/time_unit", ("s",))
    for i, raw in enumerate(_array(model["states"], path + "/states", 1)):
        p = f"{path}/states/{i}"
        state = _object(raw, ("id", "quantity", "scope", "unit", "initial"), p)
        for key, token in (
            ("id", "x"),
            ("quantity", "molecular_count"),
            ("scope", "representative_cell"),
            ("unit", "molecule"),
        ):
            _text(state[key], p + "/" + key, (token,))
        _number(state["initial"], p + "/initial")
    for i, raw in enumerate(_array(model["parameters"], path + "/parameters", 2)):
        p = f"{path}/parameters/{i}"
        parameter = _object(raw, ("id", "value", "unit"), p)
        _text(parameter["id"], p + "/id", ("alpha", "beta"))
        _number(parameter["value"], p + "/value")
        _text(parameter["unit"], p + "/unit", ("molecule/s", "1/s"))
    for i, raw in enumerate(_array(model["reactions"], path + "/reactions", 2)):
        p = f"{path}/reactions/{i}"
        reaction = _object(raw, ("id", "stoichiometry", "flux"), p)
        _text(reaction["id"], p + "/id", ("production", "decay"))
        stoichiometry = _object(reaction["stoichiometry"], ("x",), p + "/stoichiometry")
        _number(stoichiometry["x"], p + "/stoichiometry/x", nonnegative=False)
        _need(
            stoichiometry["x"] in (-1.0, 1.0),
            p + "/stoichiometry/x",
            "M0 stoichiometry must be +1 or -1",
        )
        _expression(reaction["flux"], p + "/flux")
    for i, raw in enumerate(_array(model["equations"], path + "/equations", 1)):
        p = f"{path}/equations/{i}"
        equation = _object(raw, ("state", "unit", "rhs"), p)
        _id(equation["state"], p + "/state")
        _text(equation["unit"], p + "/unit", ("molecule/s",))
        _expression(equation["rhs"], p + "/rhs")
    for i, raw in enumerate(_array(model["observables"], path + "/observables")):
        p = f"{path}/observables/{i}"
        observable = _object(raw, ("id", "state", "unit"), p)
        _id(observable["id"], p + "/id")
        _id(observable["state"], p + "/state")
        _text(observable["unit"], p + "/unit", ("molecule",))
    assumptions = _array(model["assumptions"], path + "/assumptions", 5)
    _need(
        all(type(a) is str and a in _ASSUMPTIONS for a in assumptions)
        and len(set(assumptions)) == 5,
        path + "/assumptions",
        "expected the five distinct M0 assumptions",
    )
    capabilities = _object(
        model["capabilities"], ("ode", "ssa"), path + "/capabilities"
    )
    for key, expected in (("ode", True), ("ssa", False)):
        _need(
            capabilities[key] is expected,
            path + "/capabilities/" + key,
            "unsupported M0 capability declaration",
        )
    return model


def _unique(values: list[Any], key: str, path: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for i, item in enumerate(values):
        _need(
            item[key] not in result,
            f"{path}/{i}/{key}",
            "duplicate identifier",
            "DUPLICATE_ID",
        )
        result[item[key]] = item
    return result


def _semantics(model: dict[str, Any]) -> None:
    states = _unique(model["states"], "id", "/model/states")
    parameters = _unique(model["parameters"], "id", "/model/parameters")
    reactions = _unique(model["reactions"], "id", "/model/reactions")
    equations = _unique(model["equations"], "state", "/model/equations")
    _unique(model["observables"], "id", "/model/observables")
    _need(
        set(parameters) == {"alpha", "beta"},
        "/model/parameters",
        "required parameter roles are missing",
        "ROLE",
    )
    _need(
        set(reactions) == {"production", "decay"},
        "/model/reactions",
        "required reaction roles are missing",
        "ROLE",
    )
    _need(
        set(equations) == {"x"},
        "/model/equations/0/state",
        "unknown equation state",
        "REFERENCE",
    )
    for i, parameter in enumerate(model["parameters"]):
        unit = "molecule/s" if parameter["id"] == "alpha" else "1/s"
        _need(
            parameter["unit"] == unit,
            f"/model/parameters/{i}/unit",
            "unit differs from parameter role",
            "UNIT",
        )

    def references(expr: dict[str, Any], path: str) -> None:
        if expr["op"] in ("parameter", "state"):
            namespace = parameters if expr["op"] == "parameter" else states
            _need(
                expr["id"] in namespace,
                path + "/id",
                "unresolved typed reference",
                "REFERENCE",
            )
        else:
            references(expr["left"], path + "/left")
            references(expr["right"], path + "/right")

    for collection, field in (("reactions", "flux"), ("equations", "rhs")):
        for i, item in enumerate(model[collection]):
            references(item[field], f"/model/{collection}/{i}/{field}")
    for i, observable in enumerate(model["observables"]):
        _need(
            observable["state"] in states,
            f"/model/observables/{i}/state",
            "unknown observable state",
            "REFERENCE",
        )
    alpha = {"op": "parameter", "id": "alpha"}
    decay = {
        "op": "multiply",
        "left": {"op": "parameter", "id": "beta"},
        "right": {"op": "state", "id": "x"},
    }
    for i, reaction in enumerate(model["reactions"]):
        production = reaction["id"] == "production"
        p = f"/model/reactions/{i}"
        _need(
            reaction["stoichiometry"]["x"] == (1.0 if production else -1.0),
            p + "/stoichiometry/x",
            "stoichiometry disagrees with role",
            "STOICHIOMETRY",
        )
        _need(
            reaction["flux"] == (alpha if production else decay),
            p + "/flux",
            "flux differs from exact M0 template",
            "TEMPLATE",
        )
    rhs = {"op": "subtract", "left": alpha, "right": decay}
    _need(
        model["equations"][0]["rhs"] == rhs,
        "/model/equations/0/rhs",
        "RHS differs from exact M0 template",
        "TEMPLATE",
    )


def _provenance(raw: object) -> dict[str, Any]:
    p = _object(
        raw,
        (),
        "/provenance",
        (
            "design_digest",
            "experiment_digest",
            "compiler",
            "symbol_map",
            "display_labels",
        ),
    )
    for key in ("design_digest", "experiment_digest"):
        if key in p:
            _text(p[key], "/provenance/" + key)
            _need(
                _DIGEST.fullmatch(p[key]) is not None,
                "/provenance/" + key,
                "expected SHA-256 digest syntax",
            )
    if "compiler" in p:
        compiler = _object(p["compiler"], ("name", "version"), "/provenance/compiler")
        for key in compiler:
            _text(compiler[key], "/provenance/compiler/" + key)
    if "symbol_map" in p:
        _need(
            "design_digest" in p,
            "/provenance",
            "symbol map requires its qualifying Design digest",
        )
        mapping = _object(
            p["symbol_map"], ("states", "parameters"), "/provenance/symbol_map"
        )
        for i, entry in enumerate(
            _array(mapping["states"], "/provenance/symbol_map/states", 1)
        ):
            path = f"/provenance/symbol_map/states/{i}"
            item = _object(
                entry,
                (
                    "fir_state_id",
                    "bioir_species_id",
                    "bioir_port_id",
                    "bioir_compartment_id",
                ),
                path,
            )
            _text(item["fir_state_id"], path + "/fir_state_id", ("x",))
            for name in ("bioir_species_id", "bioir_port_id", "bioir_compartment_id"):
                _id(item[name], path + "/" + name)
        entries = _array(mapping["parameters"], "/provenance/symbol_map/parameters", 2)
        for i, entry in enumerate(entries):
            path = f"/provenance/symbol_map/parameters/{i}"
            item = _object(
                entry,
                (
                    "fir_parameter_id",
                    "bioir_parameter_id",
                    "bioir_function_id",
                    "bioir_function_kind",
                ),
                path,
            )
            _text(
                item["fir_parameter_id"], path + "/fir_parameter_id", ("alpha", "beta")
            )
            for name in ("bioir_parameter_id", "bioir_function_id"):
                _id(item[name], path + "/" + name)
            _text(
                item["bioir_function_kind"],
                path + "/bioir_function_kind",
                ("constitutive_production", "first_order_decay"),
            )
        _need(
            {entry["fir_parameter_id"] for entry in entries} == {"alpha", "beta"},
            "/provenance/symbol_map/parameters",
            "map must cover alpha and beta exactly once",
        )
    if "display_labels" in p:
        labels = _object(
            p["display_labels"], (), "/provenance/display_labels", ("observables",)
        )
        if "observables" in labels:
            raw_labels = labels["observables"]
            _need(
                type(raw_labels) is dict,
                "/provenance/display_labels/observables",
                "expected a label object",
            )
            for key, value in raw_labels.items():
                path = pointer("/provenance/display_labels/observables", key)
                _id(key, path)
                _text(value, path)
    return p


def validate_model(data: object) -> dict[str, Any]:
    """Validate a complete standalone mathematical model without rewriting it."""
    model = _structure_model(data)
    _semantics(model)
    return model


def validate_envelope(data: object) -> dict[str, Any]:
    """Validate mathematics plus optional provenance shape, without source claims."""
    envelope = _object(data, ("model",), "", ("provenance",))
    model = _structure_model(envelope["model"])
    if "provenance" in envelope:
        _provenance(envelope["provenance"])
    _semantics(model)
    return envelope


def validate_sources(
    envelope: dict[str, Any], design: DesignDocument, experiment: ExperimentDocument
) -> None:
    """Check all producer obligations against exact verified local source documents."""
    validate_envelope(envelope)
    _need(
        type(design) is DesignDocument and type(experiment) is ExperimentDocument,
        "/provenance",
        "expected verified BioIR source documents",
    )
    _need(
        "provenance" in envelope,
        "/provenance",
        "compiler output requires provenance",
        "SOURCE_REQUIRED",
    )
    p = envelope["provenance"]
    for name in ("design_digest", "experiment_digest", "symbol_map"):
        _need(
            name in p,
            "/provenance/" + name,
            "compiler source field is required",
            "SOURCE_REQUIRED",
        )
    _need(
        experiment.content.design == design.reference,
        "/provenance/design_digest",
        "Experiment references a different Design",
        "SOURCE_DIGEST",
    )
    for name, source_document in (
        ("design_digest", design),
        ("experiment_digest", experiment),
    ):
        _need(
            p[name] == source_document.digest,
            "/provenance/" + name,
            "source digest mismatch",
            "SOURCE_DIGEST",
        )
    model = envelope["model"]
    mapping = p["symbol_map"]
    state = mapping["states"][0]
    species = {item.id: item for item in design.content.species}
    path = "/provenance/symbol_map/states/0"
    _need(
        state["bioir_species_id"] in species,
        path + "/bioir_species_id",
        "unknown source species",
        "REFERENCE",
    )
    source_species = species[state["bioir_species_id"]]
    _need(
        state["bioir_port_id"] in {port.id for port in source_species.ports},
        path + "/bioir_port_id",
        "unknown species-scoped port",
        "REFERENCE",
    )
    _need(
        state["bioir_compartment_id"] == source_species.compartment,
        path + "/bioir_compartment_id",
        "mapped compartment differs from species",
        "REFERENCE",
    )
    functions = {item.id: item for item in design.content.functions}
    parameters = {item.id: item for item in design.content.parameters}
    assignments = {
        item.parameter: item.quantity for item in experiment.content.parameters
    }
    fir_parameters = {
        item["id"]: (i, item) for i, item in enumerate(model["parameters"])
    }
    for i, entry in enumerate(mapping["parameters"]):
        path = f"/provenance/symbol_map/parameters/{i}"
        parameter_id = entry["bioir_parameter_id"]
        function_id = entry["bioir_function_id"]
        _need(
            parameter_id in parameters,
            path + "/bioir_parameter_id",
            "unknown source parameter",
            "REFERENCE",
        )
        _need(
            function_id in functions,
            path + "/bioir_function_id",
            "unknown source function",
            "REFERENCE",
        )
        fn = functions[function_id]
        kind = (
            "constitutive_production"
            if entry["fir_parameter_id"] == "alpha"
            else "first_order_decay"
        )
        _need(
            fn.kind == kind
            and fn.parameter == parameter_id
            and fn.target.species == source_species.id
            and fn.target.port == state["bioir_port_id"],
            path + "/bioir_function_id",
            "source function role/target/parameter mismatch",
            "SOURCE_ROLE",
        )
        _need(
            entry["bioir_function_kind"] == fn.kind,
            path + "/bioir_function_kind",
            "declared function kind differs from source",
            "SOURCE_ROLE",
        )
        index, target = fir_parameters[entry["fir_parameter_id"]]
        assignment = assignments[parameter_id]
        _need(
            target["unit"] == assignment.unit,
            f"/model/parameters/{index}/unit",
            "source assignment unit mismatch",
            "UNIT",
        )
        _need(
            target["value"] == assignment.value,
            f"/model/parameters/{index}/value",
            "source assignment value mismatch",
            "SOURCE_VALUE",
        )
    initial = next(
        item.quantity
        for item in experiment.content.initial_counts
        if item.species == source_species.id
    )
    _need(
        model["states"][0]["initial"] == initial.value,
        "/model/states/0/initial",
        "source initial count mismatch",
        "SOURCE_VALUE",
    )
    _need(
        model["states"][0]["unit"] == initial.unit,
        "/model/states/0/unit",
        "source initial unit mismatch",
        "UNIT",
    )
    source_observables = {item.id: item for item in experiment.content.observables}
    for i, item in enumerate(model["observables"]):
        path = f"/model/observables/{i}"
        _need(
            item["id"] in source_observables,
            path + "/id",
            "invented or renamed observable",
            "SOURCE_OBSERVABLE",
        )
        source = source_observables[item["id"]]
        _need(
            source.target.species == source_species.id
            and source.target.port == state["bioir_port_id"]
            and item["state"] == state["fir_state_id"],
            path + "/state",
            "source observable target mismatch",
            "SOURCE_OBSERVABLE",
        )
        _need(
            item["unit"] == model["states"][0]["unit"],
            path + "/unit",
            "source observable unit mismatch",
            "UNIT",
        )
    _need(
        {item["id"] for item in model["observables"]} == set(source_observables),
        "/model/observables",
        "source observables are not exhaustive",
        "SOURCE_OBSERVABLE",
    )
    validate_labels(envelope)


def validate_labels(envelope: dict[str, Any]) -> None:
    """Validate presentation references without treating them as model identity."""
    labels = (
        envelope.get("provenance", {}).get("display_labels", {}).get("observables", {})
    )
    ids = {item["id"] for item in envelope["model"]["observables"]}
    for key in labels:
        _need(
            key in ids,
            pointer("/provenance/display_labels/observables", key),
            "unknown observable label reference",
            "REFERENCE",
        )
