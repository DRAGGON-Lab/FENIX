"""P01 M0 authoring values. No committed identity or raw-input parsing."""

from __future__ import annotations

import json
import math
import re
from dataclasses import InitVar, dataclass, fields
from typing import ClassVar

_MAX_INTEGER = 2**53 - 1
_ID = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}")
_DIGEST = re.compile(r"[0-9a-f]{64}")
_RATE_UNITS = ("molecule/s", "1/s")

type JSONValue = str | int | float | list[JSONValue] | dict[str, JSONValue]


class BioIRValidationError(ValueError):
    """One primary failure, with a constructor-relative JSON Pointer."""

    def __init__(self, category: str, path: str, message: str) -> None:
        self.category = category
        self.path = path
        super().__init__(f"{category} at {path or '/'}: {message}")


def _require(
    condition: bool, path: str, message: str, category: str = "SCHEMA"
) -> None:
    if not condition:
        raise BioIRValidationError(category, path, message)


def _id(value: str, path: str) -> None:
    _require(
        type(value) is str and _ID.fullmatch(value) is not None,
        path,
        "expected a case-sensitive ASCII identifier of 1–64 characters",
    )


def _revision(value: int) -> None:
    _require(
        type(value) is int and 1 <= value <= _MAX_INTEGER,
        "/revision",
        "expected a positive integer through 2^53-1",
    )


def _token(value: str, allowed: tuple[str, ...], path: str) -> None:
    _require(
        type(value) is str and value in allowed, path, f"expected one of {allowed}"
    )


def _typed(value: object, cls: type[_Value], path: str) -> None:
    # Exact native values keep mutable/unvalidated subclasses out of the graph.
    _require(type(value) is cls, path, f"expected a {cls.__name__} value")


def _collection(
    values: tuple[object, ...], cls: type[_Value], path: str, size: int | None = None
) -> None:
    _require(type(values) is tuple, path, "expected an immutable tuple")
    if size is not None:
        _require(len(values) == size, path, f"M0 requires exactly {size} entries")
    for i, value in enumerate(values):
        _typed(value, cls, f"{path}/{i}")


def _unique(values: tuple[_Value, ...], key: str, path: str) -> None:
    seen: set[str] = set()
    for i, value in enumerate(values):
        identifier = getattr(value, key)
        _require(
            identifier not in seen,
            f"{path}/{i}/{key}",
            f"duplicate {key}: {identifier}",
            "DUPLICATE_ID",
        )
        seen.add(identifier)


def _quantity(
    value: Quantity, units: tuple[str, ...], path: str, positive: bool = False
) -> None:
    _typed(value, Quantity, path)
    _token(value.unit, units, path + "/unit")
    if positive:
        _require(value.value > 0, path + "/value", "volume must be strictly positive")


@dataclass(frozen=True, slots=True, kw_only=True)
class _Value:
    def _dict(self) -> dict[str, JSONValue]:
        return {
            field.name: _encode(getattr(self, field.name)) for field in fields(self)
        }


def _encode(value: object) -> JSONValue:
    if isinstance(value, _Value):
        return value._dict()
    if type(value) is tuple:
        return [_encode(item) for item in value]
    if isinstance(value, (str, int, float)):
        return value
    raise TypeError("unexpected value in validated content")


@dataclass(frozen=True, slots=True, kw_only=True)
class Quantity(_Value):
    """Explicit nonnegative count, rate or volume; no conversion or normalization."""

    value: int | float
    unit: str

    def __post_init__(self) -> None:
        _require(
            type(self.value) in (int, float),
            "/value",
            "expected a built-in int or float",
        )
        if type(self.value) is int:
            _require(
                abs(self.value) <= _MAX_INTEGER,
                "/value",
                "integer serialization exceeds P01's safe integer-token range",
                "INTEGER_RANGE",
            )
        else:
            _require(
                math.isfinite(self.value),
                "/value",
                "expected a finite binary64 value",
                "NUMBER_RANGE",
            )
        _require(self.value >= 0, "/value", "expected a nonnegative quantity")
        _token(self.unit, ("L", "molecule", *_RATE_UNITS), "/unit")


