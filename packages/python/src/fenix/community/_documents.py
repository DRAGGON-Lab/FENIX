"""Immutable P08 sources, finite source-linked FIR compilation and identity."""

from __future__ import annotations

import copy
import hashlib
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar, cast

import rfc8785

from ._wire import contract, decode, encode, equal, require, validate

STATES = ("env.signal", "receiver.reporter", "receiver.signal", "sender.signal")
OWNERS = ("env", "receiver", "receiver", "sender")
SCOPES = (
    "environment_total",
    "representative_cell",
    "representative_cell",
    "representative_cell",
)


def digest(data: Any) -> str:
    return hashlib.sha256(rfc8785.dumps(data)).hexdigest()


T = TypeVar("T", bound="Blob")


@dataclass(frozen=True, slots=True, init=False)
class Blob:
    _text: str
    _policy: ClassVar[str] = "source"

    def __init__(self) -> None:
        raise TypeError("use a validating factory")

    @classmethod
    def _store(cls: type[T], data: Any, *, raw: str | bytes | None = None) -> T:
        obj = object.__new__(cls)
        text = (
            encode(data)
            if raw is None
            else raw.decode("utf-8")
            if type(raw) is bytes
            else raw
        )
        object.__setattr__(obj, "_text", text)
        return obj

    def to_dict(self) -> dict[str, Any]:
        return cast(dict[str, Any], decode(self._text, self._policy))

    def to_json(self) -> str:
        return self._text

    def to_bytes(self) -> bytes:
        return self._text.encode("utf-8")


@dataclass(frozen=True, slots=True, init=False)
class Source(Blob):
    @property
    def digest(self) -> str:
        return cast(str, self.to_dict()["digest"])

    @property
    def reference(self) -> dict[str, Any]:
        data = self.to_dict()
        c = data["content"]
        return dict(id=c["id"], revision=int(c["revision"]), digest=data["digest"])


def unique(items: list[dict[str, Any]], field: str, path: str) -> None:
    values = [item[field] for item in items]
    require(len(values) == len(set(values)), "DUPLICATE_ID", path)


