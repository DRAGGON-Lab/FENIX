"""P01 wire structure and explicit conversion into native content values.

No schemas, fixtures or reference evaluators are loaded at runtime. Structural
checks precede scientific reference checks so envelopes can be verified first.
"""

from __future__ import annotations

import math
from dataclasses import fields
from typing import Any

from ._content import (
    _DIGEST,
    BioIRValidationError,
    Compartment,
    DesignContent,
    DesignReference,
    ExperimentContent,
    Function,
    InitialCount,
    Observable,
    Parameter,
    ParameterAssignment,
    Port,
    PortReference,
    Quantity,
    Species,
    _id,
    _require,
    _revision,
    _token,
    _Value,
)
from ._json import pointer

_CHILDREN: dict[type[_Value], dict[str, tuple[type[_Value], int | None, bool]]] = {
    Compartment: {"volume": (Quantity, None, False)},
    Species: {"ports": (Port, 1, True)},
    Function: {"target": (PortReference, None, False)},
    ParameterAssignment: {"quantity": (Quantity, None, False)},
    InitialCount: {"quantity": (Quantity, None, False)},
    Observable: {"target": (PortReference, None, False)},
    DesignContent: {
        "compartments": (Compartment, 1, True),
        "species": (Species, 1, True),
        "parameters": (Parameter, 2, True),
        "functions": (Function, 2, True),
    },
    ExperimentContent: {
        "design": (DesignReference, None, False),
        "parameters": (ParameterAssignment, 2, True),
        "initial_counts": (InitialCount, 1, True),
        "observables": (Observable, None, True),
    },
}


def _members(
    raw: object, required: set[str], allowed: set[str], path: str
) -> dict[str, Any]:
    _require(type(raw) is dict, path, "expected an object")
    assert isinstance(raw, dict)
    for name in sorted(required):
        _require(name in raw, pointer(path, name), "required member is missing")
    for name in raw:
        _require(type(name) is str, path, "object member names must be strings")
        _require(name in allowed, pointer(path, name), "unknown member")
    return raw


def _native_revision(value: Any) -> Any:
    # JSON Schema integer semantics permit 1.0/1e0. Only revision fields use
    # this lossless mapping; integral quantity floats must remain floats.
    if type(value) is float and math.isfinite(value) and value.is_integer():
        return int(value)
    return value


def _arguments(cls: type[_Value], raw: object, path: str) -> dict[str, Any]:
    names = {field.name for field in fields(cls)}
    data = _members(raw, names, names, path)
    args = data.copy()
    for name, (child_cls, size, repeated) in _CHILDREN.get(cls, {}).items():
        child_path = pointer(path, name)
        value = data[name]
        if repeated:
            _require(type(value) is list, child_path, "expected an array")
            if size is not None:
                _require(
                    len(value) == size,
                    child_path,
                    f"M0 requires exactly {size} entries",
                )
            args[name] = tuple(
                _build(child_cls, item, pointer(child_path, i))
                for i, item in enumerate(value)
            )
        else:
            args[name] = _build(child_cls, value, child_path)
    if "revision" in args:
        args["revision"] = _native_revision(args["revision"])
    if cls is ExperimentContent:
        _require(
            type(data["interventions"]) is list and not data["interventions"],
            path + "/interventions",
            "M0 requires an empty interventions array",
        )
        args["interventions"] = ()
    return args


def _build[T: _Value](cls: type[T], raw: object, path: str) -> T:
    args = _arguments(cls, raw, path)
    try:
        return cls(**args)
    except BioIRValidationError as error:
        raise BioIRValidationError(
            error.category, path + error.path, str(error)
        ) from error


def validate_content_structure(content: object, kind: str) -> dict[str, Any]:
    """Check all wire structure and local quantities, without resolving references."""
    cls = DesignContent if kind == "Design" else ExperimentContent
    args = _arguments(cls, content, "/content")
    try:
        _token(args["kind"], (kind,), "/kind")
        _token(args["schema_version"], ("0.1.0",), "/schema_version")
        _id(args["id"], "/id")
        _revision(args["revision"])
    except BioIRValidationError as error:
        raise BioIRValidationError(
            error.category, "/content" + error.path, str(error)
        ) from error
    assert isinstance(content, dict)
    return content


def decode_envelope(value: object, kind: str) -> tuple[dict[str, Any], str, object]:
    data = _members(value, {"content", "digest"}, {"content", "digest", "metadata"}, "")
    digest = data["digest"]
    _require(
        type(digest) is str and _DIGEST.fullmatch(digest) is not None,
        "/digest",
        "expected a lowercase SHA-256 digest",
    )
    metadata: object = None
    if "metadata" in data:
        metadata = _members(
            data["metadata"], set(), {"name", "description"}, "/metadata"
        )
        assert isinstance(metadata, dict)
        for name, item in metadata.items():
            _require(type(item) is str, pointer("/metadata", name), "expected a string")
            try:
                item.encode("utf-8", errors="strict")
            except UnicodeEncodeError:
                raise BioIRValidationError(
                    "INVALID_UNICODE",
                    pointer("/metadata", name),
                    "unpaired Unicode surrogate",
                ) from None
    content = validate_content_structure(data["content"], kind)
    return content, digest, metadata


def decode_design(content: object) -> DesignContent:
    validate_content_structure(content, "Design")
    return _build(DesignContent, content, "/content")


def decode_experiment(
    content: object, source_design: DesignContent
) -> ExperimentContent:
    validate_content_structure(content, "Experiment")
    args = _arguments(ExperimentContent, content, "/content")
    try:
        return ExperimentContent(**args, source_design=source_design)
    except BioIRValidationError as error:
        raise BioIRValidationError(
            error.category, "/content" + error.path, str(error)
        ) from error
