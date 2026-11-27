"""PROPOSED P08 executable review validator; independent of native FENIX.

This finite review tool is not a package API, authenticated loader or scientific
approval. Expectations live in literal catalogs, not output from this validator.
"""

import copy
import hashlib
import json
import math
import struct
from datetime import datetime
from decimal import Decimal
from itertools import pairwise
from pathlib import Path

import rfc8785
from jsonschema import Draft7Validator

HERE = Path(__file__).resolve().parent
SAFE = 9007199254740991
STATE_IDS = ("env.signal", "receiver.reporter", "receiver.signal", "sender.signal")
OWNERS = ("env", "receiver", "receiver", "sender")
SCOPES = (
    "environment_total",
    "representative_cell",
    "representative_cell",
    "representative_cell",
)


class Rejection(ValueError):
    def __init__(self, category, path):
        super().__init__(f"{category} at {path}")
        self.category, self.path = category, path


class IntegerToken(int):
    """Keep integer lexical type and the sign of integer-form zero amounts."""

    def __new__(cls, token):
        instance = super().__new__(cls, Decimal(token))
        instance.token = str(token)
        return instance

    def __float__(self):
        return float(self.token)

    def __reduce__(self):
        return IntegerToken, (self.token,)


def require(condition, category, path):
    if not condition:
        raise Rejection(category, path)


def pointer(parts):
    return "".join("/" + str(p).replace("~", "~0").replace("/", "~1") for p in parts)


def decode(raw, policy="source"):
    """P01/P03 numbers for scientific inputs; P07 exact integers for transport."""

    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "DUPLICATE_KEY", "")
            result[key] = value
        return result

    def real(token):
        value = float(token)
        require(math.isfinite(value), "NUMBER_RANGE", "")
        require(value != 0 or Decimal(token) == 0, "NUMBER_UNDERFLOW", "")
        return value

    def integer(token):
        if policy == "source":
            require(len(token.lstrip("-")) <= 16, "SOURCE_INTEGER", "")
            value = int(token)
            require(abs(value) <= SAFE, "SOURCE_INTEGER", "")
        elif policy == "fir":
            return real(token)
        return IntegerToken(token)

    def constant(_):
        raise Rejection("NUMBER_RANGE", "")

    try:
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", errors="strict")
        value = json.loads(
            raw,
            object_pairs_hook=pairs,
            parse_int=integer,
            parse_float=real,
            parse_constant=constant,
        )
    except (UnicodeError, json.JSONDecodeError) as error:
        raise Rejection("JSON", "") from error

    def unicode(item):
        if isinstance(item, str):
            try:
                item.encode("utf-8")
            except UnicodeError as error:
                raise Rejection("UNICODE", "") from error
        elif isinstance(item, dict):
            for key, child in item.items():
                unicode(key)
                unicode(child)
        elif isinstance(item, list):
            for child in item:
                unicode(child)

    unicode(value)
    return value


def schema(name, value):
    document = json.loads((HERE / name).read_bytes())
    Draft7Validator.check_schema(document)
    errors = list(Draft7Validator(document).iter_errors(value))
    if errors:
        # Structural witnesses declare this stage, not a global precedence
        # among simultaneous defects or oneOf alternatives.
        raise Rejection("SCHEMA", pointer(errors[0].absolute_path))


def digest(value):
    return hashlib.sha256(rfc8785.dumps(value)).hexdigest()


def document(value):
    schema("bioir-m1.schema.json", value)
    require(digest(value["content"]) == value["digest"], "SOURCE_DIGEST", "/digest")
    return value["content"]


def unique(items, key, path):
    values = [item[key] for item in items]
    require(len(values) == len(set(values)), "DUPLICATE_ID", path)