def bindings(content: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    owners = content["owners"]
    unique(owners, "id", "/content/owners")
    unique(owners, "role", "/content/owners")
    require(
        {owner["role"] for owner in owners} == {"sender", "receiver", "env"},
        "ROLE_COVERAGE",
        "/content/owners",
    )
    addresses, owner_map, species_map = {}, {}, {}
    for i, owner in enumerate(owners):
        role = owner["role"]
        owner_map[role] = owner["id"]
        path = f"/content/owners/{i}/species"
        species = owner["species"]
        unique(species, "id", path)
        unique(species, "role", path)
        require(
            {s["role"] for s in species}
            == ({"signal", "reporter"} if role == "receiver" else {"signal"}),
            "ROLE_COVERAGE",
            path,
        )
        for j, species_entry in enumerate(species):
            species_map[role + "." + species_entry["role"]] = species_entry["id"]
            ports = species_entry["ports"]
            port_path = path + f"/{j}/ports"
            unique(ports, "id", port_path)
            expected = (
                {"sensor_in"}
                if species_entry["role"] == "reporter"
                else {"transport_in", "transport_out"}
            )
            if role == "env":
                expected.add("density_out")
            require(
                len(ports) == len(expected) and {p["kind"] for p in ports} == expected,
                "PORT_KINDS",
                port_path,
            )
            for port in ports:
                addresses[(owner["id"], species_entry["id"], port["id"])] = (
                    role,
                    species_entry["role"],
                    port["kind"],
                )
    edges = []
    for i, edge in enumerate(content["connections"]):
        resolved = []
        for side in ("source", "target"):
            endpoint = edge[side]
            key = tuple(endpoint[name] for name in ("owner", "species", "port"))
            require(key in addresses, "ENDPOINT", f"/content/connections/{i}/{side}")
            resolved.append(addresses[key])
        edges.append(tuple(resolved))
    expected_edges = {
        ((strain, "signal", "transport_out"), ("env", "signal", "transport_in"))
        for strain in ("sender", "receiver")
    }
    expected_edges.update(
        {
            (("env", "signal", "transport_out"), (strain, "signal", "transport_in"))
            for strain in ("sender", "receiver")
        }
    )
    expected_edges.add(
        (("env", "signal", "density_out"), ("receiver", "reporter", "sensor_in"))
    )
    require(
        len(edges) == 5 and set(edges) == expected_edges,
        "BINDINGS",
        "/content/connections",
    )
    return owner_map, species_map


def source(raw: str | bytes, kind: str, expected_digest: str | None) -> dict[str, Any]:
    value = decode(raw)
    validate("bioir", value)
    require(value["content"]["kind"] == kind, "SOURCE_KIND", "/content/kind")
    require(digest(value["content"]) == value["digest"], "SOURCE_DIGEST", "/digest")
    if expected_digest is not None:
        require(value["digest"] == expected_digest, "SOURCE_DIGEST", "/digest")
    return cast(dict[str, Any], value)


def predecessor(current: Blob, previous: Blob | None) -> None:
    if previous is None:
        return
    a, b = current.to_dict()["content"], previous.to_dict()["content"]
    require(
        type(current) is type(previous) and a["id"] == b["id"],
        "REVISION",
        "/content/id",
    )
    require(
        digest(a) == digest(b) or a["revision"] > b["revision"],
        "REVISION",
        "/content/revision",
    )


def envelope(content: dict[str, Any]) -> str:
    clean = decode(encode(content))
    return encode({"content": clean, "digest": digest(clean)})


@dataclass(frozen=True, slots=True, init=False)
class Design(Source):
    @classmethod
    def from_json(
        cls,
        raw: str | bytes,
        *,
        expected_digest: str | None = None,
        previous: Design | None = None,
    ) -> Design:
        data = source(raw, "Design", expected_digest)
        bindings(data["content"])
        obj = cls._store(data, raw=raw)
        predecessor(obj, previous)
        return obj

    @classmethod
    def from_content(cls, content: dict[str, Any]) -> Design:
        return cls.from_json(envelope(content))

    def replace_content(self, content: dict[str, Any]) -> Design:
        result = Design.from_content(content)
        predecessor(result, self)
        return result


@dataclass(frozen=True, slots=True, init=False)
class Experiment(Source):
    _design: Design

    @property
    def design(self) -> Design:
        return self._design

    @classmethod
    def from_json(
        cls,
        raw: str | bytes,
        *,
        design: Design,
        expected_digest: str | None = None,
        previous: Experiment | None = None,
    ) -> Experiment:
        if type(design) is not Design:
            raise TypeError("design must be a verified community Design")
        data = source(raw, "Experiment", expected_digest)
        require(
            equal(data["content"]["design"], design.reference),
            "DESIGN_LINK",
            "/content/design",
        )
        unique(data["content"]["observables"], "id", "/content/observables")
        obj = cls._store(data, raw=raw)
        object.__setattr__(obj, "_design", design)
        predecessor(obj, previous)
        return obj

    @classmethod
    def from_content(cls, content: dict[str, Any], *, design: Design) -> Experiment:
        return cls.from_json(envelope(content), design=design)

    def replace_content(
        self, content: dict[str, Any], *, design: Design | None = None
    ) -> Experiment:
        result = Experiment.from_content(
            content, design=self.design if design is None else design
        )
        predecessor(result, self)
        return result


@dataclass(frozen=True, slots=True, init=False)
class FIR(Blob):
    _policy: ClassVar[str] = "fir"
    _experiment: Experiment

    @classmethod
    def from_json(cls, raw: str | bytes, *, experiment: Experiment) -> FIR:
        if type(experiment) is not Experiment:
            raise TypeError("experiment must be a verified community Experiment")
        data = decode(raw, "fir")
        validate("fir", data)
        model, provenance = data["model"], data["provenance"]
        e, d = experiment.to_dict()["content"], experiment.design.to_dict()["content"]
        for key in ("parameters", "populations", "initial_counts"):
            require(equal(model[key], e[key]), "SOURCE_CORRESPONDENCE", "/model/" + key)
        for key, field in (
            ("reactions", "id"),
            ("equations", "state"),
            ("observables", "id"),
        ):
            unique(model[key], field, "/model/" + key)
        require(
            equal(
                sorted(model["observables"], key=lambda v: v["id"]),
                sorted(e["observables"], key=lambda v: v["id"]),
            ),
            "SOURCE_CORRESPONDENCE",
            "/model/observables",
        )
        require(
            equal(model["volumes"], {o["role"]: o["volume"] for o in d["owners"]}),
            "SOURCE_CORRESPONDENCE",
            "/model/volumes",
        )
        for kind, value in (("design", experiment.design), ("experiment", experiment)):
            require(
                provenance[kind + "_digest"] == value.digest,
                "SOURCE_CORRESPONDENCE",
                "/provenance/" + kind + "_digest",
            )
        for key, role_map in zip(("owners", "species"), bindings(d), strict=True):
            require(
                equal(provenance[key], role_map),
                "SOURCE_CORRESPONDENCE",
                "/provenance/" + key,
            )
        obj = cls._store(data, raw=raw)
        object.__setattr__(obj, "_experiment", experiment)
        return obj

    def normalized_model(self) -> dict[str, Any]:
        model = cast(dict[str, Any], self.to_dict()["model"])
        for key, field in (
            ("reactions", "id"),
            ("equations", "state"),
            ("observables", "id"),
        ):
            model[key].sort(key=lambda item: item[field].encode("utf-16-be"))
        return model

    def model_bytes(self) -> bytes:
        return rfc8785.dumps(self.normalized_model())

    def identity_bytes(self) -> bytes:
        return rfc8785.dumps(
            dict(
                domain="fenix.fir",
                canonicalization_version="0.2.0",
                model=self.normalized_model(),
            )
        )

    @property
    def digest(self) -> str:
        return hashlib.sha256(self.identity_bytes()).hexdigest()


def compile_experiment(experiment: Experiment) -> FIR:
    if type(experiment) is not Experiment:
        raise TypeError("experiment must be a verified community Experiment")
    e, d = experiment.to_dict()["content"], experiment.design.to_dict()["content"]
    shape = contract("fir")["properties"]["model"]["properties"]
    model = {
        key: copy.deepcopy(shape[key]["const"])
        for key in ("schema_version", "template", "time_unit", "capabilities")
    }
    for key in ("parameters", "populations", "initial_counts", "observables"):
        model[key] = e[key]
    model["volumes"] = {owner["role"]: owner["volume"] for owner in d["owners"]}
    # The exact finite equation/reaction templates are normative schema data,
    # never a fixture or another language's compiler output.
    for key in ("reactions", "equations"):
        model[key] = copy.deepcopy(shape[key]["items"]["enum"])
    owners, species = bindings(d)
    provenance = dict(
        design_digest=experiment.design.digest,
        experiment_digest=experiment.digest,
        owners=owners,
        species=species,
    )
    return FIR.from_json(
        encode(dict(model=model, provenance=provenance)), experiment=experiment
    )