@dataclass(frozen=True, slots=True, kw_only=True)
class Port(_Value):
    id: str
    kind: str = "molecular_count"

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _token(self.kind, ("molecular_count",), "/kind")


@dataclass(frozen=True, slots=True, kw_only=True)
class Compartment(_Value):
    id: str
    volume: Quantity
    kind: str = "representative_cell"

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _token(self.kind, ("representative_cell",), "/kind")
        _quantity(self.volume, ("L",), "/volume", positive=True)


@dataclass(frozen=True, slots=True, kw_only=True)
class Species(_Value):
    id: str
    compartment: str
    ports: tuple[Port, ...]

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _id(self.compartment, "/compartment")
        _collection(self.ports, Port, "/ports", 1)
        _unique(self.ports, "id", "/ports")


@dataclass(frozen=True, slots=True, kw_only=True)
class Parameter(_Value):
    id: str
    unit: str

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _token(self.unit, _RATE_UNITS, "/unit")


@dataclass(frozen=True, slots=True, kw_only=True)
class PortReference(_Value):
    species: str
    port: str

    def __post_init__(self) -> None:
        _id(self.species, "/species")
        _id(self.port, "/port")


@dataclass(frozen=True, slots=True, kw_only=True)
class Function(_Value):
    id: str
    kind: str
    target: PortReference
    parameter: str

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _token(self.kind, ("constitutive_production", "first_order_decay"), "/kind")
        _typed(self.target, PortReference, "/target")
        _id(self.parameter, "/parameter")


@dataclass(frozen=True, slots=True, kw_only=True)
class ParameterAssignment(_Value):
    parameter: str
    quantity: Quantity

    def __post_init__(self) -> None:
        _id(self.parameter, "/parameter")
        _quantity(self.quantity, _RATE_UNITS, "/quantity")


@dataclass(frozen=True, slots=True, kw_only=True)
class InitialCount(_Value):
    species: str
    quantity: Quantity

    def __post_init__(self) -> None:
        _id(self.species, "/species")
        _quantity(self.quantity, ("molecule",), "/quantity")