def design_bindings(design):
    owners = design["owners"]
    unique(owners, "id", "/content/owners")
    unique(owners, "role", "/content/owners")
    require(
        {o["role"] for o in owners} == {"sender", "receiver", "env"},
        "ROLE_COVERAGE",
        "/content/owners",
    )
    ports, source_owners, source_species = {}, {}, {}
    for index, owner in enumerate(owners):
        path = f"/content/owners/{index}/species"
        role = owner["role"]
        source_owners[role] = owner["id"]
        unique(owner["species"], "id", path)
        unique(owner["species"], "role", path)
        require(
            {s["role"] for s in owner["species"]}
            == ({"signal", "reporter"} if role == "receiver" else {"signal"}),
            "ROLE_COVERAGE",
            path,
        )
        for j, species in enumerate(owner["species"]):
            spath = path + f"/{j}/ports"
            source_species[role + "." + species["role"]] = species["id"]
            unique(species["ports"], "id", spath)
            kinds = [p["kind"] for p in species["ports"]]
            expected = (
                {"sensor_in"}
                if species["role"] == "reporter"
                else {"transport_out", "transport_in"}
            )
            if role == "env":
                expected.add("density_out")
            require(
                len(kinds) == len(expected) and set(kinds) == expected,
                "PORT_KINDS",
                spath,
            )
            for port in species["ports"]:
                ports[(owner["id"], species["id"], port["id"])] = (
                    role,
                    species["role"],
                    port["kind"],
                )
    required = {
        ((a, "signal", "transport_out"), (b, "signal", "transport_in"))
        for strain in ("sender", "receiver")
        for a, b in ((strain, "env"), ("env", strain))
    }
    required.add(
        (("env", "signal", "density_out"), ("receiver", "reporter", "sensor_in"))
    )
    edges = []
    for index, edge in enumerate(design["connections"]):
        endpoints = []
        for side in ("source", "target"):
            address = edge[side]
            key = tuple(address[field] for field in ("owner", "species", "port"))
            require(key in ports, "ENDPOINT", f"/content/connections/{index}/{side}")
            endpoints.append(ports[key])
        edges.append(tuple(endpoints))
    require(
        len(edges) == 5 and set(edges) == required, "BINDINGS", "/content/connections"
    )
    return source_owners, source_species


def source_pair(design, experiment):
    d, e = document(design), document(experiment)
    require(
        d["kind"] == "Design" and e["kind"] == "Experiment",
        "SOURCE_KIND",
        "/content/kind",
    )
    maps = design_bindings(d)
    require(
        e["design"]
        == {"id": d["id"], "revision": d["revision"], "digest": design["digest"]},
        "DESIGN_LINK",
        "/content/design",
    )
    unique(e["observables"], "id", "/content/observables")
    return maps


def normalize(model):
    """M1-only collection rules. AST operands and all other arrays retain order."""
    result = copy.deepcopy(model)
    for key, field in (
        ("reactions", "id"),
        ("equations", "state"),
        ("observables", "id"),
    ):
        unique(result[key], field, "/model/" + key)
        result[key].sort(key=lambda item: item[field].encode("utf-16-be"))
    return result


def identity(model):
    normalized = normalize(model)
    model_bytes = rfc8785.dumps(normalized)
    identity_bytes = rfc8785.dumps(
        {
            "domain": "fenix.fir",
            "canonicalization_version": "0.2.0",
            "model": normalized,
        }
    )
    return (
        normalized,
        model_bytes,
        identity_bytes,
        hashlib.sha256(identity_bytes).hexdigest(),
    )


def producer(design, experiment, fir):
    maps = source_pair(design, experiment)
    schema("fir-m1.schema.json", fir)
    d, e, model, provenance = (
        design["content"],
        experiment["content"],
        fir["model"],
        fir["provenance"],
    )
    for key in ("parameters", "populations", "initial_counts"):
        require(model[key] == e[key], "SOURCE_CORRESPONDENCE", "/model/" + key)
    require(
        sorted(model["observables"], key=lambda x: x["id"])
        == sorted(e["observables"], key=lambda x: x["id"]),
        "SOURCE_CORRESPONDENCE",
        "/model/observables",
    )
    volumes = {owner["role"]: owner["volume"] for owner in d["owners"]}
    require(model["volumes"] == volumes, "SOURCE_CORRESPONDENCE", "/model/volumes")
    for name, source in (("design", design), ("experiment", experiment)):
        require(
            provenance[name + "_digest"] == source["digest"],
            "SOURCE_CORRESPONDENCE",
            "/provenance/" + name + "_digest",
        )
    for key, expected in zip(("owners", "species"), maps, strict=True):
        require(
            provenance[key] == expected, "SOURCE_CORRESPONDENCE", "/provenance/" + key
        )
    return identity(model)


def same_float(left, right):
    return struct.pack(">d", float(left)) == struct.pack(">d", float(right))


def result_record(design, experiment, fir, result, manifest, raw_result):
    normalized, _, _, fir_digest = producer(design, experiment, fir)
    schema("ode-result-m1.schema.json", result)
    schema("run-manifest-m1.schema.json", manifest)
    integer_fields = [
        (manifest["execution"]["max_nfev"], "/execution/max_nfev"),
        (manifest["evaluations"]["nfev"], "/evaluations/nfev"),
    ]
    integer_fields.extend(
        (value, "/backend/evaluations/" + key)
        for key, value in manifest["backend"]["evaluations"].items()
    )
    if "maxiters" in manifest["backend"]["solver"]["options"]:
        integer_fields.append(
            (
                manifest["backend"]["solver"]["options"]["maxiters"],
                "/backend/solver/options/maxiters",
            )
        )
    for value, path in integer_fields:
        require(isinstance(value, int) and not isinstance(value, bool), "INTEGER_TOKEN", path)
    require(result["fir_digest"] == fir_digest, "FIR_LINK", "/fir_digest")
    require(manifest["fir"]["digest"] == fir_digest, "FIR_LINK", "/fir/digest")
    for kind, source in (("design", design), ("experiment", experiment)):
        expected = {
            key: source["content"][key] for key in ("schema_version", "id", "revision")
        }
        expected["digest"] = source["digest"]
        require(
            manifest["sources"][kind] == expected, "SOURCE_LINK", "/sources/" + kind
        )
    require(
        manifest["output"]["sha256"] == hashlib.sha256(raw_result).hexdigest(),
        "RESULT_CHECKSUM",
        "/output/sha256",
    )
    times = result["times"]
    require(all(b > a for a, b in pairwise(times)), "GRID", "/times")
    require(times == manifest["execution"]["time_grid"], "GRID", "/execution/time_grid")
    require(result["state_owners"] == list(OWNERS), "SCOPE_ALIGNMENT", "/state_owners")
    require(result["state_scopes"] == list(SCOPES), "SCOPE_ALIGNMENT", "/state_scopes")
    observations = normalized["observables"]
    for key, expected in (
        ("observable_ids", [o["id"] for o in observations]),
        ("observable_state_ids", [o["state"] for o in observations]),
        ("observable_units", ["molecule"] * len(observations)),
        (
            "observable_owners",
            [OWNERS[STATE_IDS.index(o["state"])] for o in observations],
        ),
        (
            "observable_scopes",
            [SCOPES[STATE_IDS.index(o["state"])] for o in observations],
        ),
    ):
        require(result[key] == expected, "OBSERVABLE_ALIGNMENT", "/" + key)
    for key in ("state_values", "observable_values"):
        require(len(result[key]) == len(times), "DIMENSIONS", "/" + key)
    for i, (states, values) in enumerate(
        zip(result["state_values"], result["observable_values"], strict=True)
    ):
        require(
            len(values) == len(observations), "DIMENSIONS", f"/observable_values/{i}"
        )
        for j, observation in enumerate(observations):
            require(
                same_float(values[j], states[STATE_IDS.index(observation["state"])]),
                "OBSERVABLE_COPY",
                f"/observable_values/{i}/{j}",
            )
        if times[i] == 0:
            require(
                all(
                    value == normalized["initial_counts"][state]["value"]
                    for value, state in zip(states, STATE_IDS, strict=True)
                ),
                "INITIAL_SAMPLE",
                f"/state_values/{i}",
            )
    execution, backend = manifest["execution"], manifest["backend"]
    require(
        manifest["evaluations"]["nfev"] <= execution["max_nfev"],
        "WORK_COUNT",
        "/evaluations/nfev",
    )
    zero = times == [0]
    require(
        manifest["integration"] == ("skipped_zero_grid" if zero else "performed"),
        "INTEGRATION",
        "/integration",
    )
    if zero:
        require(
            manifest["evaluations"]["nfev"] == 0
            and all(v == 0 for v in backend["evaluations"].values()),
            "WORK_COUNT",
            "/evaluations",
        )
    else:
        require(manifest["evaluations"]["nfev"] > 0, "WORK_COUNT", "/evaluations/nfev")
    if backend["profile"].startswith("julia-"):
        require(
            backend["solver"]["options"]["save_start"] == (times[0] == 0),
            "BACKEND_OPTIONS",
            "/backend/solver/options/save_start",
        )
        require(
            backend["solver"]["options"]["maxiters"] == 9223372036854775807,
            "BACKEND_OPTIONS",
            "/backend/solver/options/maxiters",
        )
    for key in ("started_at_utc", "finished_at_utc"):
        try:
            datetime.strptime(manifest["timing"][key], "%Y-%m-%dT%H:%M:%S.%fZ")
        except ValueError as error:
            raise Rejection("TIMESTAMP", "/timing/" + key) from error
    return fir_digest