@dataclass(frozen=True, slots=True, kw_only=True)
class Observable(_Value):
    id: str
    target: PortReference

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _typed(self.target, PortReference, "/target")


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignReference(_Value):
    """Claimed identity. Digest correspondence is unverified by this content API."""

    id: str
    revision: int
    digest: str

    def __post_init__(self) -> None:
        _id(self.id, "/id")
        _revision(self.revision)
        _require(
            type(self.digest) is str and _DIGEST.fullmatch(self.digest) is not None,
            "/digest",
            "expected 64 lowercase hexadecimal SHA-256 characters",
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class _Content(_Value):
    kind: str
    schema_version: str
    id: str
    revision: int
    _kind: ClassVar[str]

    def _header(self) -> None:
        _token(self.kind, (self._kind,), "/kind")
        _token(self.schema_version, ("0.1.0",), "/schema_version")
        _id(self.id, "/id")
        _revision(self.revision)

    def to_dict(self) -> dict[str, JSONValue]:
        """Fresh JSON-compatible content; declaration order remains significant."""
        return self._dict()

    def to_json(self) -> str:
        """Ordinary JSON, without canonicalization, envelopes or digests."""
        return json.dumps(self.to_dict(), allow_nan=False)


def _target(target: PortReference, species: tuple[Species, ...], path: str) -> None:
    lookup = {item.id: item for item in species}
    _require(
        target.species in lookup, path + "/species", "unknown species", "REFERENCE"
    )
    _require(
        target.port in {port.id for port in lookup[target.species].ports},
        path + "/port",
        "unknown port in referenced species",
        "REFERENCE",
    )


@dataclass(frozen=True, slots=True, kw_only=True)
class DesignContent(_Content):
    """Uncommitted M0 Design, validated without assigning a scientific digest."""

    kind: str = "Design"
    schema_version: str = "0.1.0"
    compartments: tuple[Compartment, ...]
    species: tuple[Species, ...]
    parameters: tuple[Parameter, ...]
    functions: tuple[Function, ...]
    _kind: ClassVar[str] = "Design"

    def __post_init__(self) -> None:
        self._header()
        _collection(self.compartments, Compartment, "/compartments", 1)
        _collection(self.species, Species, "/species", 1)
        _collection(self.parameters, Parameter, "/parameters", 2)
        _collection(self.functions, Function, "/functions", 2)
        _unique(self.compartments, "id", "/compartments")
        _unique(self.species, "id", "/species")
        _unique(self.parameters, "id", "/parameters")
        _unique(self.functions, "id", "/functions")
        compartments = {item.id for item in self.compartments}
        for i, item in enumerate(self.species):
            _require(
                item.compartment in compartments,
                f"/species/{i}/compartment",
                "unknown compartment",
                "REFERENCE",
            )
        parameters = {item.id: item for item in self.parameters}
        kinds: set[str] = set()
        used: set[str] = set()
        for i, fn in enumerate(self.functions):
            path = f"/functions/{i}"
            _target(fn.target, self.species, path + "/target")
            _require(
                fn.parameter in parameters,
                path + "/parameter",
                "unknown parameter",
                "REFERENCE",
            )
            unit = "molecule/s" if fn.kind == "constitutive_production" else "1/s"
            _require(
                parameters[fn.parameter].unit == unit,
                path + "/parameter",
                f"{fn.kind} requires {unit}",
                "UNIT",
            )
            _require(
                fn.kind not in kinds and fn.parameter not in used,
                path,
                "M0 requires distinct production and decay roles and parameters",
                "FUNCTION_ROLE",
            )
            kinds.add(fn.kind)
            used.add(fn.parameter)
        _require(
            used == set(parameters), "/parameters", "unused parameters", "REFERENCE"
        )


@dataclass(frozen=True, slots=True, kw_only=True)
class ExperimentContent(_Content):
    """Uncommitted Experiment checked against a local, unverified Design context.

    ``source_design`` is required for validation and is neither stored nor serialized.
    ID/revision equality does not establish digest correspondence or trusted identity.
    """

    kind: str = "Experiment"
    schema_version: str = "0.1.0"
    design: DesignReference
    parameters: tuple[ParameterAssignment, ...]
    initial_counts: tuple[InitialCount, ...]
    observables: tuple[Observable, ...]
    interventions: tuple[()]
    source_design: InitVar[DesignContent]
    _kind: ClassVar[str] = "Experiment"

    def __post_init__(self, source_design: DesignContent) -> None:
        self._header()
        _typed(self.design, DesignReference, "/design")
        _typed(source_design, DesignContent, "/source_design")
        _collection(self.parameters, ParameterAssignment, "/parameters", 2)
        _collection(self.initial_counts, InitialCount, "/initial_counts", 1)
        _collection(self.observables, Observable, "/observables")
        _require(
            type(self.interventions) is tuple and len(self.interventions) == 0,
            "/interventions",
            "M0 requires an explicit empty tuple",
        )
        for name in ("id", "revision"):
            _require(
                getattr(self.design, name) == getattr(source_design, name),
                "/design/" + name,
                "reference differs from supplied Design context",
                "DESIGN_REFERENCE",
            )
        _unique(self.parameters, "parameter", "/parameters")
        _unique(self.initial_counts, "species", "/initial_counts")
        _unique(self.observables, "id", "/observables")
        parameters = {item.id: item for item in source_design.parameters}
        for i, item in enumerate(self.parameters):
            path = f"/parameters/{i}"
            _require(
                item.parameter in parameters,
                path + "/parameter",
                "unknown parameter",
                "REFERENCE",
            )
            _require(
                item.quantity.unit == parameters[item.parameter].unit,
                path + "/quantity/unit",
                "assignment unit differs from Design declaration",
                "UNIT",
            )
        _require(
            {item.parameter for item in self.parameters} == set(parameters),
            "/parameters",
            "assignments must be exhaustive",
            "REFERENCE",
        )
        _require(
            {item.species for item in self.initial_counts}
            == {item.id for item in source_design.species},
            "/initial_counts",
            "initial counts must cover the Design species",
            "REFERENCE",
        )
        for i, observable in enumerate(self.observables):
            _target(
                observable.target, source_design.species, f"/observables/{i}/target"
            )
